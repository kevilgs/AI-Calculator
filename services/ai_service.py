"""
AI Service Module

This module provides AI-powered explanations for mathematical solutions using Google's Gemini API.
"""
import json
import hashlib
from google.oauth2 import service_account
import google.generativeai as genai
from config.settings import CREDENTIALS_FILE, GEMINI_MODEL

class AIService:
    def __init__(self, cache_service):
        """
        Initialize the AI service with credentials and caching
        
        Args:
            cache_service: Cache service for storing/retrieving AI responses
        """
        self.credentials_file = CREDENTIALS_FILE
        self.cache_service = cache_service
        self.is_available = self._setup_gemini()
        self.token_usage = {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "cached_requests": 0,
            "api_requests": 0
        }
    
    def _setup_gemini(self):
        """Initialize and configure the Gemini API client"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=["https://www.googleapis.com/auth/generative-language"]
            )
            genai.configure(credentials=credentials)
            print("Gemini API client initialized successfully")
            return True
        except Exception as e:
            print(f"Error initializing Gemini API: {str(e)}")
            return False
    
    def _get_cache_key(self, messages):
        """Generate a unique cache key for the request"""
        message_str = json.dumps(messages, sort_keys=True)
        return hashlib.md5(message_str.encode('utf-8')).hexdigest()
    
    def get_explanation(self, problem_description, solution):
        """
        Get AI-generated step-by-step explanation for a mathematical problem
        
        Args:
            problem_description (str): Description of the mathematical problem
            solution (str): Solution to explain
            
        Returns:
            list: List of explanation steps
        """
        if not self.is_available:
            return ["AI explanations not available - Gemini API not initialized"]
        
        prompt = f"""As a mathematics tutor explaining concepts to students, provide a clear step-by-step explanation for this problem:

Problem: {problem_description}
Final answer: {solution}

Your response should:
1. Break down the solution process into clear steps
2. Explain the reasoning behind each step
3. Use proper mathematical notation when needed
4. Highlight key concepts and formulas using **bold text** for emphasis
5. Use *italics* for important terms or variables
6. Include notes or tips where relevant

Make your explanation engaging and educational for students who are learning this topic. 
Format your response in clear paragraphs with proper markdown formatting (bold, italics) to emphasize important points.
"""
        
        # Generate cache key
        messages = [{"role": "user", "content": prompt}]
        cache_key = self._get_cache_key(messages)
        
        # Check cache first
        cached_response = self.cache_service.check_cache(cache_key)
        if cached_response:
            self.token_usage["cached_requests"] += 1
            # Add indicator that response came from database cache
            if isinstance(cached_response, list):
                cached_response.append("📦 [Response loaded from database cache]")
                return cached_response
            return [cached_response, "📦 [Response loaded from database cache]"]
        
        # No cache hit, make API request
        try:
            self.token_usage["api_requests"] += 1
            
            # Call Gemini model using the configured model name
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(prompt)
            
            # Estimate token usage
            estimated_prompt_tokens = len(prompt.split()) * 1.3
            estimated_completion_tokens = len(response.text.split()) * 1.3
            
            # Update token usage with estimates
            self.token_usage["prompt_tokens"] += int(estimated_prompt_tokens)
            self.token_usage["completion_tokens"] += int(estimated_completion_tokens)
            self.token_usage["total_tokens"] += int(estimated_prompt_tokens + estimated_completion_tokens)
            
            # Process explanation into steps
            explanation_steps = response.text.split("\n")
            explanation_steps = [step for step in explanation_steps if step.strip()]
            
            # Add indicator that this was freshly generated
            explanation_steps.append("🔄 [Response freshly generated]")
            
            # Cache the response
            response_to_cache = explanation_steps[:-1]  # Remove the indicator before caching
            self.cache_service.save_to_cache(cache_key, response_to_cache)
            
            return explanation_steps
        except Exception as e:
            error_msg = f"Error generating AI explanation: {str(e)}"
            print(error_msg)
            return ["AI explanation not available", error_msg]