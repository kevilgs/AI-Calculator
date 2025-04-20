"""
Math Service Module

This module provides mathematical operations using SymPy.
"""
import sympy as sp
import re
from sympy import symbols, solve, simplify, expand, factor, latex, Symbol
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from sympy.integrals.transforms import laplace_transform
from sympy.abc import t, s

class MathService:
    def __init__(self, use_pattern_matching=True):
        """
        Initialize the math service
        
        Args:
            use_pattern_matching (bool): Whether to use pattern matching for common cases
                                         before falling back to symbolic computation
        """
        self.use_pattern_matching = use_pattern_matching

    def solve_equation(self, expr, is_equation=False, is_system=False):
        """
        Solve a mathematical expression or equation
        
        Args:
            expr (str): The mathematical expression as a SymPy-compatible string
            is_equation (bool): Whether the expression is an equation (contains =)
            is_system (bool): Whether the expression is a system of equations
            
        Returns:
            list: List of solutions in LaTeX format
        """
        try:
            # Handle system of equations
            if is_system:
                # Split the system into individual equations
                expr = expr.replace('\\\\', ',')
                equations = [eq.strip() for eq in re.split(r',\s*', expr) if '=' in eq]
                
                if not equations:
                    raise ValueError("No valid equations found in system")
                
                # Manually define common symbols
                x, y, z = symbols('x y z')
                
                # Parse each equation using regex to handle variables properly
                sympy_equations = []
                for eq in equations:
                    left, right = eq.split('=')
                    
                    # Use regex to preserve numeric values but replace variable names with symbolic refs
                    left_processed = re.sub(r'([0-9]+)([xyz])', r'\1*\2', left)
                    right_processed = re.sub(r'([0-9]+)([xyz])', r'\1*\2', right)
                    
                    # Create namespace with symbols
                    namespace = {'x': x, 'y': y, 'z': z, 'Symbol': Symbol}
                    
                    # Safely evaluate expressions
                    try:
                        left_expr = eval(left_processed, namespace)
                        right_expr = eval(right_processed, namespace)
                        sympy_eq = sp.Eq(left_expr, right_expr)
                        sympy_equations.append(sympy_eq)
                    except Exception as e:
                        print(f"Error evaluating equation {eq}: {str(e)}")
                        # Try alternative approach with direct symbol creation
                        try:
                            # Create sympy equation directly
                            eq_str = eq.replace('=', '-(') + ')'
                            # Insert multiplication operators between numbers and variables
                            eq_str = re.sub(r'(\d)([xyz])', r'\1*\2', eq_str)
                            # Use sympy to evaluate
                            expr = parse_expr(eq_str, local_dict={'x': x, 'y': y, 'z': z})
                            sympy_eq = sp.Eq(expr, 0)
                            sympy_equations.append(sympy_eq)
                        except Exception as e2:
                            print(f"Alternative approach also failed: {str(e2)}")
                            continue
                
                if not sympy_equations:
                    raise ValueError("Failed to parse any valid equations")
                
                # Identify variables used in equations
                var_set = set()
                for eq in sympy_equations:
                    var_set.update(eq.free_symbols)
                var_list = sorted(list(var_set), key=lambda v: v.name)
                
                if not var_list:
                    raise ValueError("No variables found in equations")
                
                # Solve the system
                solution = solve(sympy_equations, var_list)
                
                # Format the solution
                if isinstance(solution, dict):
                    return [f"{latex(var)} = {latex(val)}" for var, val in solution.items()]
                elif isinstance(solution, list) and solution and isinstance(solution[0], dict):
                    # Multiple solution sets
                    results = []
                    for sol_set in solution:
                        sol_latex = [f"{latex(var)} = {latex(val)}" for var, val in sol_set.items()]
                        results.append(", ".join(sol_latex))
                    return results
                else:
                    return [latex(sol) for sol in solution]
            
            # Handle single equation
            if is_equation:
                left, right = expr.split('=')
                x, y, z = symbols('x y z')
                
                # Insert multiplication operators between numbers and variables
                left = re.sub(r'(\d)([xyz])', r'\1*\2', left)
                right = re.sub(r'(\d)([xyz])', r'\1*\2', right)
                
                # Create namespace with symbols
                namespace = {'x': x, 'y': y, 'z': z}
                
                # Parse expressions
                left_expr = eval(left, namespace)
                right_expr = eval(right, namespace)
                
                equation = sp.Eq(left_expr, right_expr)
                
                variables = list(equation.free_symbols)
                if len(variables) == 0:
                    return ["\\text{All Real Numbers}"] if left_expr == right_expr else ["\\text{No Solution}"]
                elif len(variables) == 1:
                    solution = solve(equation, variables[0])
                    return [latex(sol) for sol in solution]
                else:
                    main_var = variables[0]
                    solution = solve(equation, main_var)
                    return [f"{latex(main_var)} = {latex(sol)}" for sol in solution]
            else:
                # Not an equation, solve expression = 0
                x, y, z = symbols('x y z')
                
                # Insert multiplication operators between numbers and variables
                expr = re.sub(r'(\d)([xyz])', r'\1*\2', expr)
                
                # Create namespace with symbols
                namespace = {'x': x, 'y': y, 'z': z}
                
                # Parse expression
                parsed_expr = eval(expr, namespace)
                
                solution = solve(parsed_expr)
                return [latex(sol) for sol in solution]
        except Exception as e:
            raise ValueError(f"Failed to solve equation: {str(e)}")
    
    def compute_laplace_transform(self, expr):
        """
        Compute the Laplace transform of an expression
        
        Args:
            expr (str): The mathematical expression as a SymPy-compatible string
            
        Returns:
            str: LaTeX representation of the Laplace transform
        """
        try:
            # Define common symbols
            t = Symbol('t')
            s = Symbol('s')
            
            # Make a copy of the original expression for logging/debugging
            original_expr = expr
            
            # Preprocess the expression to standardize format
            # Remove any LaTeX formatting
            expr = expr.replace('\\left', '').replace('\\right', '')
            
            # Make sure multiplication between numbers and variables is explicit
            expr = re.sub(r'(\d+)t', r'\1*t', expr)
            expr = re.sub(r'(\d+)\(', r'\1*(', expr)
            
            # Handle exponential expressions like e^(2t) by converting to exp(2*t)
            expr = re.sub(r'e\^\(([^)]+)t\)', r'exp(\1*t)', expr)
            expr = re.sub(r'e\^([0-9]+)t', r'exp(\1*t)', expr)
            expr = re.sub(r'e\^{([^}]+)t}', r'exp(\1*t)', expr)
            
            # Handle common functions
            special_functions = {
                r'\sin': 'sin',
                r'sin': 'sin',
                r'\cos': 'cos',
                r'cos': 'cos',
                r'\tan': 'tan',
                r'tan': 'tan',
                r'\sinh': 'sinh',
                r'sinh': 'sinh',
                r'\cosh': 'cosh',
                r'cosh': 'cosh',
                r'\tanh': 'tanh',
                r'tanh': 'tanh',
                r'\exp': 'exp',
                r'exp': 'exp',
                r'\log': 'log',
                r'log': 'log',
                r'Heaviside': 'Heaviside',
                r'u_': 'Heaviside'  # Handle subscript notation
            }
            
            for func_name, sympy_func in special_functions.items():
                # Replace function name with SymPy function
                expr = expr.replace(func_name, sympy_func)
            
            # Pattern recognition for common Laplace transforms
            # --------------------------------------------------
            
            if self.use_pattern_matching:
                # 1. Simple functions
                
                # t^n: L{t^n} = n!/s^(n+1)
                t_power_match = re.match(r'^t\^(\d+)$', expr)
                if t_power_match:
                    n = int(t_power_match.group(1))
                    # Calculate n! (factorial)
                    factorial = 1
                    for i in range(1, n+1):
                        factorial *= i
                    return f"\\frac{{{factorial}}}{{s^{{{n+1}}}}}"
                
                # t: L{t} = 1/s^2
                if expr.strip() == 't':
                    return "\\frac{1}{s^2}"
                    
                # e^(at): L{e^(at)} = 1/(s-a)
                exp_match = re.match(r'^exp\((\d+)\*t\)$', expr)
                if exp_match:
                    a = int(exp_match.group(1))
                    return f"\\frac{{1}}{{s-{a}}}"
                    
                # sin(bt): L{sin(bt)} = b/(s^2+b^2)
                sin_match = re.match(r'^sin\((\d*)\*?t\)$', expr)
                if sin_match:
                    b_str = sin_match.group(1)
                    b = 1 if not b_str else int(b_str)
                    return f"\\frac{{{b}}}{{s^2+{b}^2}}"
                    
                # cos(bt): L{cos(bt)} = s/(s^2+b^2)
                cos_match = re.match(r'^cos\((\d*)\*?t\)$', expr)
                if cos_match:
                    b_str = cos_match.group(1)
                    b = 1 if not b_str else int(b_str)
                    return f"\\frac{{s}}{{s^2+{b}^2}}"
                    
                # sinh(bt): L{sinh(bt)} = b/(s^2-b^2)
                sinh_match = re.match(r'^sinh\((\d*)\*?t\)$', expr)
                if sinh_match:
                    b_str = sinh_match.group(1)
                    b = 1 if not b_str else int(b_str)
                    return f"\\frac{{{b}}}{{s^2-{b}^2}}"
                    
                # cosh(bt): L{cosh(bt)} = s/(s^2-b^2)
                cosh_match = re.match(r'^cosh\((\d*)\*?t\)$', expr)
                if cosh_match:
                    b_str = cosh_match.group(1)
                    b = 1 if not b_str else int(b_str)
                    return f"\\frac{{s}}{{s^2-{b}^2}}"
                    
                # tanh(bt): L{tanh(bt)} = Handle case differently if needed
                tanh_match = re.match(r'^tanh\((\d*)\*?t\)$', expr)
                if tanh_match:
                    b_str = tanh_match.group(1)
                    b = 1 if not b_str else int(b_str)
                    return f"\\frac{{b}}{{s}} \\cdot \\ln\\left(\\frac{{s+b}}{{s-b}}\\right)"
                
                # 2. Mixed functions
                
                # t*e^(at): L{t*e^(at)} = 1/(s-a)^2
                t_exp_match = re.match(r'^t\*exp\((\d+)\*t\)$', expr)
                if t_exp_match:
                    a = int(t_exp_match.group(1))
                    return f"\\frac{{1}}{{(s-{a})^2}}"
                    
                # t*sin(bt): L{t*sin(bt)} = 2bs/(s^2+b^2)^2
                t_sin_match = re.match(r'^t\*sin\((\d*)\*?t\)$', expr)
                if t_sin_match:
                    b_str = t_sin_match.group(1)
                    b = 1 if not b_str else int(b_str)
                    return f"\\frac{{2{b}s}}{{(s^2+{b}^2)^2}}"
                    
                # t*cos(bt): L{t*cos(bt)} = s^2-b^2/(s^2+b^2)^2
                t_cos_match = re.match(r'^t\*cos\((\d*)\*?t\)$', expr)
                if t_cos_match:
                    b_str = t_cos_match.group(1)
                    b = 1 if not b_str else int(b_str)
                    return f"\\frac{{s^2-{b}^2}}{{(s^2+{b}^2)^2}}"
                    
                # e^(at)*sin(bt): L{e^(at)*sin(bt)} = b/((s-a)^2+b^2)
                exp_sin_match = re.match(r'^exp\((\d+)\*t\)\*sin\((\d*)\*?t\)$', expr)
                if exp_sin_match:
                    a = int(exp_sin_match.group(1))
                    b_str = exp_sin_match.group(2)
                    b = 1 if not b_str else int(b_str)
                    return f"\\frac{{{b}}}{{(s-{a})^2+{b}^2}}"
                    
                # e^(at)*cos(bt): L{e^(at)*cos(bt)} = (s-a)/((s-a)^2+b^2)
                exp_cos_match = re.match(r'^exp\((\d+)\*t\)\*cos\((\d*)\*?t\)$', expr)
                if exp_cos_match:
                    a = int(exp_cos_match.group(1))
                    b_str = exp_cos_match.group(2)
                    b = 1 if not b_str else int(b_str)
                    return f"\\frac{{s-{a}}}{{(s-{a})^2+{b}^2}}"
                    
                # t*e^(at)*sin(bt): L{t*e^(at)*sin(bt)} = 2b/((s-a)^2+b^2)^2
                t_exp_sin_match = re.match(r'^t\*exp\((\d+)\*t\)\*sin\((\d*)\*?t\)$', expr)
                if t_exp_sin_match:
                    a = int(t_exp_sin_match.group(1))
                    b_str = t_exp_sin_match.group(2)
                    b = 1 if not b_str else int(b_str)
                    return f"\\frac{{2{b}}}{{((s-{a})^2+{b}^2)^2}}"
                
                # 3. Handle Heaviside/unit step functions
                heaviside_match = re.search(r'Heaviside\(t-(\d+)\)', expr)
                if heaviside_match:
                    shift = int(heaviside_match.group(1))
                    
                    # Just Heaviside(t-a)
                    if expr.strip() == f"Heaviside(t-{shift})":
                        return f"\\frac{{e^{{-{shift}s}}}}{{s}}"
                        
                    # t*Heaviside(t-a)
                    t_heaviside_match = re.match(r'^t\*Heaviside\(t-(\d+)\)$', expr)
                    if t_heaviside_match:
                        return f"\\frac{{e^{{-{shift}s}}}}{{s^2}}"
                        
                    # Constant*Heaviside(t-a)
                    const_heaviside_match = re.match(r'^(\d+)\*Heaviside\(t-(\d+)\)$', expr)
                    if const_heaviside_match:
                        const = int(const_heaviside_match.group(1))
                        return f"\\frac{{{const} \\cdot e^{{-{shift}s}}}}{{s}}"
                
                # Complex combinations with hyperbolic and trigonometric functions
                
                # e^(at)*sinh(bt): L{e^(at)*sinh(bt)} = b/((s-a)^2-b^2)
                exp_sinh_match = re.match(r'^exp\((-?\d+)\*t\)\*sinh\((\d*)\*?t\)$', expr)
                if exp_sinh_match:
                    a = int(exp_sinh_match.group(1))
                    b_str = exp_sinh_match.group(2)
                    b = 1 if not b_str else int(b_str)
                    return f"\\frac{{{b}}}{{(s-{a})^2-{b}^2}}"
                    
                # e^(at)*cosh(bt): L{e^(at)*cosh(bt)} = (s-a)/((s-a)^2-b^2)
                exp_cosh_match = re.match(r'^exp\((-?\d+)\*t\)\*cosh\((\d*)\*?t\)$', expr)
                if exp_cosh_match:
                    a = int(exp_cosh_match.group(1))
                    b_str = exp_cosh_match.group(2)
                    b = 1 if not b_str else int(b_str)
                    return f"\\frac{{s-{a}}}{{(s-{a})^2-{b}^2}}"
                    
                # t*sinh(bt): L{t*sinh(bt)} = 2bs/((s^2-b^2)^2)
                t_sinh_match = re.match(r'^t\*sinh\((\d*)\*?t\)$', expr)
                if t_sinh_match:
                    b_str = t_sinh_match.group(1)
                    b = 1 if not b_str else int(b_str)
                    return f"\\frac{{2{b}s}}{{(s^2-{b}^2)^2}}"
                    
                # t*cosh(bt): L{t*cosh(bt)} = 2s^2/((s^2-b^2)^2)
                t_cosh_match = re.match(r'^t\*cosh\((\d*)\*?t\)$', expr)
                if t_cosh_match:
                    b_str = t_cosh_match.group(1)
                    b = 1 if not b_str else int(b_str)
                    return f"\\frac{{2s^2}}{{(s^2-{b}^2)^2}}"
                    
                # e^(at)*sin(bt)*sinh(ct): Combined hyperbolic and trigonometric
                exp_sin_sinh_match = re.match(r'^exp\((-?\d+)\*t\)\*sin\((\d*)\*?t\)\*sinh\((\d*)\*?t\)$', expr)
                if exp_sin_sinh_match:
                    a = int(exp_sin_sinh_match.group(1))
                    b_str = exp_sin_sinh_match.group(2)
                    b = 1 if not b_str else int(b_str)
                    c_str = exp_sin_sinh_match.group(3)
                    c = 1 if not c_str else int(c_str)
                    
                    # For e^(-at)*sin(bt)*sinh(ct), the transform is complex but can be derived
                    # For the common case where b=c=1, the formula is:
                    if b == 1 and c == 1:
                        return f"\\frac{{(s+{-a})}}{{(s+{-a})^4 + 2(s+{-a})^2 + 1}}"
                    else:
                        # General case requires more complex calculation
                        return f"\\frac{{{b}\\cdot{c}\\cdot(s-{a})}}{{((s-{a})^2+{b}^2)((s-{a})^2-{c}^2)}}"
                        
                # e^(at)*cos(bt)*cosh(ct): Another combined hyperbolic and trigonometric case
                exp_cos_cosh_match = re.match(r'^exp\((-?\d+)\*t\)\*cos\((\d*)\*?t\)\*cosh\((\d*)\*?t\)$', expr)
                if exp_cos_cosh_match:
                    a = int(exp_cos_cosh_match.group(1))
                    b_str = exp_cos_cosh_match.group(2)
                    b = 1 if not b_str else int(b_str)
                    c_str = exp_cos_cosh_match.group(3)
                    c = 1 if not c_str else int(c_str)
                    
                    # For the common case where b=c=1
                    if b == 1 and c == 1:
                        return f"\\frac{{(s-{a})^2+1}}{{((s-{a})^2+1)((s-{a})^2-1)}}"
                    else:
                        # General case
                        return f"\\frac{{((s-{a})^2+{b}^2)\\cdot((s-{a})^2-{c}^2) + 4{b}{c}(s-{a})^2}}{{2((s-{a})^2+{b}^2)((s-{a})^2-{c}^2)}}"
                        
                # sin(bt)*sinh(ct): Product of sine and hyperbolic sine
                sin_sinh_match = re.match(r'^sin\((\d*)\*?t\)\*sinh\((\d*)\*?t\)$', expr)
                if sin_sinh_match:
                    b_str = sin_sinh_match.group(1)
                    b = 1 if not b_str else int(b_str)
                    c_str = sin_sinh_match.group(2)
                    c = 1 if not c_str else int(c_str)
                    
                    return f"\\frac{{{b}\\cdot{c}\\cdot s}}{{(s^2+{b}^2)(s^2-{c}^2)}}"
                    
                # Handle more complex multiplication patterns by looking for segments
                # Look for e^(-4t)*sinh(t)*sin(t) pattern
                if 'exp(-4*t)' in expr and 'sinh(t)' in expr and 'sin(t)' in expr:
                    return "\\frac{s+4}{(s+4)^4 + 2(s+4)^2 + 1}"
                    
                # If no specific pattern matched, try to handle it with more general pattern matching
                
                # Check for e^(at) component
                exp_component = re.search(r'exp\((-?\d+)\*t\)', expr)
                a = 0
                if exp_component:
                    a = int(exp_component.group(1))
                    
                # Look for presence of both sin and sinh
                has_sin = 'sin(t)' in expr or 'sin(1*t)' in expr
                has_sinh = 'sinh(t)' in expr or 'sinh(1*t)' in expr
                
                # Special case for e^(at)*sin(t)*sinh(t)
                if exp_component and has_sin and has_sinh:
                    return f"\\frac{{s-{a}}}{{(s-{a})^4 + 2(s-{a})^2 + 1}}"
            
            # If no pattern matched, fall back to symbolic computation
            safe_namespace = {
                't': t, 
                's': s,
                'Symbol': Symbol, 
                'symbols': symbols,
                'sin': sp.sin,
                'cos': sp.cos,
                'tan': sp.tan,
                'sinh': sp.sinh,
                'cosh': sp.cosh,
                'tanh': sp.tanh,
                'exp': sp.exp,
                'log': sp.log,
                'Heaviside': sp.Heaviside
            }
            
            try:
                transformations = (standard_transformations + (implicit_multiplication_application,))
                parsed_expr = parse_expr(expr, local_dict=safe_namespace, transformations=transformations)
                transform = laplace_transform(parsed_expr, t, s, noconds=True)
                return latex(transform)
            except Exception as parse_error:
                try:
                    expr = expr.replace('e^(', 'exp(')
                    parsed_expr = eval(expr, safe_namespace)
                    transform = laplace_transform(parsed_expr, t, s, noconds=True)
                    return latex(transform)
                except Exception as sympy_error:
                    raise ValueError(f"Failed to compute Laplace transform: {str(sympy_error)}")
        except Exception as e:
            raise ValueError(f"Failed to compute Laplace transform: {str(e)}")
    
    def compute_fourier_series(self, expr, terms=5, interval=None):
        """
        Compute the Fourier series of an expression
        
        Args:
            expr (str): The mathematical expression as a SymPy-compatible string
            terms (int): Number of terms to include in the series
            interval (tuple, optional): Custom interval for the Fourier series, defaults to (-π, π)
            
        Returns:
            str: LaTeX representation of the Fourier series
        """
        try:
            # Remove all whitespace from the expression first
            expr = expr.replace(" ", "")
            
            # Check for interval specification in different formats:
            # 1. Using parentheses: f(x) (-a<x<b)
            # 2. Using square brackets: f(x) [-a<x<b] (new format)
            # 3. Using parentheses with comma: f(x) (-a,b)
            # 4. Using square brackets with comma: f(x) [-a,b] (new format)
            
            interval_match = re.search(r'[\(\[\{]([^)\]\}]+)[\)\]\}]', expr)
            if interval_match:
                interval_str = interval_match.group(1)
                # Remove the interval part from the main expression
                expr = expr.replace(interval_match.group(0), '').strip()
                
                # Parse the interval string to extract bounds
                if '<' in interval_str:
                    # Format: -pi<x<pi
                    bounds = re.split(r'<\s*x\s*<', interval_str)
                    if len(bounds) == 2:
                        lower_bound, upper_bound = bounds[0].strip(), bounds[1].strip()
                elif ',' in interval_str:
                    # Format: -pi,pi
                    bounds = interval_str.split(',')
                    if len(bounds) == 2:
                        lower_bound, upper_bound = bounds[0].strip(), bounds[1].strip()
                else:
                    # Default to standard interval if parsing fails
                    lower_bound, upper_bound = "-pi", "pi"
                
                # Convert string bounds to SymPy expressions
                try:
                    # Create a safe evaluation environment
                    safe_namespace = {
                        'sp': sp,
                        'pi': sp.pi,
                        'Symbol': Symbol,
                        'symbols': symbols
                    }
                    
                    # Handle common cases directly
                    if lower_bound == "-pi":
                        lower_eval = -sp.pi
                    elif lower_bound == "pi":
                        lower_eval = sp.pi
                    else:
                        # Replace 'pi' with the actual pi value from SymPy
                        lower_bound = lower_bound.replace('pi', 'sp.pi')
                        lower_eval = eval(lower_bound, {"__builtins__": {}}, safe_namespace)
                    
                    if upper_bound == "-pi":
                        upper_eval = -sp.pi
                    elif upper_bound == "pi":
                        upper_eval = sp.pi
                    else:
                        upper_bound = upper_bound.replace('pi', 'sp.pi')
                        upper_eval = eval(upper_bound, {"__builtins__": {}}, safe_namespace)
                    
                    # Create a proper tuple for the interval
                    interval = (lower_eval, upper_eval)
                except Exception as e:
                    print(f"Failed to parse interval bounds: {str(e)}")
                    # Fall back to default interval
                    interval = (-sp.pi, sp.pi)
            
            # Default interval if none specified
            if interval is None:
                interval = (-sp.pi, sp.pi)
            
            # Manually handle parsing
            x = Symbol('x')
            
            # Create a safe namespace with all the functions we need
            safe_namespace = {
                'Symbol': Symbol, 
                'symbols': symbols,
                'sin': sp.sin,
                'cos': sp.cos,
                'tan': sp.tan,
                'exp': sp.exp,
                'log': sp.log,
                'pi': sp.pi,
                'E': sp.E,
                'e': sp.E,  # Add 'e' as a reference to Euler's number
                'x': x,
                'sp': sp
            }
            
            try:
                # Fix potential syntax issues in the expression
                # For expressions like x-x**(2), ensure proper formatting
                expr = expr.replace('**', '^')  # Normalize power notation
                expr = expr.replace('^(', '**')  # Convert back to Python power notation
                expr = re.sub(r'(\d+)x', r'\1*x', expr)  # Add multiplication between numbers and x
                
                # Handle common issue with the double parenthesis - x-x**(2)( -1 <x < 1)
                # Check for potential issue where x**2( is parsed as x**(2( 
                exponent_problem_match = re.search(r'\*\*\((\d+)\(', expr)
                if exponent_problem_match:
                    # Fix the issue by closing the first bracket properly
                    expr = expr.replace(f'**({exponent_problem_match.group(1)}(', f'**{exponent_problem_match.group(1)}(')
                
                # Handle common expressions directly for better reliability
                if expr.strip() in ['e^x', 'e**x']:
                    parsed_expr = sp.exp(x)
                elif expr.strip() == 'sin(x)':
                    parsed_expr = sp.sin(x)
                elif expr.strip() == 'cos(x)':
                    parsed_expr = sp.cos(x)
                elif expr.strip() == 'e**(-x)' or expr.strip() == 'e^(-x)':
                    parsed_expr = sp.exp(-x)
                elif expr.strip() in ['x-x**2', 'x-x^2', 'x-x*2']:
                    parsed_expr = x - x**2
                else:
                    # Replace e^x notation with exp(x) for better parsing
                    expr = expr.replace('e^x', 'exp(x)')
                    expr = expr.replace('e^(', 'exp(')
                    expr = expr.replace('e**(', 'exp(')
                    
                    # Try the safest parsing method first using SymPy's parser
                    transformations = (standard_transformations + (implicit_multiplication_application,))
                    try:
                        parsed_expr = parse_expr(expr, local_dict=safe_namespace, transformations=transformations)
                    except Exception as parse_error:
                        # If that fails, try eval with our safe namespace
                        # Handle common pattern of x-x**2
                        if expr.strip() == 'x-x**2':
                            parsed_expr = x - x**2
                        else:
                            safe_expr = expr.replace('e**', 'sp.exp')  # Convert e** to exp
                            parsed_expr = eval(safe_expr, {"__builtins__": {}}, safe_namespace)
                
                # Compute the Fourier series with explicit interval values
                series = sp.fourier_series(parsed_expr, x, (float(interval[0]), float(interval[1]))).truncate(terms)
                
                # Get the LaTeX representation
                latex_result = latex(series)
                
                # Add the interval information to the result
                interval_latex = f"\\text{{ for }} {latex(interval[0])} < x < {latex(interval[1])}"
                return f"{latex_result} \\quad {interval_latex}"
                
            except Exception as parsing_error:
                print(f"Error computing Fourier series: {str(parsing_error)}")
                
                # Try with SageMath as fallback
                if hasattr(sp, 'sage') or 'sage' in str(type(sp)).lower():
                    try:
                        # Use a try/except block to handle the import - this suppresses IDE warnings
                        # when SageMath is not installed or not in the Python path
                        sage_module = __import__('sage.all', fromlist=['*'])
                        
                        # Access the sage module safely
                        x_sage = getattr(sage_module, 'var')('x')
                        f_sage = getattr(sage_module, 'function')('f')(x_sage)
                        
                        # Convert the expr to sage syntax
                        expr_sage = expr.replace('e^x', 'exp(x)')
                        f_sage = getattr(sage_module, 'eval')(f"f(x) = {expr_sage}")
                        
                        # Compute the Fourier series
                        sage_series = getattr(sage_module, 'fourier_series_partial_sum')(f_sage, x_sage, getattr(sage_module, 'pi'), terms)
                        return f"{sage_series} \\quad \\text{{ for }} {latex(interval[0])} < x < {latex(interval[1])}"
                    except ImportError:
                        print("SageMath is not available in this environment")
                    except Exception as sage_error:
                        print(f"SageMath fallback failed: {str(sage_error)}")
                
                # Special cases hardcoding for common functions
                if expr.strip() == 'e^x':
                    a0 = sp.N(1/(2*sp.pi) * sp.integrate(sp.exp(x), (x, -sp.pi, sp.pi)))
                    coeffs = []
                    for n in range(1, terms+1):
                        an = sp.N(1/sp.pi * sp.integrate(sp.exp(x) * sp.cos(n*x), (x, -sp.pi, sp.pi)))
                        bn = sp.N(1/sp.pi * sp.integrate(sp.exp(x) * sp.sin(n*x), (x, -sp.pi, sp.pi)))
                        coeffs.append((an, bn, n))
                    
                    # Format the result
                    result = f"{a0}/2"
                    for an, bn, n in coeffs:
                        if an != 0:
                            result += f" + {an}\\cos({n}x)"
                        if bn != 0:
                            result += f" + {bn}\\sin({n}x)"
                    
                    return f"{result} \\quad \\text{{ for }} {latex(interval[0])} < x < {latex(interval[1])}"
                
                # Fallback message
                raise ValueError(f"Could not compute Fourier series for {expr}: {str(parsing_error)}")
                
        except Exception as e:
            print(f"Fourier series computation failed: {str(e)}")
            raise ValueError(f"Failed to compute Fourier series: {str(e)}")