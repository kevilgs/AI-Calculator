"""
LaTeX Service Module

This module provides functionality to convert LaTeX expressions to SymPy-compatible syntax.
"""
import re

def latex_to_sympy(latex_expr):
    """
    Convert LaTeX expression to SymPy-compatible syntax
    
    Args:
        latex_expr (str): LaTeX mathematical expression
        
    Returns:
        tuple: (converted_expr, is_equation, is_system) where converted_expr is the SymPy-compatible string,
               is_equation is a boolean indicating if the expression contains an equals sign,
               and is_system is a boolean indicating if the expression represents a system of equations.
    """
    # Check if we have multiple equations (system)
    # Look for patterns like equation1,\\ equation2 or similar
    is_system = bool(re.search(r'=[^,]*,[\\\\]*\s*[^=]+=', latex_expr))
    
    # Store if this is an equation (contains =)
    is_equation = '=' in latex_expr
    
    # Remove LaTeX alignment markers
    latex_expr = re.sub(r'\\begin\{aligned\}|\{align\*?\}|\\end\{aligned\}|\{align\*?\}', '', latex_expr)
    
    # Handle parentheses and brackets
    latex_expr = latex_expr.replace('\\left(', '(')
    latex_expr = latex_expr.replace('\\right)', ')')
    latex_expr = latex_expr.replace('\\left[', '[')
    latex_expr = latex_expr.replace('\\right]', ']')
    latex_expr = latex_expr.replace('\\left{', '{')
    latex_expr = latex_expr.replace('\\right}', '}')
    
    # Handle special functions first
    
    # Unit step/Heaviside function with subscript: u_n(t) becomes Heaviside(t-n)
    # Format: u_{n}(t)
    latex_expr = re.sub(r'u\_\{([^{}]+)\}\s*\(\s*([^()]+)\s*\)', r'Heaviside(\2-\1)', latex_expr)
    
    # Alternative format: u_n(t)
    latex_expr = re.sub(r'u\_([0-9]+)\s*\(\s*([^()]+)\s*\)', r'Heaviside(\2-\1)', latex_expr)
    
    # Standard Heaviside/unit step without shift: u(t)
    latex_expr = re.sub(r'u\s*\(\s*([^()]+)\s*\)', r'Heaviside(\1)', latex_expr)
    
    # LaTeX Heaviside function
    latex_expr = re.sub(r'\\mathcal{H}\s*\(\s*([^()]+)\s*\)', r'Heaviside(\1)', latex_expr)
    latex_expr = re.sub(r'\\operatorname{H}\s*\(\s*([^()]+)\s*\)', r'Heaviside(\1)', latex_expr)
    latex_expr = re.sub(r'\\theta\s*\(\s*([^()]+)\s*\)', r'Heaviside(\1)', latex_expr)
    
    # Dirac delta function
    latex_expr = re.sub(r'\\delta\s*\(\s*([^()]+)\s*\)', r'DiracDelta(\1)', latex_expr)
    latex_expr = re.sub(r'\\operatorname{\\delta}\s*\(\s*([^()]+)\s*\)', r'DiracDelta(\1)', latex_expr)
    
    # Handle trigonometric and other functions
    trig_functions = {
        r'\\sin': 'sin',
        r'\\cos': 'cos',
        r'\\tan': 'tan',
        r'\\cot': 'cot',
        r'\\sec': 'sec',
        r'\\csc': 'csc',
        r'\\arcsin': 'asin',
        r'\\arccos': 'acos',
        r'\\arctan': 'atan',
        r'\\sinh': 'sinh',
        r'\\cosh': 'cosh',
        r'\\tanh': 'tanh',
        r'\\ln': 'log',
        r'\\log': 'log10',
        r'\\exp': 'exp'
    }
    
    for latex_func, sympy_func in trig_functions.items():
        # Replace LaTeX function with SymPy function
        latex_expr = latex_expr.replace(latex_func, sympy_func)
    
    replacements = {
        r'\\frac\{([^{}]+)\}\{([^{}]+)\}': r'(\1)/(\2)',  # Fractions
        r'\\sqrt\{([^{}]+)\}': r'sqrt(\1)',  # Square roots
        r'\\pi': 'pi',  # Pi
        r'\\infty': 'oo',  # Infinity
        r'\\cdot': '*',  # Multiplication
        r'\\times': '*',  # Multiplication
        r'\\div': '/',  # Division
        r'\\pm': '+-',  # Plus-minus
    }

    for pattern, replacement in replacements.items():
        latex_expr = re.sub(pattern, replacement, latex_expr)

    # Handle superscripts and subscripts
    latex_expr = re.sub(r'\^\{([^{}]+)\}', r'**(\1)', latex_expr)  # Superscripts
    latex_expr = re.sub(r'\_\{([^{}]+)\}', r'_(\1)', latex_expr)  # Subscripts
    
    # Replace ^ with ** for exponentiation
    latex_expr = latex_expr.replace('^', '**')
    
    return latex_expr, is_equation, is_system

def sympy_to_sage(sympy_expr):
    """
    Convert SymPy-compatible expression to SageMath-compatible syntax
    
    Args:
        sympy_expr (str): SymPy-compatible mathematical expression
        
    Returns:
        str: SageMath-compatible expression
    """
    # Most syntax is compatible, but some adjustments might be needed
    
    # Replace SymPy's Heaviside with Sage's equivalent
    sage_expr = sympy_expr.replace('Heaviside(', 'heaviside(')
    
    # Replace SymPy's DiracDelta with Sage's equivalent
    sage_expr = sage_expr.replace('DiracDelta(', 'dirac_delta(')
    
    # Handle other conversions if needed
    
    return sage_expr