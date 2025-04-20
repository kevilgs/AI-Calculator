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
import uuid
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and saved calculations."""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationship to SavedCalculation
    calculations = db.relationship('SavedCalculation', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash the password for secure storage."""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f'<User {self.username}>'

class SavedCalculation(db.Model):
    """Model to store user's saved calculations."""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    latex_input = db.Column(db.Text, nullable=False)
    operation_type = db.Column(db.String(20), nullable=False)  # 'solve', 'laplace', 'fourier', etc.
    solution = db.Column(db.Text)
    ai_explanation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    title = db.Column(db.String(100))  # Optional title for the calculation
    
    def to_dict(self):
        """Convert model to dictionary for API response."""
        return {
            'id': self.id,
            'title': self.title,
            'latex_input': self.latex_input,
            'operation_type': self.operation_type,
            'solution': self.solution,
            'ai_explanation': self.ai_explanation,
            'created_at': self.created_at.isoformat()
        }
        
    def __repr__(self):
        return f'<SavedCalculation {self.id}>'

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