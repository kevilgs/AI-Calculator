"""
Test script for Llama API integration

This script tests the Llama API connection and response handling
separately from the main application to diagnose any issues.
"""
import os
import requests
import json
import logging
import sys
from datetime import datetime

# Configure logging to show detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("llama_test")

def verify_api_key(api_key):
    """Verify if the OpenRouter API key is valid"""
    logger.info("Verifying API key validity...")
    
    try:
        # Make a simple model list request to check authentication
        response = requests.get(
            url="https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✓ API key is valid - Successfully authenticated with OpenRouter")
            return True
        elif response.status_code == 401:
            logger.error(f"✗ API key is invalid - Authentication failed with status {response.status_code}")
            logger.error(f"Error details: {response.text}")
            return False
        else:
            logger.error(f"✗ Unexpected response from OpenRouter - Status code: {response.status_code}")
            logger.error(f"Response details: {response.text}")
            return False
    except Exception as e:
        logger.error(f"✗ Error verifying API key: {str(e)}")
        return False

def test_llama_api():
    """Test the Llama API connection and response handling"""
    # Use the API key from environment or the hardcoded one for testing
    api_key = os.environ.get('OPENROUTER_API_KEY', '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')
    
    # First verify that the API key is valid
    if not verify_api_key(api_key):
        logger.error("Cannot continue testing as API key is invalid")
        logger.info("Please check your OpenRouter API key or get a new one from https://openrouter.ai/keys")
        return
    
    # Test expressions
    test_expressions = [
        "e^(-4t)*sinh(t)*sin(t)",
        "t*e^(2t)*sin(t)",
        "sin(t)",
        "t^2"
    ]
    
    for expr in test_expressions:
        logger.info(f"Testing Laplace transform for: {expr}")
        
        # Use raw string with triple quotes to avoid escape character issues
        prompt = f'''Calculate the Laplace transform of the following function: {expr}

I only need the final answer in LaTeX format. Do not provide any working, explanations, or steps.
Just return the final mathematical result as a LaTeX expression.

For example, if the input is "e^(-4t)*sinh(t)*sin(t)", the output should be "\\frac{{s+4}}{{(s+4)^4 + 2(s+4)^2 + 1}}".
'''
        
        try:
            logger.info(f"Sending request to OpenRouter API for expression: {expr}")
            
            # Record start time to measure latency
            start_time = datetime.now()
            
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://ai-calculator.app",
                    "X-Title": "AI Calculator",
                },
                data=json.dumps({
                    "model": "meta-llama/llama-3.3-70b-instruct:free",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 500,
                    "temperature": 0.1
                }),
                timeout=30
            )
            
            # Calculate request time
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Request completed in {elapsed_time:.2f} seconds")
            
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Full API response: {json.dumps(data, indent=2)}")
                
                if 'choices' in data and len(data['choices']) > 0:
                    raw_result = data['choices'][0]['message']['content'].strip()
                    logger.info(f"Raw result: {raw_result}")
                    
                    # Clean the result
                    cleaned_result = clean_latex_response(raw_result)
                    logger.info(f"Cleaned result: {cleaned_result}")
                    logger.info("✓ Test successful!")
                else:
                    logger.error("✗ No choices in API response")
            else:
                logger.error(f"✗ API request failed: {response.text}")
                
                # Provide more specific error guidance
                if response.status_code == 401:
                    logger.error("Authentication error: Your API key is invalid or has expired")
                elif response.status_code == 403:
                    logger.error("Authorization error: Your account lacks permission to use this model")
                elif response.status_code == 429:
                    logger.error("Rate limit exceeded: You've reached the request limit for your plan")
                elif response.status_code >= 500:
                    logger.error("Server error: OpenRouter is experiencing issues")
        
        except requests.exceptions.RequestException as req_e:
            logger.error(f"✗ Request error: {str(req_e)}")
            
            # More detailed network error diagnosis
            if "ConnectionError" in str(req_e):
                logger.error("Network connection error - Check your internet connection")
            elif "Timeout" in str(req_e):
                logger.error("Request timed out - OpenRouter API may be experiencing high load")
            elif "SSLError" in str(req_e):
                logger.error("SSL error - Your system may have outdated certificates")
        except Exception as e:
            logger.error(f"✗ Error testing Llama API: {str(e)}", exc_info=True)
        
        logger.info("=" * 50)  # Separator between tests

def clean_latex_response(response):
    """Clean up the response from Llama to extract just the LaTeX formula"""
    # Remove any markdown code block indicators
    response = response.replace("```latex", "").replace("```", "")
    response = response.replace("$$", "").replace("$", "")
    
    # If there are multiple lines, join them
    response = " ".join(line.strip() for line in response.split("\n") if line.strip())
    
    return response

if __name__ == "__main__":
    logger.info("Starting Llama API test")
    logger.info("This script will verify your OpenRouter API key and test the Llama API connection")
    logger.info("-" * 50)
    test_llama_api()
    logger.info("Test completed")
    logger.info("If tests failed, try the following steps:")
    logger.info("1. Check your OpenRouter API key at https://openrouter.ai/keys")
    logger.info("2. Ensure you have sufficient credits on your account")
    logger.info("3. Check if the meta-llama/llama-3.3-70b-instruct:free model is available")
    logger.info("4. Try using a different API key or a different model")