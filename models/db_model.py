"""
Database Models Module

This module handles database connections and operations for the calculator application.
"""
import mysql.connector
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from config.settings import DB_CONFIG

class DatabaseManager:
    """Database manager for the calculator application"""
    
    def __init__(self):
        """Initialize the database manager and create necessary tables"""
        self.create_database_if_not_exists()
    
    def create_database_if_not_exists(self):
        """Create the database and tables if they don't exist"""
        # Connect without specifying a database
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        
        try:
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            conn.database = DB_CONFIG['database']
            
            # Create cache table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS response_cache (
                    cache_key VARCHAR(255) PRIMARY KEY,
                    response_data LONGTEXT,
                    timestamp DATETIME
                )
            """)
            
            print("Database and tables created successfully")
            conn.commit()
        except Exception as e:
            print(f"Error creating database: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    def get_db_connection(self):
        """Get a connection to the MySQL database"""
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            return conn
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            return None
    
    def check_cache(self, cache_key: str) -> Optional[Any]:
        """Check if a response exists in cache and return it"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT response_data FROM response_cache WHERE cache_key = %s", 
                (cache_key,)
            )
            result = cursor.fetchone()
            
            if result:
                print(f"Cache hit! Using cached response")
                return json.loads(result['response_data'])
            return None
        except Exception as e:
            print(f"Error checking cache: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def save_to_cache(self, cache_key: str, response: Any) -> bool:
        """Save a response to the cache"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        try:
            # Convert response to JSON string
            response_json = json.dumps(response)
            
            # Insert or update the cache entry
            cursor.execute(
                """
                INSERT INTO response_cache (cache_key, response_data, timestamp) 
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    response_data = VALUES(response_data),
                    timestamp = VALUES(timestamp)
                """,
                (cache_key, response_json, datetime.now())
            )
            conn.commit()
            print(f"Response cached with key {cache_key}")
            return True
        except Exception as e:
            print(f"Error saving to cache: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()
            
    def migrate_file_cache_to_db(self, cache_dir="response_cache"):
        """Migrate existing file cache to database"""
        if not os.path.exists(cache_dir):
            print("No cache directory found, skipping migration")
            return
        
        print("Migrating file cache to database...")
        migrated = 0
        
        for filename in os.listdir(cache_dir):
            if filename.endswith('.json'):
                cache_key = filename.split('.')[0]  # Remove .json extension
                file_path = os.path.join(cache_dir, filename)
                
                try:
                    with open(file_path, 'r') as f:
                        cache_data = json.load(f)
                    
                    if 'response' in cache_data:
                        self.save_to_cache(cache_key, cache_data['response'])
                        migrated += 1
                except Exception as e:
                    print(f"Error migrating {filename}: {str(e)}")
        
        print(f"Migration complete. {migrated} cache entries migrated.")