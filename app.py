"""
AI Calculator Application

This is the main entry point for the AI-powered calculator application.
It integrates LaTeX parsing, mathematical computation, and AI explanations.
"""
import os
import flask
from flask import Flask, render_template, send_from_directory, jsonify, redirect

# Import configuration
from config.settings import CACHE_DIR, SQLALCHEMY_DATABASE_URI, SECRET_KEY

# Import services
from services.latex_service import latex_to_sympy
from services.math_service import MathService
from services.ai_service import AIService
from services.cache_service import CacheService
from services.gemini_service import GeminiService
from services.user_service import UserService

# Import database models
from models.db_model import db

# Import routes
from routes import register_routes

def create_app():
    """Create and configure the Flask application"""
    # Initialize Flask app
    app = Flask(__name__, 
                static_folder='frontend',
                template_folder='frontend')
    
    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = SECRET_KEY
    
    # Initialize database
    db.init_app(app)
    
    # Setup logging
    if app.debug:
        app.logger.setLevel('DEBUG')
    
    # Initialize services
    initialize_services(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register routes
    register_routes(app)
    
    # Setup basic routes
    setup_basic_routes(app)
    
    return app

def initialize_services(app):
    """Initialize all services and attach them to the Flask app"""
    # Cache service
    cache_service = CacheService(CACHE_DIR)
    app.cache_service = cache_service
    
    # AI service - now only needs the cache service, credentials from config
    ai_service = AIService(cache_service)
    app.ai_service = ai_service
    
    # Math service - initialize with pattern matching enabled
    math_service = MathService(use_pattern_matching=True)
    app.math_service = math_service
    
    # LaTeX service - this is a module with functions, not a class
    app.latex_service = lambda: None  # Create a simple object
    app.latex_service.latex_to_sympy = latex_to_sympy
    
    # Gemini service - for verification of results using LLM
    gemini_service = GeminiService()
    app.gemini_service = gemini_service
    
    # User service - for authentication and saved calculations
    user_service = UserService()
    app.user_service = user_service
    
    # Log service availability
    if gemini_service.is_available:
        app.logger.info("Gemini service is available for result verification")
    else:
        app.logger.warning("Gemini service is not available - check Gemini API credentials in config/calculator-456910-4c150120dcc7.json")

def setup_basic_routes(app):
    """Setup basic routes that are not part of the API"""
    @app.route('/')
    def index() -> str:
        """Serve the main page, but redirect to auth if not logged in"""
        # Check for authentication cookie/session
        auth_token = flask.request.cookies.get('authToken')
        
        # If no auth token, redirect to auth page
        if not auth_token:
            return redirect('/auth')
            
        # Otherwise serve the main app
        return render_template('index.html')  # type: ignore

    @app.route('/login')
    def login() -> str:
        """Serve the login page"""
        return render_template('login.html')
        
    @app.route('/register')
    def register() -> str:
        """Serve the registration page"""
        return render_template('register.html')
        
    @app.route('/dashboard')
    def dashboard() -> str:
        """Serve the user dashboard page"""
        # Check for authentication cookie/session
        auth_token = flask.request.cookies.get('authToken')
        
        # If no auth token, redirect to auth page
        if not auth_token:
            return redirect('/auth')
            
        return render_template('dashboard.html')
        
    @app.route('/auth')
    def auth() -> str:
        """Serve the new combined auth page"""
        return render_template('auth.html')
        
    @app.route('/logout')
    def logout() -> str:
        """Handle logout and redirect to auth page"""
        response = redirect('/auth')
        response.delete_cookie('authToken')
        return response

    @app.route('/node_modules/<path:filename>')
    def serve_node_modules(filename) -> flask.Response:  # type: ignore
        """Serve node_modules files (needed for iink)"""
        node_modules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'node_modules')
        return send_from_directory(node_modules_path, filename)
        
    @app.route('/check-iink')
    def check_iink() -> flask.Response:  # type: ignore
        """Check if the iink library is properly installed"""
        node_modules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'node_modules')
        
        # Check for different possible iink library paths
        possible_paths = [
            os.path.join(node_modules_path, 'iink-ts', 'dist', 'iink.min.js'),
            os.path.join(node_modules_path, 'iink-js', 'dist', 'iink.min.js'),
            os.path.join(node_modules_path, '@myscript', 'iink-js', 'dist', 'iink.min.js'),
            os.path.join(node_modules_path, 'myscript-math-web', 'dist', 'myscript-math-web.min.js'),
            os.path.join(node_modules_path, 'myscript', 'dist', 'myscript.min.js')
        ]
        
        found_paths = []
        iink_dirs = []
        
        if os.path.exists(node_modules_path):
            # Check for library files
            for path in possible_paths:
                if os.path.exists(path):
                    relative_path = os.path.relpath(path, node_modules_path)
                    found_paths.append(relative_path)
            
            # If no libraries found, check for directories
            if not found_paths:
                iink_dirs = [d for d in os.listdir(node_modules_path) 
                           if 'iink' in d.lower() or 'myscript' in d.lower()]
        
        return jsonify({
            'found_libraries': found_paths,
            'node_modules_exists': os.path.exists(node_modules_path),
            'iink_related_dirs': iink_dirs
        })

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)