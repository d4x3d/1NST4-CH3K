"""
Proxy Management Module

This module handles proxy loading, rotation, and health checking
for the Instagram checker.
"""

import random
import requests
from typing import List, Optional, Dict, Set, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class Proxy:
    """Proxy configuration data class."""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: str = "http"

    def __str__(self) -> str:
        """Return proxy URL string."""
        if self.username and self.password:
            return f"{self.proxy_type}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type}://{self.host}:{self.port}"

    def to_dict(self) -> Dict[str, str]:
        """Convert to requests proxy format."""
        proxy_url = str(self)
        return {
            "http": proxy_url,
            "https": proxy_url
        }


class ProxyManager:
    """Manages proxy loading, rotation, and health checking."""

    def __init__(self):
        """Initialize the proxy manager."""
        self.proxies: List[Proxy] = []
        self.healthy_proxies: List[Proxy] = []
        self.dead_proxies: Set[str] = set()
        self.current_index = 0

    def load_from_file(self, file_path: str) -> int:
        """
        Load proxies from a file.

        Args:
            file_path: Path to proxy file

        Returns:
            Number of proxies loaded

        Supported formats:
        - host:port
        - host:port:username:password
        - http://host:port
        - socks5://host:port
        """
        loaded_count = 0

        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    proxy = self._parse_proxy_line(line)
                    if proxy:
                        self.proxies.append(proxy)
                        loaded_count += 1
                    else:
                        print(f"Warning: Invalid proxy format on line {line_num}: {line}")

        except FileNotFoundError:
            print(f"Error: Proxy file not found: {file_path}")
        except Exception as e:
            print(f"Error loading proxies: {e}")

        return loaded_count

    def _parse_proxy_line(self, line: str) -> Optional[Proxy]:
        """
        Parse a single proxy line.

        Args:
            line: Proxy line to parse

        Returns:
            Proxy object or None if invalid
        """
        # Remove protocol if present
        if '://' in line:
            protocol, rest = line.split('://', 1)
            proxy_type = protocol
            line = rest
        else:
            proxy_type = "http"

        # Handle authentication
        username = None
        password = None

        if '@' in line:
            auth, host_port = line.rsplit('@', 1)
            if ':' in auth:
                username, password = auth.split(':', 1)
            line = host_port

        # Parse host:port
        if ':' in line:
            host, port_str = line.rsplit(':', 1)
            try:
                port = int(port_str)
                return Proxy(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    proxy_type=proxy_type
                )
            except ValueError:
                pass

        return None

    def add_proxy(self, proxy: Proxy):
        """Add a single proxy."""
        self.proxies.append(proxy)

    def check_proxy_health(self, proxy: Proxy, test_url: str = "https://httpbin.org/ip",
                          timeout: int = 5) -> bool:
        """
        Check if a proxy is working.

        Args:
            proxy: Proxy to test
            test_url: URL to test against
            timeout: Request timeout

        Returns:
            True if proxy is healthy
        """
        try:
            response = requests.get(
                test_url,
                proxies=proxy.to_dict(),
                timeout=timeout
            )
            return response.status_code == 200
        except Exception:
            return False

    def filter_healthy_proxies(self, test_url: str = "https://httpbin.org/ip",
                              timeout: int = 5, max_workers: int = 10) -> int:
        """
        Filter proxies to find healthy ones.

        Args:
            test_url: URL to test proxies against
            timeout: Request timeout per proxy
            max_workers: Maximum concurrent tests

        Returns:
            Number of healthy proxies found
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        self.healthy_proxies.clear()
        healthy_count = 0

        def test_proxy(proxy: Proxy) -> Tuple[Proxy, bool]:
            is_healthy = self.check_proxy_health(proxy, test_url, timeout)
            return proxy, is_healthy

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all proxy tests
            future_to_proxy = {
                executor.submit(test_proxy, proxy): proxy
                for proxy in self.proxies
            }

            # Collect results
            for future in as_completed(future_to_proxy):
                proxy, is_healthy = future.result()
                if is_healthy:
                    self.healthy_proxies.append(proxy)
                    healthy_count += 1
                    print(f"✓ Healthy proxy: {proxy.host}:{proxy.port}")
                else:
                    self.dead_proxies.add(f"{proxy.host}:{proxy.port}")
                    print(f"✗ Dead proxy: {proxy.host}:{proxy.port}")

        return healthy_count

    def get_next_proxy(self) -> Optional[Proxy]:
        """
        Get the next proxy using round-robin rotation.

        Returns:
            Next proxy or None if no proxies available
        """
        if not self.healthy_proxies:
            return None

        proxy = self.healthy_proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.healthy_proxies)
        return proxy

    def get_random_proxy(self) -> Optional[Proxy]:
        """
        Get a random proxy from healthy proxies.

        Returns:
            Random proxy or None if no proxies available
        """
        if not self.healthy_proxies:
            return None

        return random.choice(self.healthy_proxies)

    def get_all_healthy_proxies(self) -> List[Proxy]:
        """Get all healthy proxies."""
        return self.healthy_proxies.copy()

    def remove_dead_proxy(self, proxy: Proxy):
        """Remove a proxy from the healthy list."""
        if proxy in self.healthy_proxies:
            self.healthy_proxies.remove(proxy)
            self.dead_proxies.add(f"{proxy.host}:{proxy.port}")

    def get_stats(self) -> Dict[str, int]:
        """Get proxy statistics."""
        return {
            "total": len(self.proxies),
            "healthy": len(self.healthy_proxies),
            "dead": len(self.dead_proxies)
        }

    def clear_dead_proxies(self):
        """Clear the dead proxies set."""
        self.dead_proxies.clear()


def create_sample_proxies() -> List[Proxy]:
    """Create some sample proxies for testing."""
    return [
        Proxy(host="proxy1.example.com", port=8080),
        Proxy(host="proxy2.example.com", port=8080, username="user", password="pass"),
        Proxy(host="socks.example.com", port=1080, proxy_type="socks5"),
    ]


def load_proxies_from_string(proxy_string: str) -> List[Proxy]:
    """
    Load proxies from a string (newline or comma separated).

    Args:
        proxy_string: String containing proxies

    Returns:
        List of Proxy objects
    """
    proxies = []

    # Split by newlines or commas
    for line in proxy_string.replace(',', '\n').split('\n'):
        line = line.strip()
        if line:
            proxy = ProxyManager()._parse_proxy_line(line)
            if proxy:
                proxies.append(proxy)

    return proxies