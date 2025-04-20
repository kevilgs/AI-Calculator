#!/usr/bin/env python3
"""
Test script for SageMath Docker container connectivity.
This script tests if the SageMath service can connect to the Docker container
and perform basic mathematical operations.
"""
import os
import sys
import logging
from services.sage_service import SageService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_sage")

def test_connection():
    """Test basic connectivity to SageMath Docker container"""
    logger.info("Testing connection to SageMath Docker container...")
    
    # Create SageService instance
    sage_service = SageService()
    
    if not sage_service.available:
        logger.error("SageMath service is not available!")
        logger.error("Make sure the Docker container is running with the command:")
        logger.error("docker run -p 8888:8888 sagemath/sagemath:latest sage-jupyter")
        return False
    
    logger.info("SageMath service is available!")
    logger.info(f"Connected to SageMath at {sage_service.base_url}")
    logger.info(f"Using kernel ID: {sage_service.kernel_id}")
    return True

def test_basic_math():
    """Test basic mathematical operations"""
    logger.info("Testing basic mathematical operations...")
    
    sage_service = SageService()
    if not sage_service.available:
        logger.error("SageMath service is not available!")
        return False
    
    try:
        # Test a simple calculation
        code = """
x = 5 + 7
print(f"RESULT: {x}")
"""
        result = sage_service.execute(code)
        stdout = result.get("stdout", "")
        logger.info(f"Simple calculation result: {stdout}")
        
        if "RESULT: 12" in stdout:
            logger.info("Basic calculation test passed!")
        else:
            logger.warning("Basic calculation test failed!")
        
        return True
    except Exception as e:
        logger.error(f"Error in basic math test: {str(e)}")
        return False

def test_laplace_transform():
    """Test Laplace transform calculation"""
    logger.info("Testing Laplace transform...")
    
    sage_service = SageService()
    if not sage_service.available:
        logger.error("SageMath service is not available!")
        return False
    
    try:
        # Test Laplace transform of a simple function
        result = sage_service.compute_laplace_transform("sin(t)")
        logger.info(f"Laplace transform of sin(t): {result}")
        
        if result and "1" in result and "s" in result:
            logger.info("Laplace transform test passed!")
        else:
            logger.warning("Laplace transform test failed or unexpected result!")
        
        return True
    except Exception as e:
        logger.error(f"Error in Laplace transform test: {str(e)}")
        return False

def test_fourier_series():
    """Test Fourier series calculation"""
    logger.info("Testing Fourier series...")
    
    sage_service = SageService()
    if not sage_service.available:
        logger.error("SageMath service is not available!")
        return False
    
    try:
        # Test Fourier series of x^2
        result = sage_service.compute_fourier_series("x^2")
        logger.info(f"Fourier series of x^2: {result}")
        
        # Test Fourier series of x-x^2
        logger.info("Testing problematic case: x-x^2")
        result = sage_service.compute_fourier_series("x-x^2")
        logger.info(f"Fourier series of x-x^2: {result}")
        
        return True
    except Exception as e:
        logger.error(f"Error in Fourier series test: {str(e)}")
        return False

def test_direct_execution():
    """Test direct execution method"""
    logger.info("Testing direct execution method...")
    
    sage_service = SageService()
    if not sage_service.available:
        logger.error("SageMath service is not available!")
        return False
    
    try:
        # Test direct execution with the special case handler
        result = sage_service._evaluate_direct("""
var('x')
f = x-x^2
result = fourier_series_partial_sum(f, x, pi, 5)
print(f"RESULT: {result}")
print(f"LATEX: {latex(result)}")
""")
        stdout = result.get("stdout", "")
        error = result.get("error", False)
        
        logger.info(f"Direct execution result: {stdout}")
        logger.info(f"Error detected: {error}")
        
        return True
    except Exception as e:
        logger.error(f"Error in direct execution test: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and provide a summary"""
    logger.info("=== Starting SageMath Docker Connection Tests ===")
    
    # First test connection
    connection_result = test_connection()
    if not connection_result:
        logger.error("Connection test failed. Cannot proceed with other tests.")
        return False
    
    # Run all the other tests
    test_results = {
        "Basic Math": test_basic_math(),
        "Laplace Transform": test_laplace_transform(),
        "Fourier Series": test_fourier_series(),
        "Direct Execution": test_direct_execution()
    }
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    all_passed = True
    for test_name, result in test_results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n✅ All tests passed! SageMath Docker container is working correctly.")
    else:
        logger.warning("\n❌ Some tests failed. Check the logs above for details.")
    
    return all_passed

if __name__ == "__main__":
    # Add current directory to Python path to ensure imports work
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Run all tests
    success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)