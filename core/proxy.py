"""
Proxy Management Module

Handles loading, rotating, and health-checking of HTTP / SOCKS5 proxies
for the Instagram checker (or any other scraper).

Supported proxy formats in files / strings:
    host:port
    http://host:port
    socks5://host:port
    user:pass@host:port
    http://user:pass@host:port
    socks5://user:pass@[2001:db8::1]:1080   # IPv6 example
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, ParseResult

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


# --------------------------------------------------------------------------- #
# Proxy data class
# --------------------------------------------------------------------------- #
@dataclass
class Proxy:
    """Immutable proxy configuration."""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: str = "http"          # http or socks5

    def __str__(self) -> str:
        """String representation used by requests."""
        auth = f"{self.username}:{self.password}@" if self.username and self.password else ""
        return f"{self.proxy_type}://{auth}{self.host}:{self.port}"

    def to_dict(self) -> Dict[str, str]:
        """Requests-compatible proxy dict."""
        url = str(self)
        return {"http": url, "https": url}


# --------------------------------------------------------------------------- #
# Proxy manager
# --------------------------------------------------------------------------- #
class ProxyManager:
    """Load, test and rotate proxies."""

    def __init__(self) -> None:
        self.proxies: List[Proxy] = []
        self.healthy_proxies: List[Proxy] = []
        self.dead_proxies: Set[str] = set()          # "host:port" keys
        self._index: int = 0

    # ------------------------------------------------------------------- #
    # Loading
    # ------------------------------------------------------------------- #
    def load_from_file(self, file_path: str) -> int:
        """
        Load proxies from a text file (one per line).

        Returns:
            Number of successfully parsed proxies.
        """
        loaded = 0
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, raw in enumerate(f, 1):
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    proxy = self._parse_line(line)
                    if proxy:
                        self.proxies.append(proxy)
                        loaded += 1
                    else:
                        print(f"[WARN] line {line_num}: invalid format -> {line}")
        except FileNotFoundError:
            print(f"[ERROR] Proxy file not found: {file_path}")
        except Exception as exc:
            print(f"[ERROR] Loading proxies: {exc}")

        return loaded

    # ------------------------------------------------------------------- #
    # Parsing helpers
    # ------------------------------------------------------------------- #
    @staticmethod
    def _split_host_port(netloc: str) -> Tuple[str, int]:
        """
        Split netloc into (host, port). Handles IPv6 addresses in [].
        """
        if netloc.startswith("["):                     # IPv6
            host_end = netloc.rfind("]")
            host = netloc[1:host_end]
            port_part = netloc[host_end + 1:]
        else:
            if ":" not in netloc:
                raise ValueError("missing port")
            host, port_part = netloc.rsplit(":", 1)
        port = int(port_part.lstrip(":") or "0")
        if not (0 < port <= 65535):
            raise ValueError("invalid port")
        return host, port

    @classmethod
    def _parse_line(cls, line: str) -> Optional[Proxy]:
        """
        Parse a single proxy line into a Proxy object.
        Returns ``None`` on failure.
        """
        # 1. Remove surrounding whitespace
        line = line.strip()
        if not line:
            return None

        # 2. Detect scheme (http / socks5) – default http
        scheme = "http"
        if "://" in line:
            scheme, line = line.split("://", 1)
            scheme = scheme.lower()
            if scheme not in {"http", "https", "socks5", "socks5h"}:
                return None
            # normalize
            if scheme.startswith("socks5"):
                scheme = "socks5"

        # 3. Split auth (if any) and host:port
        username: Optional[str] = None
        password: Optional[str] = None
        netloc = line

        if "@" in line:
            auth, netloc = line.rsplit("@", 1)
            if ":" in auth:
                username, password = auth.split(":", 1)
            else:
                username = auth          # only user, no pass

        # 4. Split host:port (IPv6 aware)
        try:
            host, port = cls._split_host_port(netloc)
        except Exception:
            return None

        return Proxy(
            host=host,
            port=port,
            username=username or None,
            password=password or None,
            proxy_type=scheme,
        )

    # ------------------------------------------------------------------- #
    # Health checking
    # ------------------------------------------------------------------- #
    def check_proxy_health(
        self,
        proxy: Proxy,
        test_url: str = "https://httpbin.org/get",
        timeout: int = 15,
    ) -> bool:
        """
        Test a single proxy.

        NOTE: SOCKS5 proxies require ``PySocks`` (`pip install pysocks`).
        """
        try:
            resp = requests.get(
                test_url,
                proxies=proxy.to_dict(),
                timeout=timeout,
                headers={"User-Agent": "ProxyChecker/1.0"},
            )
            return resp.status_code == 200
        except Exception:
            return False

    def filter_healthy_proxies(
        self,
        test_url: str = "https://httpbin.org/get",
        timeout: int = 15,
        max_workers: int = 20,
    ) -> int:
        """
        Concurrently test all loaded proxies and keep only the healthy ones.

        Returns:
            Number of healthy proxies.
        """
        self.healthy_proxies.clear()
        healthy = 0

        def _test(p: Proxy) -> Tuple[Proxy, bool]:
            return p, self.check_proxy_health(p, test_url, timeout)

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_proxy = {pool.submit(_test, p): p for p in self.proxies}
            for future in as_completed(future_to_proxy):
                p, ok = future.result()
                key = f"{p.host}:{p.port}"
                if ok:
                    self.healthy_proxies.append(p)
                    healthy += 1
                    print(f"Healthy: {p.host}:{p.port}")
                else:
                    self.dead_proxies.add(key)
                    print(f"Dead: {p.host}:{p.port}")

        return healthy

    # ------------------------------------------------------------------- #
    # Rotation helpers
    # ------------------------------------------------------------------- #
    def get_next_proxy(self) -> Optional[Proxy]:
        """Round-robin rotation over healthy proxies."""
        if not self.healthy_proxies:
            return None
        proxy = self.healthy_proxies[self._index]
        self._index = (self._index + 1) % len(self.healthy_proxies)
        return proxy

    def get_random_proxy(self) -> Optional[Proxy]:
        """Random healthy proxy."""
        return random.choice(self.healthy_proxies) if self.healthy_proxies else None

    def get_all_healthy_proxies(self) -> List[Proxy]:
        """Copy of the current healthy list."""
        return self.healthy_proxies.copy()

    def remove_dead_proxy(self, proxy: Proxy) -> None:
        """Mark a proxy as dead and remove it from the healthy pool."""
        if proxy in self.healthy_proxies:
            self.healthy_proxies.remove(proxy)
        self.dead_proxies.add(f"{proxy.host}:{proxy.port}")

    # ------------------------------------------------------------------- #
    # Stats & utilities
    # ------------------------------------------------------------------- #
    def get_stats(self) -> Dict[str, int]:
        return {
            "total": len(self.proxies),
            "healthy": len(self.healthy_proxies),
            "dead": len(self.dead_proxies),
        }

    def clear_dead_proxies(self) -> None:
        self.dead_proxies.clear()


# --------------------------------------------------------------------------- #
# Helper functions (outside the class)
# --------------------------------------------------------------------------- #
def create_sample_proxies() -> List[Proxy]:
    """Return a few proxies for quick testing."""
    return [
        Proxy(host="1.2.3.4", port=8080),
        Proxy(host="5.6.7.8", port=3128, username="alice", password="secret"),
        Proxy(host="socks.example.com", port=1080, proxy_type="socks5"),
        Proxy(host="2001:db8::1", port=1080, proxy_type="socks5", username="bob", password="pass"),
    ]


def load_proxies_from_string(proxy_string: str) -> List[Proxy]:
    """
    Load proxies from a multi-line or comma-separated string.

    Example:
        "1.1.1.1:8080, user:pass@2.2.2.2:3128"
    """
    manager = ProxyManager()
    lines = re.split(r"[\n,]", proxy_string)
    proxies = []
    for raw in lines:
        p = manager._parse_line(raw.strip())
        if p:
            proxies.append(p)
    return proxies


# --------------------------------------------------------------------------- #
# Quick demo (uncomment to run)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # 1. Load from a file (create test_proxies.txt first)
    pm = ProxyManager()
    # pm.load_from_file("test_proxies.txt")

    # 2. Or use sample data
    pm.proxies = create_sample_proxies()

    print(f"Loaded {len(pm.proxies)} proxies")
    healthy = pm.filter_healthy_proxies(max_workers=10)
    print(f"Found {healthy} healthy proxies")
    print(pm.get_stats())

    # Rotate a few times
    for _ in range(5):
        print("Next proxy ->", pm.get_next_proxy())