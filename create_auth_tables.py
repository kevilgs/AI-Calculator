"""
Database migration script to add user authentication and saved calculations tables.

This script should be run once to create the necessary tables in your existing MySQL database.
"""
import sys
import os

# Add the parent directory to sys.path to import from the main application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from models.db_model import db, User, SavedCalculation
from config.settings import SQLALCHEMY_DATABASE_URI

def create_tables():
    """Create the User and SavedCalculation tables in the existing database."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database with the app
    db.init_app(app)
    
    with app.app_context():
        # Check if tables already exist
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if 'user' not in existing_tables and 'saved_calculation' not in existing_tables:
            print("Creating User and SavedCalculation tables...")
            
            # Create the tables
            db.create_all()
            
            print("Tables created successfully!")
        else:
            if 'user' in existing_tables:
                print("User table already exists.")
            if 'saved_calculation' in existing_tables:
                print("SavedCalculation table already exists.")
            
            # If only one table exists, create the other
            if 'user' in existing_tables and 'saved_calculation' not in existing_tables:
                print("Creating SavedCalculation table...")
                SavedCalculation.__table__.create(db.engine)
                print("SavedCalculation table created successfully!")
            elif 'saved_calculation' in existing_tables and 'user' not in existing_tables:
                print("Creating User table...")
                User.__table__.create(db.engine)
                print("User table created successfully!")

if __name__ == "__main__":
    create_tables()
    print("Database migration completed.")