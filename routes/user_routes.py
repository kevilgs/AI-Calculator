"""
User Routes Module

This module defines the routes for user authentication and saved calculations.
"""
from flask import request, jsonify, current_app, g, send_file, make_response
from functools import wraps
import jwt
from datetime import datetime, timedelta
import os
import io
import tempfile
from routes import api_bp
from config.settings import SECRET_KEY

# For PDF Generation
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Add TeX rendering support
try:
    from matplotlib import mathtext
    from matplotlib.backends.backend_pdf import FigureCanvasPdf
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

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

def sanitize_html_tags(text):
    """
    Sanitize and balance HTML tags in text to ensure proper rendering.
    This fixes issues with incorrect tag nesting or mismatched tags.
    """
    # Remove any existing HTML tags first
    clean_text = text.replace('<b>', '**').replace('</b>', '**')
    clean_text = clean_text.replace('<i>', '*').replace('</i>', '*')
    clean_text = clean_text.replace('<em>', '*').replace('</em>', '*')
    clean_text = clean_text.replace('<strong>', '**').replace('</strong>', '**')
    
    # Now re-process with a better tag balancing approach
    result = ""
    bold_open = False
    italic_open = False
    
    # Re-process markdown-style formatting
    i = 0
    while i < len(clean_text):
        # Handle bold formatting
        if i < len(clean_text) - 1 and clean_text[i:i+2] == '**':
            if not bold_open:
                result += '<b>'
                bold_open = True
            else:
                result += '</b>'
                bold_open = False
            i += 2
        # Handle italic formatting
        elif clean_text[i] == '*':
            if not italic_open:
                result += '<i>'
                italic_open = True
            else:
                result += '</i>'
                italic_open = False
            i += 1
        else:
            result += clean_text[i]
            i += 1
    
    # Ensure all tags are closed
    if bold_open:
        result += '</b>'
    if italic_open:
        result += '</i>'
    
    return result

def cleanup_temp_files(canvas, doc):
    """Cleanup handler to remove temporary files after PDF generation."""
    try:
        # Look for Image objects that have temp filenames
        for item in doc.canv._object_stack:
            if hasattr(item, '_temp_filename') and getattr(item, '_temp_filename', None):
                try:
                    if os.path.exists(item._temp_filename):
                        os.unlink(item._temp_filename)
                except Exception as e:
                    print(f"Error cleaning up temp file: {e}")
    except Exception as e:
        print(f"Error in cleanup: {e}")

@api_bp.route('/calculations/<calculation_id>/pdf', methods=['GET'])
@token_required
def generate_calculation_pdf(calculation_id):
    """Generate a PDF for a specific calculation."""
    user_service = current_app.user_service
    
    # Get calculation by ID
    calculation = user_service.get_calculation_by_id(calculation_id, g.user_id)
    
    if not calculation:
        return jsonify({"success": False, "error": "Calculation not found"}), 404
    
    # Prepare the calculation data
    title = calculation.get('title') or f"{calculation.get('operation_type', '').capitalize()} Problem"
    problem = calculation.get('latex_input', '')
    solution = calculation.get('solution', '')
    explanation = calculation.get('ai_explanation', '')
    created_at = calculation.get('created_at', '')
    
    # Format date if available
    formatted_date = ""
    if created_at:
        try:
            # Parse ISO date format
            date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
        except (ValueError, TypeError):
            formatted_date = str(created_at)
    
    # Generate a PDF with proper LaTeX rendering
    buffer = io.BytesIO()
    
    # Set up the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=title,
        author="MathSolver AI",
        subject="Mathematical Calculation",
        topMargin=36,
        bottomMargin=36,
        leftMargin=50,
        rightMargin=50
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Add custom styles - use unique names to avoid conflicts
    custom_title_style = ParagraphStyle(
        name='CustomTitle',
        parent=styles['Title'],
        textColor=colors.HexColor("#6200ea"),
        spaceAfter=6,
        fontSize=18
    )
    
    date_style = ParagraphStyle(
        name='DateStyle',
        parent=styles['Normal'],
        textColor=colors.HexColor("#6b6b80"),
        fontSize=9,
        alignment=1,  # Center alignment
        spaceAfter=10
    )
    
    section_title_style = ParagraphStyle(
        name='SectionTitleStyle',
        parent=styles['Heading2'],
        textColor=colors.HexColor("#6200ea"),
        fontSize=14,
        spaceBefore=16,
        spaceAfter=8
    )
    
    normal_text_style = ParagraphStyle(
        name='NormalTextStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        spaceAfter=12
    )
    
    footer_style = ParagraphStyle(
        name='FooterStyle',
        parent=styles['Normal'],
        textColor=colors.HexColor("#6b6b80"),
        fontSize=9,
        alignment=1  # Center alignment
    )
    
    # Create direct text rendering for LaTeX when matplotlib fails
    plain_problem = None
    plain_solution = None
    
    if not MATPLOTLIB_AVAILABLE:
        plain_problem = Paragraph(f"<pre>{problem}</pre>", ParagraphStyle('PlainProblem', 
                                 parent=styles['Normal'], fontName='Courier', fontSize=12))
        plain_solution = Paragraph(f"<pre>{solution}</pre>", ParagraphStyle('PlainSolution', 
                                  parent=styles['Normal'], fontName='Courier', fontSize=12))
    
    # Create content for the PDF
    content = []
    
    # Title
    content.append(Paragraph(title, custom_title_style))
    
    # Date
    if formatted_date:
        content.append(Paragraph(formatted_date, date_style))
    
    # Divider
    content.append(HRFlowable(
        width="100%",
        thickness=1,
        color=colors.HexColor("#e0e0f5"),
        spaceBefore=0,
        spaceAfter=15
    ))
    
    # Problem section
    content.append(Paragraph("Problem", section_title_style))
    
    # Render the problem LaTeX
    if MATPLOTLIB_AVAILABLE and problem:
        problem_img = render_latex(problem)
        if problem_img:
            content.append(problem_img)
        else:
            content.append(Paragraph(f"<pre>{problem}</pre>", 
                         ParagraphStyle('FallbackProblem', parent=styles['Normal'], 
                                        fontName='Courier', fontSize=12)))
    elif plain_problem:
        content.append(plain_problem)
    else:
        content.append(Paragraph(f"<pre>{problem}</pre>", 
                       ParagraphStyle('BasicProblem', parent=styles['Normal'], 
                                      fontName='Courier', fontSize=12)))
    
    content.append(Spacer(1, 15))
    
    # Solution section
    content.append(Paragraph("Solution", section_title_style))
    
    # Render the solution LaTeX
    if MATPLOTLIB_AVAILABLE and solution:
        solution_img = render_latex(solution)
        if solution_img:
            content.append(solution_img)
        else:
            content.append(Paragraph(f"<pre>{solution}</pre>", 
                         ParagraphStyle('FallbackSolution', parent=styles['Normal'], 
                                        fontName='Courier', fontSize=12)))
    elif plain_solution:
        content.append(plain_solution)
    else:
        content.append(Paragraph(f"<pre>{solution}</pre>", 
                       ParagraphStyle('BasicSolution', parent=styles['Normal'], 
                                      fontName='Courier', fontSize=12)))
    
    content.append(Spacer(1, 15))
    
    # Explanation section (if available)
    if explanation:
        content.append(Paragraph("Explanation", section_title_style))
        
        try:
            # Try a simpler sanitization approach - remove all tags and re-add only balanced ones
            all_text = explanation.replace('<b>', ' ').replace('</b>', ' ')
            all_text = all_text.replace('<i>', ' ').replace('</i>', ' ')
            all_text = all_text.replace('<em>', ' ').replace('</em>', ' ')
            all_text = all_text.replace('<strong>', ' ').replace('</strong>', ' ')
            all_text = all_text.replace('*', ' ')
            
            # Add the plain text explanation
            content.append(Paragraph(all_text, normal_text_style))
        except Exception as e:
            print(f"Error rendering explanation: {e}")
            # Ultra-safe fallback - completely plain text
            plain_explanation = ''.join(c for c in explanation if c.isprintable() and c != '<' and c != '>')
            content.append(Paragraph(plain_explanation, normal_text_style))
    
    # Footer
    content.append(Spacer(1, 20))
    content.append(HRFlowable(
        width="100%",
        thickness=1,
        color=colors.HexColor("#e0e0f5"),
        spaceBefore=0,
        spaceAfter=10
    ))
    content.append(Paragraph("Generated by MathSolver AI", footer_style))
    
    # Build the PDF with the cleanup function
    doc.build(content, onFirstPage=cleanup_temp_files, onLaterPages=cleanup_temp_files)
    
    # Clean up any leftover temporary files from rendering
    tmp_dir = tempfile.gettempdir()
    try:
        for filename in os.listdir(tmp_dir):
            if filename.startswith('tmp') and filename.endswith('.png'):
                filepath = os.path.join(tmp_dir, filename)
                if os.path.isfile(filepath):
                    try:
                        os.unlink(filepath)
                    except:
                        pass
    except:
        # Just ignore any errors in cleanup
        pass
    
    # Set up the response
    buffer.seek(0)
    
    # Generate a clean filename from the title
    filename = title.replace(' ', '_').replace('/', '_').lower() + ".pdf"
    
    response = make_response(send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    ))
    
    return response

def render_latex(latex_string):
    """Render LaTeX using matplotlib and return a ReportLab drawable."""
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    try:
        # Create a figure with transparent background
        fig = Figure(figsize=(7, 1.5), dpi=150, facecolor='white')
        
        # Add axes for the text (with no border)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        
        # Add the LaTeX text
        ax.text(0.5, 0.5, f"${latex_string}$", 
                fontsize=14, 
                ha='center', 
                va='center',
                transform=ax.transAxes)
        
        # Instead of using ImageReader, create a temporary file but handle it properly
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        # Save the figure to the temp file
        fig.savefig(temp_filename, format='png', dpi=150, bbox_inches='tight')
        
        # Create a ReportLab Image from the file path
        from reportlab.platypus import Image
        img = Image(temp_filename, width=400, height=100)
        
        # Set up cleanup of the temp file after it's been read by ReportLab
        # We need to delay the cleanup until after PDF generation
        img._temp_filename = temp_filename  # Store filename for cleanup later
        
        return img
    except Exception as e:
        print(f"Error rendering LaTeX: {e}")
        # Fallback to text rendering
        from reportlab.platypus import Paragraph
        fallback_style = ParagraphStyle(
            name='LatexFallbackStyle',
            parent=getSampleStyleSheet()['Normal'],
            fontName='Courier',
            fontSize=12,
            leading=14
        )
        return Paragraph(f"<pre>{latex_string}</pre>", fallback_style)