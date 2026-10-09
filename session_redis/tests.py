#!/usr/bin/env python3
"""Unit tests for session_redis module"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock

import redis
from session_redis.session import RedisSessionStore


class TestSessionRedisErrorHandling(unittest.TestCase):
    """Test session_redis error handling for graceful degradation"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_redis = Mock(spec=redis.Redis)
        self.store = RedisSessionStore(
            redis=self.mock_redis,
            prefix='test:',
            session_class=Mock
        )

    def test_get_nonexistent_session_returns_new(self):
        """Non-existent sessions should return a new session"""
        self.mock_redis.get.return_value = None
        result = self.store.get('nonexistent-sid')
        self.assertIsNotNone(result)
        self.mock_redis.get.assert_called_once()

    def test_get_redis_exception_returns_new(self):
        """Redis exceptions should be caught and return new session"""
        self.mock_redis.get.side_effect = redis.ConnectionError("Connection failed")
        result = self.store.get('test-sid')
        self.assertIsNotNone(result)

    def test_get_redis_auth_error_returns_new(self):
        """Redis auth errors should be caught and return new session"""
        self.mock_redis.get.side_effect = redis.AuthenticationError("Auth failed")
        result = self.store.get('test-sid')
        self.assertIsNotNone(result)

    def test_get_invalid_json_returns_new(self):
        """Invalid JSON in session should return new session"""
        self.mock_redis.get.return_value = b'not-valid-json-{{{{'
        result = self.store.get('test-sid')
        self.assertIsNotNone(result)

    def test_save_redis_exception_handled(self):
        """save() should handle Redis exceptions gracefully"""
        self.mock_redis.set.side_effect = redis.ConnectionError("Connection failed")
        session = Mock()
        session.sid = 'test-sid'
        session.uid = 1
        result = self.store.save(session)
        self.assertFalse(result)

    def test_delete_redis_exception_handled(self):
        """delete() should handle Redis exceptions gracefully"""
        self.mock_redis.delete.side_effect = redis.ConnectionError("Connection failed")
        session = Mock()
        session.sid = 'test-sid'
        result = self.store.delete(session)
        self.assertFalse(result)

    def test_get_session_init_exception_returns_new(self):
        """Session initialization errors should be caught"""
        self.mock_redis.get.return_value = b'{"uid": 1, "login": "test"}'
        self.store.session_class = Mock(side_effect=Exception("Session init failed"))
        result = self.store.get('test-sid')
        self.assertIsNotNone(result)


class TestSessionRedisIntegration(unittest.TestCase):
    """Integration tests with real Redis"""

    @classmethod
    def setUpClass(cls):
        """Set up real Redis connection for integration tests"""
        try:
            cls.redis = redis.from_url('redis://localhost:6379')
            cls.redis.ping()
            cls.redis_available = True
        except (redis.ConnectionError, Exception):
            cls.redis_available = False

    def setUp(self):
        """Clean up test data"""
        if self.redis_available:
            # Clean test keys
            for key in self.redis.keys('test:*'):
                self.redis.delete(key)

    def test_real_redis_connection(self):
        """Test with real Redis instance"""
        if not self.redis_available:
            self.skipTest("Redis not available")

        store = RedisSessionStore(
            redis=self.redis,
            prefix='test:',
            session_class=Mock
        )

        # Should handle gracefully
        result = store.get('nonexistent')
        self.assertIsNotNone(result)

    def test_real_corrupted_data(self):
        """Test handling of corrupted data in Redis"""
        if not self.redis_available:
            self.skipTest("Redis not available")

        self.redis.set('test:corrupted', 'invalid-json-{{{')

        store = RedisSessionStore(
            redis=self.redis,
            prefix='test:',
            session_class=Mock
        )

        result = store.get('corrupted')
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
