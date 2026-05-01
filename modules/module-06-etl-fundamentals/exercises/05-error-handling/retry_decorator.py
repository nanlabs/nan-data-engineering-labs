#!/usr/bin/env python3
"""
Retry decorator with exponential backoff.
"""
import time
import logging
from functools import wraps
from typing import Type, Tuple

logger = logging.getLogger(__name__)

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay (exponential backoff)
        exceptions: Tuple of exceptions to catch and retry

    Example:
        @retry(max_attempts=3, delay=1, backoff=2)
        def fetch_data():
            response = requests.get(url)
            return response.json()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay

            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise

                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {current_delay:.2f}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1

        return wrapper
    return decorator

# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Simulate flaky function
    attempt_count = 0

    @retry(max_attempts=5, delay=0.5, backoff=2)
    def flaky_function():
        """Fails first 3 times, succeeds on 4th."""
        global attempt_count
        attempt_count += 1

        if attempt_count < 4:
            raise ConnectionError(f"Failed attempt {attempt_count}")

        return f"Success on attempt {attempt_count}!"

    print("Testing retry decorator...")
    result = flaky_function()
    print(f"Result: {result}")
