"""
Cache Service Module

This module provides caching functionality for API responses.
"""
import os
from models.db_model import DatabaseManager

class CacheService:
    def __init__(self, cache_dir="response_cache"):
        """
        Initialize the cache service
        
        Args:
            cache_dir (str): Directory for file-based cache
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize database manager
        self.db_manager = DatabaseManager()
        
        # Initialize database cache and migrate existing file cache if needed
        self._initialize_cache()
    
    def _initialize_cache(self):
        """Initialize the database cache and migrate file-based cache if necessary"""
        self.db_manager.migrate_file_cache_to_db(self.cache_dir)
    
    def check_cache(self, cache_key):
        """
        Check if a response exists in cache and return it
        
        Args:
            cache_key (str): Unique key for the cached item
            
        Returns:
            Any: The cached response or None if not found
        """
        return self.db_manager.check_cache(cache_key)
    
    def save_to_cache(self, cache_key, response):
        """
        Save a response to the cache
        
        Args:
            cache_key (str): Unique key for the cached item
            response: The response to cache
            
        Returns:
            bool: True if successfully cached, False otherwise
        """
        return self.db_manager.save_to_cache(cache_key, response)