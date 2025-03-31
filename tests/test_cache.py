"""Tests for the cache module."""

import json
import time
from pathlib import Path

from gac.cache import DEFAULT_CACHE_DIR, DEFAULT_CACHE_EXPIRATION, Cache, cached


class TestCache:
    """Tests for the Cache class."""

    def setup_method(self):
        """Set up a test cache directory."""
        self.test_cache_dir = "test_cache"
        self.cache = Cache(cache_dir=self.test_cache_dir, expiration=60)

    def teardown_method(self):
        """Clean up the test cache directory."""
        # Remove all test cache files
        if Path(self.test_cache_dir).exists():
            for file in Path(self.test_cache_dir).glob("*.json"):
                file.unlink()
            Path(self.test_cache_dir).rmdir()

    def test_init(self):
        """Test initialization of the Cache."""
        assert self.cache.cache_dir == Path(self.test_cache_dir)
        assert self.cache.expiration == 60
        assert Path(self.test_cache_dir).exists()

    def test_cache_dir_default(self):
        """Test default cache directory."""
        cache = Cache()
        assert cache.cache_dir == Path(DEFAULT_CACHE_DIR)
        assert cache.expiration == DEFAULT_CACHE_EXPIRATION

    def test_get_cache_key(self):
        """Test generating cache keys."""
        # Test with string
        key = self.cache._get_cache_key("test")
        assert isinstance(key, str)
        assert len(key) > 0

        # Test with dictionary
        key = self.cache._get_cache_key({"a": 1, "b": 2})
        assert isinstance(key, str)
        assert len(key) > 0

        # Test with non-JSON serializable object
        class TestObj:
            pass

        key = self.cache._get_cache_key(TestObj())
        assert isinstance(key, str)
        assert len(key) > 0

    def test_get_cache_path(self):
        """Test getting cache file path."""
        path = self.cache._get_cache_path("test_key")
        assert path == Path(self.test_cache_dir) / "test_key.json"

    def test_set_get(self):
        """Test setting and getting values."""
        # Set a value
        self.cache.set("test_key", "test_value")

        # Check that the file exists
        cache_file = Path(self.test_cache_dir) / f"{self.cache._get_cache_key('test_key')}.json"
        assert cache_file.exists()

        # Get the value back
        value = self.cache.get("test_key")
        assert value == "test_value"

    def test_get_missing(self):
        """Test getting a missing value."""
        value = self.cache.get("missing_key", "default_value")
        assert value == "default_value"

    def test_get_expired(self):
        """Test getting an expired value."""
        # Create a cache with a very short expiration
        cache = Cache(cache_dir=self.test_cache_dir, expiration=0.1)

        # Set a value
        cache.set("test_key", "test_value")

        # Wait for it to expire
        time.sleep(0.2)

        # Try to get it back, should return default
        value = cache.get("test_key", "default_value")
        assert value == "default_value"

    def test_get_invalid_json(self):
        """Test getting a value with invalid JSON."""
        # Create an invalid cache file
        key = self.cache._get_cache_key("test_key")
        cache_file = self.cache._get_cache_path(key)

        with open(cache_file, "w") as f:
            f.write("invalid json")

        # Try to get it back, should return default
        value = self.cache.get("test_key", "default_value")
        assert value == "default_value"

        # File should be deleted
        assert not cache_file.exists()

    def test_delete(self):
        """Test deleting a cached value."""
        # Set a value
        self.cache.set("test_key", "test_value")

        # Check it exists
        key = self.cache._get_cache_key("test_key")
        cache_file = self.cache._get_cache_path(key)
        assert cache_file.exists()

        # Delete it
        self.cache.delete("test_key")

        # Check it's gone
        assert not cache_file.exists()

        # Deleting non-existent key should not raise
        self.cache.delete("missing_key")

    def test_clear(self):
        """Test clearing all cached values."""
        # Set multiple values
        self.cache.set("test_key1", "test_value1")
        self.cache.set("test_key2", "test_value2")

        # Check files exist
        assert len(list(Path(self.test_cache_dir).glob("*.json"))) == 2

        # Clear all
        self.cache.clear()

        # Check all files are gone
        assert len(list(Path(self.test_cache_dir).glob("*.json"))) == 0

    def test_clear_expired(self):
        """Test clearing only expired cached values."""
        # Create a cache with mixed expiration times
        cache = Cache(cache_dir=self.test_cache_dir, expiration=60)

        # Set a value that won't expire
        cache.set("fresh_key", "fresh_value")

        # Set a value with a fake timestamp that's expired
        key = cache._get_cache_key("expired_key")
        path = cache._get_cache_path(key)
        with open(path, "w") as f:
            json.dump(
                {"timestamp": time.time() - 120, "value": "expired_value"}, f  # 2 minutes ago
            )

        # Set an invalid file
        invalid_path = Path(self.test_cache_dir) / "invalid.json"
        with open(invalid_path, "w") as f:
            f.write("invalid json")

        # Clear expired
        cleared = cache.clear_expired()

        # Should have cleared 2 files (expired and invalid)
        assert cleared == 2

        # Check only fresh file remains
        files = list(Path(self.test_cache_dir).glob("*.json"))
        assert len(files) == 1
        fresh_key = cache._get_cache_key("fresh_key")
        assert cache._get_cache_path(fresh_key) in files


class TestCachedDecorator:
    """Tests for the cached decorator."""

    def test_cached_functionality(self):
        """Test basic caching with the decorator."""
        # Create a wrapper around Cache for testing
        test_cache = Cache(cache_dir="test_cache_func", expiration=60)

        # Track function calls
        calls = []

        # Function to test caching on
        def test_func(x, y):
            calls.append((x, y))
            return x + y

        # Create a decorated function
        cached_func = cached(cache_instance=test_cache)(test_func)

        # First call should compute and cache
        assert cached_func(1, 2) == 3
        assert len(calls) == 1

        # Second call with same args should use cache
        assert cached_func(1, 2) == 3
        assert len(calls) == 1  # Still only one call

        # Call with different args should compute
        assert cached_func(3, 4) == 7
        assert len(calls) == 2

        # Test cache_skip
        assert cached_func(1, 2, cache_skip=True) == 3
        assert len(calls) == 3  # Should call again

        # Clean up
        test_cache.clear()
        if Path("test_cache_func").exists():
            for file in Path("test_cache_func").glob("*.json"):
                file.unlink()
            Path("test_cache_func").rmdir()
