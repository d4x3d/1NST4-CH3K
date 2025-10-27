"""
Instagram Account Checker Core Module

This module handles the core functionality of checking Instagram accounts
via the account recovery API endpoint.
"""

import json
import time
import random
import requests
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from bs4 import BeautifulSoup


class CheckResult(Enum):
    """Enumeration of possible check results."""
    VALID = "valid"
    INVALID = "invalid"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


@dataclass
class CheckResponse:
    """Data class for check results."""
    email: str
    result: CheckResult
    message: str
    response_data: Optional[Dict] = None
    response_time: float = 0.0


class InstagramChecker:
    """Main Instagram account checker class."""

    def __init__(self, proxy: Optional[str] = None, timeout: int = 10):
        """
        Initialize the Instagram checker.

        Args:
            proxy: Proxy URL (optional)
            timeout: Request timeout in seconds
        """
        self.session = requests.Session()
        self.proxy = proxy
        self.timeout = timeout
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:135.0) Gecko/20100101 Firefox/135.0",
        ]

        # Instagram API endpoint
        self.api_url = "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/"

        # Set up session headers
        self._setup_session()

    def _setup_session(self):
        """Set up the session with required headers."""
        # Clear existing headers
        self.session.headers.clear()

        # Set up base headers
        self.session.headers.update({
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=1",
            "Referer": "https://www.instagram.com/accounts/password/reset/",
            "Origin": "https://www.instagram.com",
            "DNT": "1",
            "Connection": "keep-alive",
        })

        # Rotate user agent
        self.session.headers.update({
            "User-Agent": random.choice(self.user_agents)
        })

    def _get_csrf_token(self) -> Optional[str]:
        """
        Get CSRF token from Instagram by fetching the password reset page.

        Returns:
            CSRF token extracted from cookies or headers
        """
        try:
            # First, clear any existing cookies
            self.session.cookies.clear()

            # Fetch the password reset page to get a fresh CSRF token
            response = self.session.get(
                "https://www.instagram.com/accounts/password/reset/",
                proxies={"http": self.proxy, "https": self.proxy} if self.proxy else None,
                timeout=self.timeout
            )

            # Try to extract CSRF token from cookies
            csrf_token = response.cookies.get('csrftoken')

            # If not found in cookies, try to extract from response headers or HTML
            if not csrf_token:
                # Look for csrftoken in response headers
                csrf_token = response.headers.get('x-csrftoken')

                # If still not found, try to extract from HTML content
                if not csrf_token:
                    import re
                    # Look for CSRF token pattern in HTML
                    token_pattern = r'csrf_token[\"\']?\s*[:=]\s*[\"\']([^\"\']+)[\"\']'
                    matches = re.search(token_pattern, response.text)
                    if matches:
                        csrf_token = matches.group(1)

            # If we still don't have a token, use a fallback
            if not csrf_token:
                csrf_token = "missing"  # Use "missing" to trigger Instagram's fallback

            return csrf_token

        except Exception as e:
            # Log the error and use fallback
            print(f"[!] Error fetching CSRF token: {e}")
            return "missing"  # Use "missing" as fallback

    def check_account(self, email_or_username: str) -> CheckResponse:
        """
        Check if an Instagram account exists.

        Args:
            email_or_username: Email address or username to check

        Returns:
            CheckResponse object with result
        """
        start_time = time.time()

        try:
            # Get CSRF token
            csrf_token = self._get_csrf_token()

            # Prepare request data
            data = {
                "email_or_username": email_or_username,
                "jazoest": "22064"  # Static value from the HAR file
            }

            # Update headers with CSRF token
            headers = {
                "X-CSRFToken": csrf_token,
                "X-Instagram-AJAX": "1",  # Simplified value
                "X-IG-App-ID": "936619743392459",
                "X-ASBD-ID": "129477",  # Updated ASBD ID
                "X-IG-WWW-Claim": "0",
                "X-Requested-With": "XMLHttpRequest"
            }

            # Make the request
            response = self.session.post(
                self.api_url,
                data=data,
                headers=headers,
                proxies={"http": self.proxy, "https": self.proxy} if self.proxy else None,
                timeout=self.timeout
            )

            response_time = time.time() - start_time

            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                return CheckResponse(
                    email=email_or_username,
                    result=CheckResult.ERROR,
                    message="Invalid JSON response",
                    response_time=response_time
                )

            # Analyze response
            if response.status_code == 200:
                if response_data.get("status") == "ok":
                    return CheckResponse(
                        email=email_or_username,
                        result=CheckResult.VALID,
                        message=response_data.get("toast_message", "Account exists"),
                        response_data=response_data,
                        response_time=response_time
                    )
                elif response_data.get("status") == "fail":
                    if "No users found" in response_data.get("message", ""):
                        return CheckResponse(
                            email=email_or_username,
                            result=CheckResult.INVALID,
                            message="Account does not exist",
                            response_data=response_data,
                            response_time=response_time
                        )
                    else:
                        return CheckResponse(
                            email=email_or_username,
                            result=CheckResult.ERROR,
                            message=f"API Error: {response_data.get('message', 'Unknown error')}",
                            response_data=response_data,
                            response_time=response_time
                        )
            elif response.status_code == 429:
                return CheckResponse(
                    email=email_or_username,
                    result=CheckResult.RATE_LIMITED,
                    message="Rate limited by Instagram",
                    response_time=response_time
                )
            else:
                return CheckResponse(
                    email=email_or_username,
                    result=CheckResult.ERROR,
                    message=f"HTTP {response.status_code}: {response.text[:100]}",
                    response_time=response_time
                )

        except requests.exceptions.Timeout:
            return CheckResponse(
                email=email_or_username,
                result=CheckResult.ERROR,
                message="Request timeout",
                response_time=time.time() - start_time
            )
        except requests.exceptions.ConnectionError:
            return CheckResponse(
                email=email_or_username,
                result=CheckResult.ERROR,
                message="Connection error",
                response_time=time.time() - start_time
            )
        except Exception as e:
            return CheckResponse(
                email=email_or_username,
                result=CheckResult.ERROR,
                message=f"Unexpected error: {str(e)}",
                response_time=time.time() - start_time
            )

        # This should never be reached, but just in case
        return CheckResponse(
            email=email_or_username,
            result=CheckResult.ERROR,
            message="Unknown error occurred",
            response_time=time.time() - start_time
        )

    def check_accounts_batch(self, emails_or_usernames: List[str],
                           delay: float = 1.0) -> List[CheckResponse]:
        """
        Check multiple accounts with optional delay between requests.

        Args:
            emails_or_usernames: List of emails/usernames to check
            delay: Delay between requests in seconds

        Returns:
            List of CheckResponse objects
        """
        results = []

        for i, email in enumerate(emails_or_usernames):
            if i > 0 and delay > 0:
                time.sleep(delay)

            result = self.check_account(email)
            results.append(result)

            # Rotate user agent periodically
            if i % 5 == 0:
                self.session.headers.update({
                    "User-Agent": random.choice(self.user_agents)
                })

        return results


def check_single_account(email_or_username: str, proxy: Optional[str] = None) -> CheckResponse:
    """
    Convenience function to check a single account.

    Args:
        email_or_username: Email or username to check
        proxy: Optional proxy URL

    Returns:
        CheckResponse object
    """
    checker = InstagramChecker(proxy=proxy)
    return checker.check_account(email_or_username)


def check_accounts_from_file(file_path: str, proxy: Optional[str] = None,
                           delay: float = 1.0) -> List[CheckResponse]:
    """
    Check accounts from a file.

    Args:
        file_path: Path to file containing emails/usernames
        proxy: Optional proxy URL
        delay: Delay between requests

    Returns:
        List of CheckResponse objects
    """
    try:
        with open(file_path, 'r') as f:
            emails = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading file: {e}")

    checker = InstagramChecker(proxy=proxy)
    return checker.check_accounts_batch(emails, delay)