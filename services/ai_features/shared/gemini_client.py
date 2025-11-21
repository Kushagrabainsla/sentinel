import json
import os
import logging
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class GeminiClient:
    """Simple HTTP-based Gemini client without gRPC dependencies."""
    
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY is required")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def generate_content(self, model_name, prompt, temperature=0.7):
        """
        Generates content using the specified Gemini model via REST API.
        
        Args:
            model_name (str): The name of the model (e.g., 'gemini-flash-latest').
            prompt (str): The prompt to send to the model.
            temperature (float): Controls randomness in the output.
            
        Returns:
            str: The generated text content.
        """
        try:
            url = f"{self.base_url}/{model_name}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": temperature
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            text = result['candidates'][0]['content']['parts'][0]['text']
            return text
            
        except Exception as e:
            logger.error(f"Error generating content with {model_name}: {str(e)}")
            raise
    
    def generate_json(self, model_name, prompt, temperature=0.7):
        """
        Generates JSON content. Appends instructions to return valid JSON.
        """
        json_prompt = f"{prompt}\n\nReturn the result as a valid JSON object. Do not include markdown formatting like ```json ... ```."
        response_text = self.generate_content(model_name, json_prompt, temperature)
        
        # Clean up potential markdown formatting
        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
            
        try:
            return json.loads(cleaned_text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_text}")
            raise ValueError("Model did not return valid JSON") from e
