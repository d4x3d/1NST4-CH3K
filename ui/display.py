"""
Display Module

This module handles the beautiful CLI interface with colors,
ASCII art, and real-time progress display for 1NST4-CH3K.
"""

import time
import sys
import threading
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.columns import Columns
from rich.align import Align


@dataclass
class DisplayConfig:
    """Configuration for display settings."""
    show_colors: bool = True
    show_progress: bool = True
    show_timestamps: bool = False
    max_results_display: int = 50


class InstagramDisplay:
    """Main display class for 1NST4-CH3K."""

    def __init__(self, config: Optional[DisplayConfig] = None):
        """
        Initialize the display.

        Args:
            config: Display configuration
        """
        self.config = config or DisplayConfig()
        self.console = Console()
        self.start_time = time.time()

        # Color scheme (Instagram inspired)
        self.colors = {
            "primary": "#E4405F",      # Instagram pink
            "secondary": "#833AB4",    # Instagram purple
            "gradient": ["#E4405F", "#F77737", "#FCAF45", "#833AB4"],
            "success": "#00C851",     # Green
            "error": "#FF1744",       # Red
            "warning": "#FF9800",     # Orange
            "info": "#2196F3",        # Blue
            "muted": "#9E9E9E"        # Gray
        }

        # Status icons
        self.icons = {
            "valid": "[✓]",
            "invalid": "[✗]",
            "error": "[!]",
            "rate_limited": "[#]",
            "loading": "[~]",
            "success": "[*]",
            "instagram": "[@]"
        }

        # Live summary
        self.live = None
        self.summary_text = Text()
        self.counts = {"valid": 0, "invalid": 0, "error": 0}
        self.total = 0
        self.lock = threading.Lock()

    def print_banner(self):
        """Print the 1NST4-CH3K banner."""
        banner = Text(self._get_banner_text(), style=f"bold {self.colors['primary']}")
        panel = Panel(
            Align.center(banner),
            border_style=self.colors["secondary"],
            padding=(1, 2)
        )
        self.console.print(panel)

    def _get_banner_text(self) -> str:
        """Get the ASCII art banner text."""
        return """
   ░▒▓█▓▒░▒▓███████▓▒░ ░▒▓███████▓▒░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░
 ░▒▓████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
    ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
    ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░   ░▒▓█▓▒░   ░▒▓████████▓▒░▒▓█▓▒░      ░▒▓████████▓▒░▒▓███████▓▒░░▒▓███████▓▒░
    ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░  ░▒▓█▓▒░          ░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
    ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░  ░▒▓█▓▒░          ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
    ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░   ░▒▓█▓▒░          ░▒▓█▓▒░░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░
                                                                                                          by D4X3D          
        """

    def print_header_info(self, total_accounts: int, using_proxies: bool = False):
        """Print header information before starting checks."""
        self.console.print(f"[?] Starting checks for {total_accounts} accounts", style=self.colors["info"])

        if using_proxies:
            self.console.print("[+] Using proxy rotation for enhanced performance", style=self.colors["secondary"])

        self.console.print(f"[T] Started at: {time.strftime('%H:%M:%S')}", style=self.colors["muted"])
        self.console.print()  # Empty line

    def create_progress_display(self, total_accounts: int) -> Progress:
        """Create a progress display for real-time updates."""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold]{task.description}[/bold]"),
            BarColumn(complete_style=self.colors["primary"]),
            TaskProgressColumn(),
            TextColumn("• {task.fields[rate]:.1f} checks/sec"),
            TextColumn("• ⏱ {task.fields[elapsed]}"),
            TimeRemainingColumn(),
            console=self.console
        )

        progress.add_task(
            "Checking accounts...",
            total=total_accounts,
            rate=0.0,
            elapsed="0:00:00"
        )

        return progress

    def print_result(self, email: str, status: str, message: str, response_time: float):
        """Print a single check result."""
        # Update counts
        with self.lock:
            if status == "valid":
                self.counts["valid"] += 1
            elif status == "invalid":
                self.counts["invalid"] += 1
            else:
                self.counts["error"] += 1

        # Color coding based on status
        if status == "valid":
            icon = self.icons["valid"]
            color = self.colors["success"]
        elif status == "invalid":
            icon = self.icons["invalid"]
            color = self.colors["muted"]
        elif status == "rate_limited":
            icon = self.icons["rate_limited"]
            color = self.colors["warning"]
        else:
            icon = self.icons["error"]
            color = self.colors["error"]

        # Format the result line
        result_text = Text.assemble(
            (icon, color),
            (" ", ""),
            (email, f"bold {color}"),
            (" → ", self.colors["muted"]),
            (message, color),
            (f" ({response_time:.2f}s)", self.colors["muted"])
        )

        self.console.print(result_text)

    def print_results_table(self, results: List[Dict[str, Any]]):
        """Print a table of all results."""
        if not results:
            return

        table = Table(show_header=True, header_style=f"bold {self.colors['primary']}")

        table.add_column("Email/Username", style="white", width=30)
        table.add_column("Status", style="bold", width=10)
        table.add_column("Message", style="white", width=40)
        table.add_column("Response Time", style="cyan", width=12)

        # Status counters
        valid_count = 0
        invalid_count = 0
        error_count = 0

        for result in results[-self.config.max_results_display:]:  # Show last N results
            status = result.get("result", "unknown")
            message = result.get("message", "")
            response_time = result.get("response_time", 0)

            # Update counters
            if status == "valid":
                valid_count += 1
                status_color = self.colors["success"]
            elif status == "invalid":
                invalid_count += 1
                status_color = self.colors["muted"]
            else:
                error_count += 1
                status_color = self.colors["error"]

            table.add_row(
                result.get("email", ""),
                f"[{status_color}]{status.upper()}[/{status_color}]",
                message,
                f"{response_time:.2f}s"
            )

        self.console.print(table)

        # Print summary statistics
        self.print_summary_stats(valid_count, invalid_count, error_count, len(results))

    def print_summary_stats(self, valid: int, invalid: int, error: int, total: int):
        """Print summary statistics inline."""
        total_time = time.time() - self.start_time
        rate = total / total_time if total_time > 0 else 0

        stats_text = Text.assemble(
            ("Valid: ", self.colors["success"]),
            (f"{valid}", f"bold {self.colors['success']}"),
            (" | Invalid: ", self.colors["muted"]),
            (f"{invalid}", f"bold {self.colors['muted']}"),
            (" | Errors: ", self.colors["error"]),
            (f"{error}", f"bold {self.colors['error']}"),
            (" | Total: ", self.colors["info"]),
            (f"{total}", f"bold {self.colors['info']}"),
            (" | Time: ", self.colors["warning"]),
            (f"{total_time:.1f}s", f"bold {self.colors['warning']}"),
            (" | Rate: ", self.colors["secondary"]),
            (f"{rate:.1f}/sec", f"bold {self.colors['secondary']}")
        )
        self.console.print(stats_text)

    def print_proxy_stats(self, proxy_manager_stats: Dict[str, int]):
        """Print proxy statistics."""
        if not proxy_manager_stats:
            return

        stats_text = Text.assemble(
            ("[+] Proxy Statistics\n", f"bold {self.colors['secondary']}"),
            ("═══════════════════\n", self.colors["muted"]),
            ("[-] Total proxies: ", self.colors["info"]),
            (f"{proxy_manager_stats.get('total', 0)}", f"bold {self.colors['info']}"),
            ("\n[✓] Healthy proxies: ", self.colors["success"]),
            (f"{proxy_manager_stats.get('healthy', 0)}", f"bold {self.colors['success']}"),
            ("\n[✗] Dead proxies: ", self.colors["error"]),
            (f"{proxy_manager_stats.get('dead', 0)}", f"bold {self.colors['error']}")
        )

        panel = Panel(
            stats_text,
            border_style=self.colors["secondary"],
            padding=(1, 2)
        )
        self.console.print(panel)

    def print_loading_message(self, message: str = "Processing..."):
        """Print a loading message with spinner."""
        self.console.print(f"[bold {self.colors['info']}]{self.icons['loading']} {message}[/bold {self.colors['info']}]")

    def print_success_message(self, message: str):
        """Print a success message."""
        self.console.print(f"[bold {self.colors['success']}]{self.icons['success']} {message}[/bold {self.colors['success']}]")

    def print_error_message(self, message: str):
        """Print an error message."""
        self.console.print(f"[bold {self.colors['error']}]{self.icons['error']} {message}[/bold {self.colors['error']}]")

    def print_warning_message(self, message: str):
        """Print a warning message."""
        self.console.print(f"[bold {self.colors['warning']}]{self.icons['error']} {message}[/bold {self.colors['warning']}]")

    def print_info_message(self, message: str):
        """Print an info message."""
        self.console.print(f"[bold {self.colors['info']}][i] {message}[/bold {self.colors['info']}]")

    def clear_screen(self):
        """Clear the console screen."""
        self.console.clear()

    def print_credits(self):
        """Print the tool credits."""
        credits_text = Text.assemble(
            ("1NST4-CH3K by ", self.colors["muted"]),
            ("d4x3d", f"bold {self.colors['primary']}"),
            (" v0.1.1", self.colors["muted"])
        )

        panel = Panel(
            credits_text,
            border_style=self.colors["primary"],
            padding=(0, 2)
        )
        self.console.print(panel)

    def start_live_summary(self, total: int):
        """Start live summary display."""
        self.total = total
        self.start_time = time.time()
        self.live = Live(self.summary_text, console=self.console, refresh_per_second=1, auto_refresh=True)
        self.live.start()

    def update_summary(self):
        """Update the live summary."""
        if self.live:
            total_time = time.time() - self.start_time
            rate = self.total / total_time if total_time > 0 else 0

            with self.lock:
                self.summary_text = Text.assemble(
                    ("Valid: ", self.colors["success"]),
                    (f"{self.counts['valid']}", f"bold {self.colors['success']}"),
                    (" | Invalid: ", self.colors["muted"]),
                    (f"{self.counts['invalid']}", f"bold {self.colors['muted']}"),
                    (" | Errors: ", self.colors["error"]),
                    (f"{self.counts['error']}", f"bold {self.colors['error']}"),
                    (" | Total: ", self.colors["info"]),
                    (f"{self.total}", f"bold {self.colors['info']}"),
                    (" | Time: ", self.colors["warning"]),
                    (f"{total_time:.1f}s", f"bold {self.colors['warning']}"),
                    (" | Rate: ", self.colors["secondary"]),
                    (f"{rate:.1f}/sec", f"bold {self.colors['secondary']}")
                )

            self.live.update(self.summary_text)

    def stop_live_summary(self):
        """Stop live summary display."""
        if self.live:
            self.live.stop()


# Global display instance
display = InstagramDisplay()


def print_banner():
    """Convenience function to print banner."""
    display.print_banner()


def print_result(email: str, status: str, message: str, response_time: float):
    """Convenience function to print result."""
    display.print_result(email, status, message, response_time)


def print_summary_stats(valid: int, invalid: int, error: int, total: int):
    """Convenience function to print summary statistics."""
    display.print_summary_stats(valid, invalid, error, total)