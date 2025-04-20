"""
Health Routes Module

This module defines routes for health checks and system status.
"""
from flask import jsonify, current_app
from routes import api_bp

@api_bp.route('/health')
def health_check():
    """API health check endpoint"""
    # Get AI service to check its status
    ai_service = current_app.ai_service
    
    return jsonify({
        "status": "ok",
        "using_sympy": True,
        "gemini_available": ai_service.is_available,
        "token_usage": ai_service.token_usage
    })