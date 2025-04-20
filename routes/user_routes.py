"""
User Routes Module

This module defines the routes for user authentication and saved calculations.
"""
from flask import request, jsonify, current_app, g
from functools import wraps
import jwt
from datetime import datetime, timedelta
from routes import api_bp
from config.settings import SECRET_KEY

# JWT configuration
JWT_SECRET = SECRET_KEY  # Use the secret key from settings
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24  # hours

def token_required(f):
    """Decorator for routes that require authentication via JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in the Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({"success": False, "error": "Authentication token is missing"}), 401
            
        try:
            # Decode the token
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            # Store user data in flask g object for route handlers
            g.user_id = payload['user_id']
            g.username = payload['username']
            
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "error": "Authentication token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"success": False, "error": "Invalid authentication token"}), 401
            
        return f(*args, **kwargs)
    
    return decorated

@api_bp.route('/auth/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "Invalid request payload"}), 400
        
    # Extract registration data
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # Validate required fields
    if not username or not email or not password:
        return jsonify({"success": False, "error": "Missing required fields"}), 400
        
    # Get user service
    user_service = current_app.user_service
    
    # Register the user
    success, message, user = user_service.register_user(username, email, password)
    
    if not success:
        return jsonify({"success": False, "error": message}), 400
        
    # Return success response
    return jsonify({
        "success": True,
        "message": message,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 201

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """Authenticate a user and return JWT token."""
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "Invalid request payload"}), 400
        
    # Extract login data
    username = data.get('username')
    password = data.get('password')
    
    # Validate required fields
    if not username or not password:
        return jsonify({"success": False, "error": "Missing required fields"}), 400
        
    # Get user service
    user_service = current_app.user_service
    
    # Authenticate the user
    success, message, user = user_service.authenticate_user(username, password)
    
    if not success:
        return jsonify({"success": False, "error": message}), 401
        
    # Generate JWT token
    token_payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION)
    }
    
    token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    # Return success response with token
    return jsonify({
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 200

@api_bp.route('/calculations', methods=['GET'])
@token_required
def get_calculations():
    """Get all calculations for the authenticated user."""
    user_service = current_app.user_service
    
    # Get calculations for user
    calculations = user_service.get_user_calculations(g.user_id)
    
    return jsonify({
        "success": True,
        "calculations": calculations
    }), 200

@api_bp.route('/calculations/<calculation_id>', methods=['GET'])
@token_required
def get_calculation(calculation_id):
    """Get a specific calculation by ID."""
    user_service = current_app.user_service
    
    # Get calculation by ID
    calculation = user_service.get_calculation_by_id(calculation_id, g.user_id)
    
    if not calculation:
        return jsonify({"success": False, "error": "Calculation not found"}), 404
        
    return jsonify({
        "success": True,
        "calculation": calculation
    }), 200

@api_bp.route('/calculations', methods=['POST'])
@token_required
def save_calculation():
    """Save a calculation for the authenticated user."""
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "Invalid request payload"}), 400
        
    # Extract calculation data
    latex_input = data.get('latex_input')
    operation_type = data.get('operation_type')
    solution = data.get('solution')
    ai_explanation = data.get('ai_explanation')
    title = data.get('title')
    
    # Validate required fields
    if not latex_input or not operation_type or not solution:
        return jsonify({"success": False, "error": "Missing required fields"}), 400
        
    # Get user service
    user_service = current_app.user_service
    
    # Save the calculation
    success, message, calculation = user_service.save_calculation(
        g.user_id, latex_input, operation_type, solution, ai_explanation, title
    )
    
    if not success:
        return jsonify({"success": False, "error": message}), 400
        
    # Return success response
    return jsonify({
        "success": True,
        "message": message,
        "calculation": calculation.to_dict()
    }), 201

@api_bp.route('/calculations/<calculation_id>', methods=['DELETE'])
@token_required
def delete_calculation(calculation_id):
    """Delete a specific calculation."""
    user_service = current_app.user_service
    
    # Delete calculation
    success, message = user_service.delete_calculation(calculation_id, g.user_id)
    
    if not success:
        return jsonify({"success": False, "error": message}), 404
        
    return jsonify({
        "success": True,
        "message": message
    }), 200