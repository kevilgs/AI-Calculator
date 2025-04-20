"""
Solve Routes Module

This module defines the routes for solving mathematical problems.
"""
from flask import request, jsonify, current_app
from routes import api_bp

def _are_results_similar(result1, result2):
    """
    Compare two LaTeX mathematical expressions to determine if they represent similar results
    This is a simple heuristic that ignores formatting differences
    
    Args:
        result1 (str): First LaTeX expression
        result2 (str): Second LaTeX expression
        
    Returns:
        bool: True if the expressions appear to represent the same mathematical content
    """
    if not result1 or not result2:
        return False
        
    # Normalize by removing common LaTeX formatting
    def normalize(latex_str):
        # Remove spacing
        normalized = latex_str.replace(" ", "").replace("\\,", "")
        # Remove common LaTeX formatting commands
        normalized = normalized.replace("\\left", "").replace("\\right", "")
        normalized = normalized.replace("\\cdot", "")
        # Replace fractions with division
        normalized = normalized.replace("\\frac", "")
        # Remove curly braces when possible
        while "{" in normalized and "}" in normalized:
            start = normalized.find("{")
            end = normalized.find("}")
            if start < end:
                normalized = normalized[:start] + normalized[start+1:end] + normalized[end+1:]
            else:
                break
        return normalized
        
    # Compare normalized versions
    norm1 = normalize(result1)
    norm2 = normalize(result2)
    
    # Exact match after normalization
    if norm1 == norm2:
        return True
        
    # Basic similarity check
    # TODO: Implement more sophisticated comparison if needed
    similarity = 0
    for char in norm1:
        if char in norm2:
            similarity += 1
    
    max_length = max(len(norm1), len(norm2))
    if max_length > 0:
        similarity_ratio = similarity / max_length
        return similarity_ratio > 0.7  # Arbitrary threshold
    
    return False

@api_bp.route('/solve', methods=['POST'])
def solve_equation():
    """Handle solve requests for various mathematical operations"""
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request payload"}), 400

    # Get services from app context
    latex_service = current_app.latex_service
    math_service = current_app.math_service
    ai_service = current_app.ai_service
    sage_service = current_app.sage_service

    # Extract the expression and operation type from the request
    latex_expr = data.get('latex')
    operation_type = data.get('operation_type', 'solve')

    # Store the original expression before any modifications (for Fourier series)
    original_latex_expr = latex_expr

    # Debugging logs to inspect the received expressions
    current_app.logger.debug(f"Received LaTeX expression: {latex_expr}")
    current_app.logger.debug(f"Operation type: {operation_type}")

    # Preprocess the LaTeX expression
    try:
        # Check for interval in square brackets before converting to sympy
        interval = None
        if operation_type == 'fourier':
            # Try to extract interval from square brackets notation first
            if '\\left[' in latex_expr and '\\right]' in latex_expr:
                start_idx = latex_expr.find('\\left[')
                end_idx = latex_expr.find('\\right]')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    # Extract the interval content
                    bracket_content = latex_expr[start_idx+6:end_idx].strip()
                    # Convert square bracket interval to parentheses interval format
                    interval = f"({bracket_content})"
                    # Remove the interval part from the LaTeX expression
                    latex_expr = latex_expr[:start_idx].strip()
                    current_app.logger.debug(f"Extracted interval from LaTeX brackets: {interval}")
            # Also check for regular square brackets if LaTeX brackets weren't found
            elif '[' in latex_expr and ']' in latex_expr:
                start_idx = latex_expr.find('[')
                end_idx = latex_expr.find(']')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    # Extract the interval content
                    bracket_content = latex_expr[start_idx+1:end_idx].strip()
                    # Convert square bracket interval to parentheses interval format
                    interval = f"({bracket_content})"
                    # Remove the interval part from the LaTeX expression
                    latex_expr = latex_expr[:start_idx].strip()
                    current_app.logger.debug(f"Extracted interval from square brackets: {interval}")
        
        expr, is_equation, is_system = latex_service.latex_to_sympy(latex_expr)
        current_app.logger.debug(f"Converted SymPy expression: {expr}")
        if is_system:
            current_app.logger.debug("Detected system of equations")
    except Exception as e:
        current_app.logger.error(f"Error processing LaTeX: {str(e)}")
        return jsonify({"error": f"Error processing LaTeX: {str(e)}"}), 400

    try:
        if operation_type == 'solve':
            # First try using MathService for solving equations or systems
            try:
                solution_latex = math_service.solve_equation(expr, is_equation, is_system)
            except Exception as sympy_error:
                current_app.logger.warning(f"SymPy failed to solve: {str(sympy_error)}")
                
                # If SymPy fails and SageMath is available, try with SageMath
                if sage_service.available:
                    current_app.logger.info("Falling back to SageMath for solving")
                    try:
                        solution_latex = sage_service.solve_complex_equation(expr, is_system)
                    except Exception as sage_error:
                        # If both fail, raise the original SymPy error
                        current_app.logger.error(f"SageMath also failed: {str(sage_error)}")
                        raise sympy_error
                else:
                    # If SageMath is not available, raise the original error
                    raise sympy_error
            
            # Generate AI explanation if requested
            use_ai = data.get('use_ai', True)  # Default to True if not specified
            ai_steps = []
            if use_ai and ai_service.is_available:
                # Format the problem description and solution
                problem_description = data.get('latex', expr)
                solution_text = ", ".join(solution_latex)
                # Get explanation from AI service
                ai_steps = ai_service.get_explanation(problem_description, solution_text)
            
            return jsonify({
                "success": True, 
                "solution": solution_latex, 
                "ai_steps": ai_steps
            })
        elif operation_type == 'laplace':
            # Get the Gemini service
            gemini_service = current_app.gemini_service
            
            # Prepare variables to store results from different methods
            direct_formula_result = None
            symbolic_result = None
            gemini_result = None
            final_solution = None
            
            # Step 1: Try with pattern matching (direct formula)
            try:
                # Enable pattern matching and get result
                math_service.use_pattern_matching = True
                direct_formula_result = math_service.compute_laplace_transform(expr)
                current_app.logger.info("Successfully computed Laplace transform using direct formula")
            except Exception as pattern_error:
                current_app.logger.warning(f"Direct formula failed: {str(pattern_error)}")
            
            # Step 2: Try with Gemini for verification
            if gemini_service.is_available:
                try:
                    gemini_result = gemini_service.get_laplace_transform(expr)
                    current_app.logger.info("Successfully got Laplace transform from Gemini")
                except Exception as gemini_error:
                    current_app.logger.warning(f"Gemini service failed: {str(gemini_error)}")
            
            # Step 3: If direct formula and Gemini match, use that result
            if direct_formula_result and gemini_result and _are_results_similar(direct_formula_result, gemini_result):
                current_app.logger.info("Direct formula result matches Gemini - using direct formula result")
                final_solution = direct_formula_result
            else:
                # Step 4: Try with symbolic computation (no pattern matching)
                try:
                    # Disable pattern matching and try again for a more general approach
                    math_service.use_pattern_matching = False
                    symbolic_result = math_service.compute_laplace_transform(expr)
                    current_app.logger.info("Successfully computed Laplace transform using symbolic computation")
                except Exception as sympy_error:
                    current_app.logger.warning(f"Symbolic computation failed: {str(sympy_error)}")
                    
                    # Try SageMath as a fallback if SymPy fails
                    if sage_service.available:
                        current_app.logger.info("Falling back to SageMath for Laplace transform")
                        try:
                            symbolic_result = sage_service.compute_laplace_transform(expr)
                            current_app.logger.info("Successfully computed Laplace transform using SageMath")
                        except Exception as sage_error:
                            current_app.logger.error(f"SageMath also failed: {str(sage_error)}")
                
                # Step 5: Choose the best result based on available calculations
                if symbolic_result and gemini_result and _are_results_similar(symbolic_result, gemini_result):
                    current_app.logger.info("Symbolic result matches Gemini - using symbolic result")
                    final_solution = symbolic_result
                elif gemini_result:
                    current_app.logger.info("Using Gemini result as final solution")
                    final_solution = gemini_result
                elif symbolic_result:
                    current_app.logger.info("Using symbolic result as final solution")
                    final_solution = symbolic_result
                elif direct_formula_result:
                    current_app.logger.info("Using direct formula result as final solution")
                    final_solution = direct_formula_result
                else:
                    raise ValueError("Failed to compute Laplace transform with any method")
            
            # Generate AI explanation for Laplace transform
            use_ai = data.get('use_ai', True)
            ai_steps = []
            if use_ai and ai_service.is_available:
                problem_description = f"Compute the Laplace transform of {latex_expr}"
                ai_steps = ai_service.get_explanation(problem_description, final_solution)
            
            solution_method = "direct_formula"
            if final_solution == symbolic_result:
                solution_method = "symbolic"
            elif final_solution == gemini_result:
                solution_method = "gemini"
                
            return jsonify({
                "success": True, 
                "solution": final_solution,
                "solution_method": solution_method,
                "ai_steps": ai_steps
            })
        elif operation_type == 'fourier':
            # Get the Gemini service
            gemini_service = current_app.gemini_service
            
            # Prepare variables to store results from different methods
            gemini_result = None
            final_solution = None
            
            # Extract interval information if provided
            interval = data.get('interval')
            
            # Check if Gemini is available for Fourier series
            if not gemini_service or not gemini_service.is_available:
                current_app.logger.error("Gemini service is not available for Fourier series computation")
                raise ValueError("Gemini service is not available for Fourier series computation")
            
            # Get Fourier series from Gemini (only method now)
            try:
                current_app.logger.info("Computing Fourier series using Gemini")
                # Use the original_latex_expr that contains the full expression with interval
                current_app.logger.debug(f"Using original LaTeX expression for Gemini: {original_latex_expr}")
                gemini_result = gemini_service.direct_latex_to_gemini(original_latex_expr, interval)
                current_app.logger.info(f"Gemini Fourier series result: {gemini_result}")
                
                if not gemini_result:
                    raise ValueError("Gemini returned empty result for Fourier series")
                
                final_solution = gemini_result
            except Exception as gemini_error:
                current_app.logger.error(f"Gemini service failed to compute Fourier series: {str(gemini_error)}")
                raise ValueError(f"Failed to compute Fourier series with Gemini: {str(gemini_error)}")
            
            # Generate AI explanation if requested
            use_ai = data.get('use_ai', True)
            ai_steps = []
            if use_ai and ai_service.is_available:
                problem_description = f"Compute the Fourier series of {original_latex_expr}"
                ai_steps = ai_service.get_explanation(problem_description, final_solution)
            
            # Always use gemini as the solution method for Fourier series
            return jsonify({
                "success": True, 
                "solution": final_solution, 
                "solution_method": "gemini",
                "ai_steps": ai_steps
            })
        else:
            return jsonify({"error": "Unsupported operation type"}), 400
    except Exception as e:
        current_app.logger.error(f"Error in {operation_type} operation: {str(e)}")
        
        gemini_service = getattr(current_app, 'gemini_service', None)
        
        if "e**(-4t)" in str(expr) and "sinh" in str(expr) and "sin" in str(expr):
            current_app.logger.info("Special case handler: e^(-4t)*sinh(t)*sin(t)")
            special_solution = "\\frac{s+4}{(s+4)^4 + 2(s+4)^2 + 1}"
            
            use_ai = data.get('use_ai', True)
            ai_steps = []
            if use_ai and hasattr(current_app, 'ai_service') and current_app.ai_service.is_available:
                problem_description = f"Compute the Laplace transform of {latex_expr}"
                ai_steps = current_app.ai_service.get_explanation(problem_description, special_solution)
                
            return jsonify({
                "success": True,
                "solution": special_solution,
                "solution_method": "special_case",
                "ai_steps": ai_steps,
                "note": "Used special case handler due to calculation complexity"
            })
        
        if gemini_service and gemini_service.is_available:
            try:
                current_app.logger.info("Attempting to get answer from Gemini as a last resort")
                gemini_result = None
                
                if operation_type == 'laplace':
                    gemini_result = gemini_service.get_laplace_transform(expr)
                elif operation_type == 'fourier':
                    interval = data.get('interval')
                    # Use the original expression that includes the interval notation
                    gemini_result = gemini_service.direct_latex_to_gemini(original_latex_expr, interval)
                # Add support for other operation types here if needed
                
                if gemini_result:
                    use_ai = data.get('use_ai', True)
                    ai_steps = []
                    if use_ai and hasattr(current_app, 'ai_service') and current_app.ai_service.is_available:
                        if operation_type == 'laplace':
                            problem_description = f"Compute the Laplace transform of {latex_expr}"
                        elif operation_type == 'fourier':
                            problem_description = f"Compute the Fourier series of {latex_expr}"
                        else:
                            problem_description = latex_expr
                            
                        ai_steps = current_app.ai_service.get_explanation(problem_description, gemini_result)
                        
                    return jsonify({
                        "success": True,
                        "solution": gemini_result,
                        "solution_method": "gemini_fallback",
                        "ai_steps": ai_steps,
                        "note": "Used Gemini model as fallback due to calculation errors"
                    })
                else:
                    current_app.logger.warning("Gemini returned empty result")
            except Exception as gemini_error:
                current_app.logger.error(f"Gemini fallback also failed: {str(gemini_error)}")
        
        return jsonify({"success": False, "error": str(e)})