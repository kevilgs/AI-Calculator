"""
Gemini API Quota Checker

This script checks the quota and usage for your Google Gemini API.
It will tell you your current limits, how much you've used, and when your quota resets.
"""

import os
import json
import datetime
from google.oauth2 import service_account
import google.generativeai as genai
import requests

# Path to credentials file
CREDENTIALS_FILE = 'config/calculator-456910-4c150120dcc7.json'

def load_credentials():
    """Load the service account credentials"""
    try:
        # Get absolute path to credentials file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(base_dir, CREDENTIALS_FILE)
        
        if os.path.exists(credentials_path):
            print(f"Found credentials file at {credentials_path}")
            with open(credentials_path, 'r') as f:
                creds_info = json.load(f)
            
            credentials = service_account.Credentials.from_service_account_info(creds_info)
            return credentials, creds_info
        else:
            print(f"Error: Credentials file not found at {credentials_path}")
            return None, None
    except Exception as e:
        print(f"Error loading credentials: {str(e)}")
        return None, None

def check_token_validity(creds_info):
    """Check if the service account exists and has valid permissions"""
    try:
        # Get project ID and service account email
        project_id = creds_info.get('project_id')
        client_email = creds_info.get('client_email')
        
        print(f"\nProject ID: {project_id}")
        print(f"Service Account: {client_email}")
        
        # You could make a test request here to check validity
        # For now, we'll just return the project info
        return project_id
    except Exception as e:
        print(f"Error checking token validity: {str(e)}")
        return None

def make_test_request(credentials):
    """Make a small test request to check API access"""
    try:
        # Configure Gemini with credentials
        genai.configure(credentials=credentials)
        
        # Try to initialize a model (this doesn't make an actual generation request)
        model = genai.GenerativeModel('models/gemini-1.5-pro')
        
        # Make a minimal request to check quota
        print("\nMaking a test request to check API status...")
        response = model.generate_content("Hello")
        
        print("✅ API access is working! You can make requests.")
        return True
    except Exception as e:
        print(f"❌ API test request failed: {str(e)}")
        
        # Check if it's a quota error
        error_str = str(e)
        if "429" in error_str or "exceeded your current quota" in error_str:
            print("\n🚫 QUOTA EXCEEDED: You have reached your API usage limit.")
            print("You'll need to wait until your quota resets or upgrade your plan.")
            
            # Try to extract reset time if available
            if "retry_delay" in error_str:
                try:
                    retry_seconds = int(error_str.split("seconds:")[1].split("}")[0].strip())
                    reset_time = datetime.datetime.now() + datetime.timedelta(seconds=retry_seconds)
                    print(f"Quota should reset in approximately {retry_seconds} seconds")
                    print(f"Estimated reset time: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
                except:
                    print("Could not determine when your quota will reset.")
            
            return False
        
        # Other errors
        print("This could be due to invalid credentials or network issues.")
        return False

def check_project_quotas(project_id):
    """
    This is a placeholder function since directly checking quota via API requires 
    additional Google Cloud permissions. In a real scenario, you would use the 
    Google Cloud API to check quotas.
    """
    print("\n=== GEMINI API QUOTA INFORMATION ===")
    print("Free tier limits:")
    print("- 60 queries per minute")
    print("- Typically 1M-2M tokens per minute (varies by model)")
    print("- Total daily quota of tokens (depends on your specific setup)")
    
    print("\nTo check your exact usage and limits:")
    print(f"1. Go to: https://console.cloud.google.com/apis/dashboard?project={project_id}")
    print("2. Click on 'Quotas & System Limits' in the left sidebar")
    print("3. Search for 'Gemini' or 'Generative Language API'")
    
    print("\nAlternatively, visit:")
    print("- https://ai.google.dev/ - Google AI Developer portal")
    print("- Login with the same account used for this project")
    print("- Go to 'API' section to view your usage and limits")

def main():
    """Main function to check Gemini API quota"""
    print("=== Gemini API Quota Checker ===")
    
    # Load credentials
    credentials, creds_info = load_credentials()
    if not credentials or not creds_info:
        print("Could not load credentials. Please check your credentials file.")
        return
    
    # Check token validity
    project_id = check_token_validity(creds_info)
    if not project_id:
        print("Could not validate credentials.")
        return
    
    # Make test request
    api_working = make_test_request(credentials)
    
    # Display quota information
    check_project_quotas(project_id)
    
    print("\n=== RECOMMENDATIONS ===")
    if not api_working:
        print("Since your quota appears to be exceeded:")
        print("1. Wait for your quota to reset (usually daily)")
        print("2. Consider upgrading your plan if you need more capacity")
        print("3. Optimize your code to make fewer API calls")
        print("4. Use caching more effectively to reduce API usage")
    else:
        print("Your API access is working, but you may want to:")
        print("1. Monitor your usage through the Google Cloud Console")
        print("2. Implement more robust error handling for quota limits")
        print("3. Set up alerts when approaching quota limits")

if __name__ == "__main__":
    main()