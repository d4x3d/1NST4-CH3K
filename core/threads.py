"""
Threading Module

This module handles concurrent processing of Instagram account checks
using thread pools and rate limiting.
"""

import time
import threading
from typing import List, Dict, Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from dataclasses import dataclass
from queue import Queue, Empty
import random


@dataclass
class ThreadResult:
    """Result from a threaded operation."""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time: float = 0.0


class RateLimiter:
    """Rate limiter for controlling request frequency."""

    def __init__(self, requests_per_second: float = 1.0):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second
        """
        self.requests_per_second = requests_per_second
        self.interval = 1.0 / requests_per_second if requests_per_second > 0 else 0
        self.last_request_time = 0.0
        self.lock = threading.Lock()

    def acquire(self):
        """Acquire permission to make a request."""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time

            if time_since_last < self.interval:
                sleep_time = self.interval - time_since_last
                time.sleep(sleep_time)

            self.last_request_time = time.time()

    def update_rate(self, requests_per_second: float):
        """Update the rate limit."""
        with self.lock:
            self.requests_per_second = requests_per_second
            self.interval = 1.0 / requests_per_second if requests_per_second > 0 else 0


class ThreadedChecker:
    """Threaded Instagram account checker with rate limiting."""

    def __init__(self, max_workers: int = 5, requests_per_second: float = 1.0):
        """
        Initialize threaded checker.

        Args:
            max_workers: Maximum number of worker threads
            requests_per_second: Rate limit for requests
        """
        self.max_workers = max_workers
        self.rate_limiter = RateLimiter(requests_per_second)
        self.results: List[ThreadResult] = []
        self.lock = threading.Lock()

    def check_with_rate_limit(self, check_func: Callable, *args, **kwargs) -> ThreadResult:
        """
        Execute a check function with rate limiting.

        Args:
            check_func: Function to execute
            *args, **kwargs: Arguments for the function

        Returns:
            ThreadResult object
        """
        start_time = time.time()
        self.rate_limiter.acquire()

        try:
            result = check_func(*args, **kwargs)
            execution_time = time.time() - start_time
            return ThreadResult(
                success=True,
                data=result,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return ThreadResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=execution_time
            )

    def check_batch_threaded(self, items: List[Any], check_func: Callable,
                           *args, **kwargs) -> List[ThreadResult]:
        """
        Check multiple items using thread pool.

        Args:
            items: List of items to check
            check_func: Function to execute for each item
            *args, **kwargs: Additional arguments for check_func

        Returns:
            List of ThreadResult objects
        """
        self.results.clear()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {}
            for item in items:
                future = executor.submit(
                    self.check_with_rate_limit,
                    check_func,
                    item,
                    *args,
                    **kwargs
                )
                future_to_item[future] = item

            # Collect results as they complete
            for future in as_completed(future_to_item):
                result = future.result()
                with self.lock:
                    self.results.append(result)

        return self.results

    def update_rate_limit(self, requests_per_second: float):
        """Update the rate limit."""
        self.rate_limiter.update_rate(requests_per_second)


class ProgressTracker:
    """Track progress of threaded operations."""

    def __init__(self, total_items: int):
        """
        Initialize progress tracker.

        Args:
            total_items: Total number of items to process
        """
        self.total_items = total_items
        self.completed_items = 0
        self.successful_items = 0
        self.failed_items = 0
        self.lock = threading.Lock()

    def increment_completed(self, success: bool = True):
        """Increment completion counter."""
        with self.lock:
            self.completed_items += 1
            if success:
                self.successful_items += 1
            else:
                self.failed_items += 1

    def get_progress(self) -> Dict[str, Any]:
        """Get current progress statistics."""
        with self.lock:
            return {
                "total": self.total_items,
                "completed": self.completed_items,
                "successful": self.successful_items,
                "failed": self.failed_items,
                "remaining": self.total_items - self.completed_items,
                "percentage": (self.completed_items / self.total_items * 100) if self.total_items > 0 else 0
            }


class BoundedQueue:
    """Thread-safe bounded queue for coordinating work."""

    def __init__(self, max_size: int = 1000):
        """
        Initialize bounded queue.

        Args:
            max_size: Maximum queue size
        """
        self.queue = Queue(maxsize=max_size)
        self.lock = threading.Lock()

    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None):
        """Put item in queue."""
        self.queue.put(item, block=block, timeout=timeout)

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """Get item from queue."""
        return self.queue.get(block=block, timeout=timeout)

    def empty(self) -> bool:
        """Check if queue is empty."""
        return self.queue.empty()

    def full(self) -> bool:
        """Check if queue is full."""
        return self.queue.full()

    def size(self) -> int:
        """Get queue size."""
        return self.queue.qsize()


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks.

    Args:
        items: List to split
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    chunks = []
    for i in range(0, len(items), chunk_size):
        chunks.append(items[i:i + chunk_size])
    return chunks


def run_with_timeout(func: Callable, timeout: float, *args, **kwargs) -> Any:
    """
    Run a function with a timeout.

    Args:
        func: Function to run
        timeout: Timeout in seconds
        *args, **kwargs: Function arguments

    Returns:
        Function result or None if timeout
    """
    result = [None]
    error = [None]  # type: ignore

    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            error[0] = e  # type: ignore

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return None  # Timeout

    if error[0]:
        raise error[0]

    return result[0]


class AdaptiveRateLimiter:
    """Rate limiter that adapts based on response times and errors."""

    def __init__(self, initial_rps: float = 1.0, min_rps: float = 0.1, max_rps: float = 5.0):
        """
        Initialize adaptive rate limiter.

        Args:
            initial_rps: Initial requests per second
            min_rps: Minimum requests per second
            max_rps: Maximum requests per second
        """
        self.target_rps = initial_rps
        self.min_rps = min_rps
        self.max_rps = max_rps
        self.rate_limiter = RateLimiter(initial_rps)

        self.response_times: List[float] = []
        self.error_count = 0
        self.success_count = 0
        self.lock = threading.Lock()

    def record_request(self, response_time: float, success: bool):
        """Record a request result to adapt rate limiting."""
        with self.lock:
            self.response_times.append(response_time)
            if success:
                self.success_count += 1
            else:
                self.error_count += 1

            # Keep only recent response times
            if len(self.response_times) > 100:
                self.response_times = self.response_times[-50:]

            self._adapt_rate()

    def _adapt_rate(self):
        """Adapt the rate based on performance metrics."""
        if len(self.response_times) < 10:
            return  # Not enough data

        avg_response_time = sum(self.response_times) / len(self.response_times)
        success_rate = self.success_count / (self.success_count + self.error_count) if (self.success_count + self.error_count) > 0 else 0

        # Adjust rate based on performance
        if success_rate > 0.9 and avg_response_time < 2.0:
            # Good performance, can increase rate
            self.target_rps = min(self.target_rps * 1.1, self.max_rps)
        elif success_rate < 0.7 or avg_response_time > 5.0:
            # Poor performance, decrease rate
            self.target_rps = max(self.target_rps * 0.8, self.min_rps)

        self.rate_limiter.update_rate(self.target_rps)

    def acquire(self):
        """Acquire permission to make a request."""
        self.rate_limiter.acquire()

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        with self.lock:
            return {
                "target_rps": self.target_rps,
                "avg_response_time": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
                "success_rate": self.success_count / (self.success_count + self.error_count) if (self.success_count + self.error_count) > 0 else 0,
                "total_requests": self.success_count + self.error_count
            }