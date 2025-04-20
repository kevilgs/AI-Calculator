"""
Application Settings and Configuration

This module provides configuration settings for the AI Calculator application.
In a production environment, sensitive information should be loaded from
environment variables or secure vaults rather than being hardcoded.
"""
import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")

# API credentials
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "credentials.json")

# Cache settings
CACHE_DIR = os.path.join(BASE_DIR, "response_cache")
ENABLE_CACHING = True

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Change this to your MySQL username
    'password': '1234',  # Change this to your MySQL password
    'database': 'calculator_cache'
}

# SQLAlchemy database URI (using MySQL)
SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"

# Application secret key (for sessions and JWT)
SECRET_KEY = 'your-secret-key-here'  # Change this to a secure random string in production

# AI settings
GEMINI_MODEL = 'models/gemini-1.5-pro'

# Math settings
DEFAULT_OPERATION = 'solve'
MAX_FOURIER_TERMS = 5