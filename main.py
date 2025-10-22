#!/usr/bin/env python3
"""
1NST4-CH3K - Instagram Account Checker

A powerful Instagram account validation tool with proxy support,
multi-threading, and beautiful CLI interface.

Created by: d4x3d
"""

import sys
import os
import time
import argparse
from pathlib import Path
from typing import List, Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.checker import InstagramChecker, CheckResult, check_accounts_from_file
    from core.proxy import ProxyManager
    from core.threads import ThreadedChecker
    from ui.display import InstagramDisplay, print_banner, print_result, print_summary_stats
    from utils.config import load_config
except ImportError as e:
    print(f"[✗] Error importing modules: {e}")
    print("Please ensure all dependencies are installed and project structure is correct.")
    sys.exit(1)


class InstagramCheckerApp:
    """Main application class for 1NST4-CH3K."""

    def __init__(self):
        """Initialize the application."""
        self.display = InstagramDisplay()
        self.proxy_manager = ProxyManager()
        self.checker = None

    def setup_proxy_manager(self, proxy_file: Optional[str] = None) -> bool:
        """
        Set up proxy manager.

        Args:
            proxy_file: Path to proxy file

        Returns:
            True if proxies loaded successfully
        """
        if proxy_file and os.path.exists(proxy_file):
            loaded = self.proxy_manager.load_from_file(proxy_file)
            if loaded > 0:
                self.display.print_info_message(f"[+] Loaded {loaded} proxies from {proxy_file}")
                return True
            else:
                self.display.print_warning_message(f"[!] No valid proxies found in {proxy_file}")
                return False

        # No proxy file provided or file doesn't exist
        self.display.print_info_message("[+] Running without proxies")
        return True

    def check_single_account(self, email: str, use_proxy: bool = False) -> None:
        """
        Check a single Instagram account.

        Args:
            email: Email or username to check
            use_proxy: Whether to use proxy rotation
        """
        self.display.print_header_info(1, use_proxy)

        # Get proxy if available
        proxy_url = None
        if use_proxy and self.proxy_manager.get_all_healthy_proxies():
            proxy = self.proxy_manager.get_next_proxy()
            if proxy:
                proxy_url = str(proxy)
                self.display.print_info_message(f"[+] Using proxy: {proxy.host}:{proxy.port}")

        # Perform check
        checker = InstagramChecker(proxy=proxy_url)
        result = checker.check_account(email)

        # Display result
        status_str = result.result.value
        print_result(email, status_str, result.message, result.response_time)

        # Show summary
        valid = 1 if result.result == CheckResult.VALID else 0
        invalid = 1 if result.result == CheckResult.INVALID else 0
        error = 1 if result.result == CheckResult.ERROR else 0
        print_summary_stats(valid, invalid, error, 1)

        self.display.print_credits()

    def check_accounts_from_file(self, file_path: str, threads: int = 5,
                               delay: float = 1.0, use_proxy: bool = False,
                               output_file: Optional[str] = None) -> None:
        """
        Check multiple accounts from a file.

        Args:
            file_path: Path to file containing emails/usernames
            threads: Number of threads to use
            delay: Delay between requests
            use_proxy: Whether to use proxy rotation
            output_file: Optional output file for results
        """
        if not os.path.exists(file_path):
            self.display.print_error_message(f"[✗] File not found: {file_path}")
            return

        # Load accounts
        try:
            with open(file_path, 'r') as f:
                accounts = [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.display.print_error_message(f"[✗] Error reading file: {e}")
            return

        if not accounts:
            self.display.print_warning_message(f"[!] No accounts found in {file_path}")
            return

        self.display.print_header_info(len(accounts), use_proxy)

        # Set up threaded checker
        threaded_checker = ThreadedChecker(max_workers=threads, requests_per_second=1.0/delay)

        # Start live summary
        self.display.start_live_summary(len(accounts))

        # Define check function
        def check_with_proxy(account):
            proxy_url = None
            if use_proxy and self.proxy_manager.get_all_healthy_proxies():
                proxy = self.proxy_manager.get_next_proxy()
                if proxy:
                    proxy_url = str(proxy)

            checker = InstagramChecker(proxy=proxy_url)
            result = checker.check_account(account)

            # Print result and update summary
            self.display.print_result(account, result.result.value, result.message, result.response_time)
            self.display.update_summary()

            return {
                "email": account,
                "result": result.result.value,
                "message": result.message,
                "response_time": result.response_time
            }

        # Perform checks
        self.display.print_loading_message(f"[~] Checking {len(accounts)} accounts with {threads} threads...")

        start_time = time.time()
        results = threaded_checker.check_batch_threaded(accounts, check_with_proxy)
        total_time = time.time() - start_time

        # Stop live summary
        self.display.stop_live_summary()

        # Count results
        valid_count = sum(1 for r in results if r.data and r.data["result"] == "valid")
        invalid_count = sum(1 for r in results if r.data and r.data["result"] == "invalid")
        error_count = sum(1 for r in results if not r.success or r.data["result"] == "error")

        # Show recent results in table format
        successful_results = [r.data for r in results if r.success and r.data]
        # Removed table display as per user request

        # Save results if output file specified
        if output_file:
            self.save_results(successful_results, output_file)

        self.display.print_credits()

    def save_results(self, results: List[dict], output_file: str) -> None:
        """Save results to file."""
        try:
            if output_file.endswith('.json'):
                import json
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2)
            elif output_file.endswith('.csv'):
                import csv
                with open(output_file, 'w', newline='') as f:
                    if results:
                        writer = csv.DictWriter(f, fieldnames=results[0].keys())
                        writer.writeheader()
                        writer.writerows(results)
            else:
                # Default to JSON
                import json
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2)

            self.display.print_success_message(f"[S] Results saved to {output_file}")

        except Exception as e:
            self.display.print_error_message(f"[✗] Error saving results: {e}")

    def run(self):
        """Run the application."""
        parser = argparse.ArgumentParser(
            description="1NST4-CH3K - Instagram Account Checker",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s --email user@example.com
  %(prog)s --file accounts.txt --threads 10 --delay 2.0
  %(prog)s --file accounts.txt --proxy proxies.txt --output results.json
  %(prog)s --batch accounts.txt --threads 5 --proxy proxies.txt
            """
        )

        parser.add_argument(
            '--email', '-e',
            type=str,
            help='Single email or username to check'
        )

        parser.add_argument(
            '--file', '-f',
            type=str,
            help='File containing emails/usernames to check (one per line)'
        )

        parser.add_argument(
            '--threads', '-t',
            type=int,
            default=5,
            help='Number of threads to use (default: 5)'
        )

        parser.add_argument(
            '--delay', '-d',
            type=float,
            default=1.0,
            help='Delay between requests in seconds (default: 1.0)'
        )

        parser.add_argument(
            '--proxy',
            type=str,
            help='File containing proxy list'
        )

        parser.add_argument(
            '--output', '-o',
            type=str,
            help='Output file for results (JSON/CSV format auto-detected by extension)'
        )

        parser.add_argument(
            '--batch',
            type=str,
            help='Batch mode - same as --file but with threading enabled by default'
        )

        args = parser.parse_args()

        # Print banner first
        print_banner()

        # Set up proxy manager
        if not self.setup_proxy_manager(args.proxy):
            return

        # Determine operation mode
        if args.email:
            # Single account check
            self.check_single_account(args.email, use_proxy=bool(args.proxy))

        elif args.file or args.batch:
            # File-based checking
            file_path = args.file or args.batch
            self.check_accounts_from_file(
                file_path=file_path,
                threads=args.threads,
                delay=args.delay,
                use_proxy=bool(args.proxy),
                output_file=args.output
            )

        else:
            # No arguments provided, show help
            parser.print_help()
            self.display.print_credits()


def main():
    """Main entry point."""
    try:
        app = InstagramCheckerApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\n[!] Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[✗] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
