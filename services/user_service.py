"""
User service module for handling user authentication and saved calculations.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from flask import current_app
from models.db_model import db, User, SavedCalculation

class UserService:
    """Service for handling user-related operations like authentication and saved calculations."""
    
    def __init__(self):
        """Initialize the user service."""
        self.logger = current_app.logger if current_app else None
    
    def register_user(self, username: str, email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Register a new user.
        
        Args:
            username: The username for the new user
            email: The email address for the new user
            password: The password for the new user
            
        Returns:
            Tuple containing (success, message, user)
        """
        try:
            # Check if username is already taken
            if User.query.filter_by(username=username).first():
                return False, "Username already exists", None
                
            # Check if email is already registered
            if User.query.filter_by(email=email).first():
                return False, "Email already registered", None
                
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            
            # Add to database
            db.session.add(user)
            db.session.commit()
            
            if self.logger:
                self.logger.info(f"New user registered: {username}")
                
            return True, "User registered successfully", user
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Error registering user: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
            return False, error_msg, None
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: The username to authenticate
            password: The password to check
            
        Returns:
            Tuple containing (success, message, user)
        """
        try:
            # Find user by username
            user = User.query.filter_by(username=username).first()
            
            # Check if user exists
            if not user:
                return False, "User not found", None
                
            # Check password
            if not user.check_password(password):
                return False, "Invalid password", None
                
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            if self.logger:
                self.logger.info(f"User authenticated: {username}")
                
            return True, "Authentication successful", user
            
        except Exception as e:
            error_msg = f"Error authenticating user: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
            return False, error_msg, None
    
    def save_calculation(self, user_id: str, latex_input: str, operation_type: str, 
                        solution: str, ai_explanation: str = None, title: str = None) -> Tuple[bool, str, Optional[SavedCalculation]]:
        """
        Save a calculation for a user.
        
        Args:
            user_id: The ID of the user
            latex_input: The LaTeX input for the calculation
            operation_type: The type of calculation ('solve', 'laplace', 'fourier', etc.)
            solution: The solution result
            ai_explanation: Optional AI-generated explanation
            title: Optional title for the calculation
            
        Returns:
            Tuple containing (success, message, saved_calculation)
        """
        try:
            # Create new saved calculation
            calculation = SavedCalculation(
                user_id=user_id,
                latex_input=latex_input,
                operation_type=operation_type,
                solution=solution,
                ai_explanation=ai_explanation,
                title=title or f"{operation_type.capitalize()} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # Add to database
            db.session.add(calculation)
            db.session.commit()
            
            if self.logger:
                self.logger.info(f"Calculation saved for user {user_id}")
                
            return True, "Calculation saved successfully", calculation
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Error saving calculation: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
            return False, error_msg, None
    
    def get_user_calculations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all calculations for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of calculation dictionaries
        """
        try:
            calculations = SavedCalculation.query.filter_by(user_id=user_id).order_by(SavedCalculation.created_at.desc()).all()
            return [calc.to_dict() for calc in calculations]
            
        except Exception as e:
            error_msg = f"Error retrieving calculations: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
            return []
    
    def get_calculation_by_id(self, calculation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific calculation by ID and verify it belongs to the user.
        
        Args:
            calculation_id: The ID of the calculation
            user_id: The ID of the user who should own the calculation
            
        Returns:
            Calculation dictionary or None if not found or not owned by user
        """
        try:
            calculation = SavedCalculation.query.filter_by(id=calculation_id, user_id=user_id).first()
            return calculation.to_dict() if calculation else None
            
        except Exception as e:
            error_msg = f"Error retrieving calculation: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
            return None
    
    def delete_calculation(self, calculation_id: str, user_id: str) -> Tuple[bool, str]:
        """
        Delete a specific calculation.
        
        Args:
            calculation_id: The ID of the calculation to delete
            user_id: The ID of the user who should own the calculation
            
        Returns:
            Tuple containing (success, message)
        """
        try:
            calculation = SavedCalculation.query.filter_by(id=calculation_id, user_id=user_id).first()
            
            if not calculation:
                return False, "Calculation not found or not owned by user"
                
            db.session.delete(calculation)
            db.session.commit()
            
            if self.logger:
                self.logger.info(f"Calculation {calculation_id} deleted for user {user_id}")
                
            return True, "Calculation deleted successfully"
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Error deleting calculation: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
            return False, error_msg