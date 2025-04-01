"""Caching utilities for reducing repeated operations."""

import hashlib
import json
import logging
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, cast

# Set up logging
logger = logging.getLogger(__name__)

# Type variable for generic function return types
T = TypeVar("T")

# Default cache directory
DEFAULT_CACHE_DIR = os.path.expanduser("~/.gac_cache")

# Default cache expiration (24 hours in seconds)
DEFAULT_CACHE_EXPIRATION = 86400


class Cache:
    """A simple disk-based cache for expensive operations."""

    def __init__(self, cache_dir: Optional[str] = None, expiration: int = DEFAULT_CACHE_EXPIRATION):
        """
        Initialize the cache.

        Args:
            cache_dir: Directory to store cache files (defaults to ~/.gac_cache)
            expiration: Cache expiration time in seconds (defaults to 24 hours)
        """
        self.cache_dir = Path(cache_dir or DEFAULT_CACHE_DIR)
        self.expiration = expiration
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists."""
        with self._lock:
            if not self.cache_dir.exists():
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created cache directory: {self.cache_dir}")

    def _get_cache_key(self, key_data: Any) -> str:
        """
        Generate a cache key from the input data.

        Args:
            key_data: Data to generate a key from

        Returns:
            A string hash representing the data
        """
        if isinstance(key_data, str):
            data_str = key_data
        else:
            try:
                data_str = json.dumps(key_data, sort_keys=True)
            except TypeError:
                # If data is not JSON serializable, use its string representation
                data_str = str(key_data)

        return hashlib.md5(data_str.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """
        Get the file path for a cache key.

        Args:
            key: Cache key

        Returns:
            Path to the cache file
        """
        return self.cache_dir / f"{key}.json"

    def get(self, key_data: Any, default: Any = None) -> Any:
        """
        Get a value from the cache.

        Args:
            key_data: Data to generate a key from
            default: Default value to return if key not found

        Returns:
            The cached value or the default
        """
        with self._lock:
            key = self._get_cache_key(key_data)
            cache_path = self._get_cache_path(key)

            if not cache_path.exists():
                logger.debug(f"Cache miss for key: {key}")
                return default

            try:
                with open(cache_path, "r") as f:
                    cache_data = json.load(f)

                # Check if cache has expired
                if time.time() - cache_data["timestamp"] > self.expiration:
                    logger.debug(f"Cache expired for key: {key}")
                    cache_path.unlink(missing_ok=True)
                    return default

                logger.debug(f"Cache hit for key: {key}")
                return cache_data["value"]
            except (json.JSONDecodeError, KeyError, IOError) as e:
                logger.warning(f"Error reading cache for key {key}: {e}")
                # Remove invalid cache file
                cache_path.unlink(missing_ok=True)
                return default

    def set(self, key_data: Any, value: Any) -> None:
        """
        Store a value in the cache.

        Args:
            key_data: Data to generate a key from
            value: Value to store
        """
        with self._lock:
            key = self._get_cache_key(key_data)
            cache_path = self._get_cache_path(key)

            # Create cache data with timestamp
            cache_data = {"timestamp": time.time(), "value": value}

            try:
                # Write to a temporary file first, then rename for atomicity
                fd, temp_path = tempfile.mkstemp(dir=self.cache_dir)
                try:
                    with os.fdopen(fd, "w") as f:
                        json.dump(cache_data, f)
                    # Use os.replace for atomic operation
                    os.replace(temp_path, cache_path)
                    logger.debug(f"Cached value for key: {key}")
                except (IOError, TypeError, json.JSONDecodeError):
                    # Clean up the temporary file if an error occurs
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    raise
            except (TypeError, IOError) as e:
                logger.warning(f"Error writing cache for key {key}: {e}")

    def delete(self, key_data: Any) -> None:
        """
        Delete a value from the cache.

        Args:
            key_data: Data to generate a key from
        """
        with self._lock:
            key = self._get_cache_key(key_data)
            cache_path = self._get_cache_path(key)

            if cache_path.exists():
                cache_path.unlink()
                logger.debug(f"Deleted cache for key: {key}")

    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.debug("Cleared all cached values")

    def clear_expired(self) -> int:
        """
        Clear all expired cache entries.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            cleared_count = 0
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, "r") as f:
                        cache_data = json.load(f)

                    # Check if cache has expired
                    if time.time() - cache_data["timestamp"] > self.expiration:
                        cache_file.unlink()
                        cleared_count += 1
                except (json.JSONDecodeError, KeyError, IOError):
                    # Invalid cache file, remove it
                    cache_file.unlink(missing_ok=True)
                    cleared_count += 1

            logger.debug(f"Cleared {cleared_count} expired cache entries")
            return cleared_count


def cached(
    func: Optional[Callable[..., T]] = None,
    *,
    cache_instance: Optional[Cache] = None,
    expiration: Optional[int] = None,
    key_prefix: str = "",
) -> Callable[..., T]:
    """
    Decorator for caching function results.

    Args:
        func: Function to decorate
        cache_instance: Optional cache instance to use
        expiration: Cache expiration time in seconds
        key_prefix: Prefix for cache keys

    Returns:
        Decorated function
    """

    def decorator(f: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create or use provided cache instance
            nonlocal cache_instance
            if cache_instance is None:
                cache_instance = Cache(expiration=expiration or DEFAULT_CACHE_EXPIRATION)

            # Create cache key from function name, args, and kwargs
            cache_key = {
                "prefix": key_prefix,
                "func": f.__module__ + "." + f.__name__,
                "args": args,
                "kwargs": {k: v for k, v in kwargs.items() if k != "cache_skip"},
            }

            # Skip cache if requested
            if kwargs.get("cache_skip", False):
                if "cache_skip" in kwargs:
                    del kwargs["cache_skip"]
                return f(*args, **kwargs)

            # Try to get from cache
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                return cast(T, cached_result)

            # Compute and cache result
            result = f(*args, **kwargs)
            try:
                cache_instance.set(cache_key, result)
            except Exception as e:
                logger.warning(f"Failed to cache result: {e}")

            return result

        return wrapper

    # Handle both @cached and @cached() syntax
    if func is None:
        return decorator
    return decorator(func)
