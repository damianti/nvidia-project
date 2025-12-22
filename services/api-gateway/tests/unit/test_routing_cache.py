"""
Tests for routing_cache
"""
import pytest
from datetime import datetime, timedelta

from app.services.routing_cache import Cache, CacheEntry


class TestCacheEntry:
    """Tests for CacheEntry"""
    
    def test_cache_entry_creation(self):
        """Test creating a CacheEntry"""
        expires_at = datetime.now() + timedelta(seconds=1800)
        entry = CacheEntry(
            target_host="172.19.0.1",
            target_port=32768,
            container_id="abc123",
            image_id=1,
            expires_at=expires_at
        )
        
        assert entry.target_host == "172.19.0.1"
        assert entry.target_port == 32768
        assert entry.container_id == "abc123"
        assert entry.image_id == 1
        assert entry.expires_at == expires_at


class TestCache:
    """Tests for Cache"""
    
    @pytest.fixture
    def cache(self):
        """Create cache instance"""
        return Cache()
    
    @pytest.fixture
    def valid_entry(self):
        """Create valid cache entry"""
        return CacheEntry(
            target_host="172.19.0.1",
            target_port=32768,
            container_id="abc123",
            image_id=1,
            expires_at=datetime.now() + timedelta(seconds=1800)
        )
    
    @pytest.fixture
    def expired_entry(self):
        """Create expired cache entry"""
        return CacheEntry(
            target_host="172.19.0.1",
            target_port=32768,
            container_id="abc123",
            image_id=1,
            expires_at=datetime.now() - timedelta(seconds=1)
        )
    
    def test_get_nonexistent_entry(self, cache):
        """Test getting non-existent entry"""
        result = cache.get("nonexistent.localhost", "127.0.0.1")
        assert result is None
    
    def test_set_and_get_entry(self, cache, valid_entry):
        """Test setting and getting entry"""
        cache.set("testapp.localhost", "127.0.0.1", valid_entry)
        result = cache.get("testapp.localhost", "127.0.0.1")
        
        assert result is not None
        assert result.target_host == "172.19.0.1"
        assert result.target_port == 32768
    
    def test_get_expired_entry(self, cache, expired_entry):
        """Test getting expired entry"""
        cache.set("testapp.localhost", "127.0.0.1", expired_entry)
        result = cache.get("testapp.localhost", "127.0.0.1")
        
        assert result is None
    
    def test_invalidate_entry(self, cache, valid_entry):
        """Test invalidating entry"""
        cache.set("testapp.localhost", "127.0.0.1", valid_entry)
        cache.invalidate("testapp.localhost", "127.0.0.1")
        
        result = cache.get("testapp.localhost", "127.0.0.1")
        assert result is None
    
    def test_invalidate_nonexistent_entry(self, cache):
        """Test invalidating non-existent entry (Error Case 3: Not Found).
        
        Verifies:
        - KeyError is raised when entry doesn't exist
        - Or method handles it gracefully
        
        Args:
            cache: Cache instance fixture
        """
        # Arrange & Act & Assert
        # The current implementation raises KeyError, so we test for that
        with pytest.raises(KeyError):
            cache.invalidate("nonexistent.localhost", "127.0.0.1")
    
    def test_clear_expired_entries(self, cache, valid_entry, expired_entry):
        """Test clearing expired entries"""
        cache.set("valid.localhost", "127.0.0.1", valid_entry)
        cache.set("expired.localhost", "127.0.0.1", expired_entry)
        
        removed = cache.clear_expired()
        
        assert removed == 1
        assert cache.get("valid.localhost", "127.0.0.1") is not None
        assert cache.get("expired.localhost", "127.0.0.1") is None
    
    def test_clear_expired_no_expired_entries(self, cache, valid_entry):
        """Test clearing expired when none exist"""
        cache.set("valid.localhost", "127.0.0.1", valid_entry)
        
        removed = cache.clear_expired()
        
        assert removed == 0
        assert cache.get("valid.localhost", "127.0.0.1") is not None
    
    def test_multiple_entries_different_keys(self, cache, valid_entry):
        """Test multiple entries with different keys"""
        entry1 = CacheEntry(
            target_host="172.19.0.1",
            target_port=32768,
            container_id="abc123",
            image_id=1,
            expires_at=datetime.now() + timedelta(seconds=1800)
        )
        entry2 = CacheEntry(
            target_host="172.19.0.2",
            target_port=32769,
            container_id="def456",
            image_id=2,
            expires_at=datetime.now() + timedelta(seconds=1800)
        )
        
        cache.set("app1.localhost", "127.0.0.1", entry1)
        cache.set("app2.localhost", "127.0.0.1", entry2)
        
        result1 = cache.get("app1.localhost", "127.0.0.1")
        result2 = cache.get("app2.localhost", "127.0.0.1")
        
        assert result1.target_host == "172.19.0.1"
        assert result2.target_host == "172.19.0.2"
    
    def test_same_app_different_client_ips(self, cache, valid_entry):
        """Test same app with different client IPs"""
        entry1 = CacheEntry(
            target_host="172.19.0.1",
            target_port=32768,
            container_id="abc123",
            image_id=1,
            expires_at=datetime.now() + timedelta(seconds=1800)
        )
        entry2 = CacheEntry(
            target_host="172.19.0.2",
            target_port=32769,
            container_id="def456",
            image_id=1,
            expires_at=datetime.now() + timedelta(seconds=1800)
        )
        
        cache.set("testapp.localhost", "127.0.0.1", entry1)
        cache.set("testapp.localhost", "192.168.1.1", entry2)
        
        result1 = cache.get("testapp.localhost", "127.0.0.1")
        result2 = cache.get("testapp.localhost", "192.168.1.1")
        
        assert result1.target_host == "172.19.0.1"
        assert result2.target_host == "172.19.0.2"
    
    def test_overwrite_entry(self, cache, valid_entry):
        """Test overwriting existing entry"""
        entry1 = CacheEntry(
            target_host="172.19.0.1",
            target_port=32768,
            container_id="abc123",
            image_id=1,
            expires_at=datetime.now() + timedelta(seconds=1800)
        )
        entry2 = CacheEntry(
            target_host="172.19.0.2",
            target_port=32769,
            container_id="def456",
            image_id=1,
            expires_at=datetime.now() + timedelta(seconds=1800)
        )
        
        cache.set("testapp.localhost", "127.0.0.1", entry1)
        cache.set("testapp.localhost", "127.0.0.1", entry2)
        
        result = cache.get("testapp.localhost", "127.0.0.1")
        assert result.target_host == "172.19.0.2"
        assert result.target_port == 32769

