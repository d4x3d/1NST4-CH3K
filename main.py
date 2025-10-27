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
import json
import signal
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
                # Filter healthy proxies
                healthy_count = self.proxy_manager.filter_healthy_proxies(
                    test_url="https://httpbin.org/get",
                    timeout=15,
                    max_workers=10
                )
                if healthy_count > 0:
                    self.display.print_info_message(f"[+] Found {healthy_count} healthy proxies")
                else:
                    self.display.print_warning_message(f"[!] No healthy proxies found after testing. Running without proxies.")
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
                                    output_file: Optional[str] = None) -> List[dict]:
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
            return []

        # Load accounts
        try:
            with open(file_path, 'r') as f:
                accounts = [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.display.print_error_message(f"[✗] Error reading file: {e}")
            return []

        if not accounts:
            self.display.print_warning_message(f"[!] No accounts found in {file_path}")
            return []

        self.display.print_header_info(len(accounts), use_proxy)

        # Set up threaded checker
        threaded_checker = ThreadedChecker(max_workers=threads, requests_per_second=(1.0/delay) * threads)

        # Start live summary
        self.display.start_live_summary(len(accounts))

        # Define check function
        def check_with_proxy(account):
            proxy_url = None
            if use_proxy and self.proxy_manager.get_all_healthy_proxies():
                proxy = self.proxy_manager.get_next_proxy()
                if proxy:
                    proxy_url = str(proxy)

            try:
                checker = InstagramChecker(proxy=proxy_url)
                result = checker.check_account(account)
        
                # Print result and update summary
                self.display.print_result(account, result.result.value, result.message, result.response_time)
                self.display.update_summary()
        
                # Save if valid
                if result.result == CheckResult.VALID and output_file:
                    if output_file.endswith('.json'):
                        with open(output_file, 'a') as f:
                            f.write(json.dumps({
                                "email": account,
                                "result": result.result.value,
                                "message": result.message,
                                "response_time": result.response_time
                            }) + '\n')
                    else:
                        with open(output_file, 'a') as f:
                            f.write(account + '\n')
        
                return {
                    "email": account,
                    "result": result.result.value,
                    "message": result.message,
                    "response_time": result.response_time
                }
            except Exception as e:
                # Handle error
                self.display.print_result(account, "error", str(e), 0.0)
                self.display.update_summary()
                return {
                    "email": account,
                    "result": "error",
                    "message": str(e),
                    "response_time": 0.0
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

        self.display.print_credits()
        return [r.data for r in results if r.data]

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
        """Run the application in interactive mode."""
        # Print banner first
        print_banner()

        # Interactive prompts
        print("\n[?] Choose operation mode:")
        print("1. Check single account")
        print("2. Check accounts from file")
        choice = input("Enter choice (1 or 2): ").strip()

        email = None
        file_path = None
        threads = 5
        delay = 1.0
        proxy_file = None
        output_file = None

        if choice == '1':
            email = input("Enter email or username to check: ").strip()
            if not email:
                self.display.print_error_message("[✗] Email or username is required")
                return
        elif choice == '2':
            file_path = input("Enter path to file with emails/usernames (one per line): ").strip()
            if not file_path or not os.path.exists(file_path):
                self.display.print_error_message(f"[✗] File not found: {file_path}")
                return
            threads_input = input("Enter number of threads (default 5): ").strip()
            if threads_input:
                try:
                    threads = int(threads_input)
                except ValueError:
                    self.display.print_warning_message("[!] Invalid number, using default 5")
            delay_input = input("Enter delay between requests in seconds (default 1.0): ").strip()
            if delay_input:
                try:
                    delay = float(delay_input)
                except ValueError:
                    self.display.print_warning_message("[!] Invalid number, using default 1.0")
        else:
            self.display.print_error_message("[✗] Invalid choice")
            return

        # Proxy setup
        proxy_input = input("Enter path to proxy file (optional, press Enter to skip): ").strip()
        if proxy_input and os.path.exists(proxy_input):
            proxy_file = proxy_input
        else:
            proxy_file = None

        # Output file
        if choice == '2':
            output_input = input("Enter output file for results (optional, e.g., results.json): ").strip()
            if output_input:
                output_file = output_input

        # Set up proxy manager
        if not self.setup_proxy_manager(proxy_file):
            return

        # Determine operation mode
        if email:
            # Single account check
            self.check_single_account(email, use_proxy=bool(proxy_file))

        elif file_path:
            # File-based checking
            self.check_accounts_from_file(
                file_path=file_path,
                threads=threads,
                delay=delay,
                use_proxy=bool(proxy_file),
                output_file=output_file
            )


def main():
    """Main entry point."""
    # Load configuration
    config = load_config('data/config.yaml')

    parser = argparse.ArgumentParser(description="Instagram Account Checker")
    parser.add_argument('--file', required=True, help='Path to file with emails/usernames')
    parser.add_argument('--proxy', help='Path to proxy file')
    parser.add_argument('--threads', type=int, default=config.checker.max_threads, help=f'Number of threads (default: {config.checker.max_threads})')
    parser.add_argument('--delay', type=float, default=config.checker.delay_between_requests, help=f'Delay between requests (default: {config.checker.delay_between_requests})')
    parser.add_argument('--output', default=config.checker.output_file or 'results.txt', help=f'Output file for results (default: {config.checker.output_file or "results.txt"})')

    args = parser.parse_args()

    # Load proxy from config if not provided
    if not args.proxy:
        args.proxy = config.checker.proxy_file

    def signal_handler(sig, frame):
        print("\n[!] Interrupted. Results saved as they were processed.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        app = InstagramCheckerApp()
        # Print banner
        print_banner()

        # Set up proxy manager
        if args.proxy and not app.setup_proxy_manager(args.proxy):
            return

        # Check accounts from file
        results = app.check_accounts_from_file(
            file_path=args.file,
            threads=args.threads,
            delay=args.delay,
            use_proxy=bool(args.proxy),
            output_file=args.output
        )

        # Save all results to both JSON and TXT in result folder
        if results:
            os.makedirs(config.checker.output_dir, exist_ok=True)
            # Save to JSON
            with open(config.checker.output_json_file, 'w') as f:
                json.dump(results, f, indent=2)
            # Save to TXT
            with open(config.checker.output_txt_file, 'w') as f:
                for res in results:
                    f.write(f"{res['email']} - {res['result']} - {res['message']} - {res['response_time']}s\n")
            print(f"[S] All results saved to {config.checker.output_json_file} and {config.checker.output_txt_file}")

        app.display.print_credits()

    except KeyboardInterrupt:
        print("\n\n[!] Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[✗] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
