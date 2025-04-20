"""
Routes Package

This package contains all route definitions for the calculator API.
"""
from flask import Blueprint
from flask_cors import CORS

# Create Blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import routes to register them with the blueprint
from routes.solve_routes import *
from routes.health_routes import *

def register_routes(app):
    """
    Register all blueprints with the Flask app
    
    Args:
        app: The Flask application instance
    """
    # Enable CORS for all routes
    CORS(app)
    
    # Register the API blueprint
    app.register_blueprint(api_bp)