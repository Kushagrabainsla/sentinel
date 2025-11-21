import os
import google.generativeai as genai
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class GeminiClient:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY is required")
        
        genai.configure(api_key=api_key)
        
    def generate_content(self, model_name, prompt, temperature=0.7):
        """
        Generates content using the specified Gemini model.
        
        Args:
            model_name (str): The name of the model (e.g., 'gemini-1.5-flash', 'gemini-1.5-pro').
            prompt (str): The prompt to send to the model.
            temperature (float): Controls randomness in the output.
            
        Returns:
            str: The generated text content.
        """
        try:
            print(f"DEBUG: Generating content with model: {model_name}")
            model = genai.GenerativeModel(model_name)
            generation_config = genai.types.GenerationConfig(
                temperature=temperature
            )
            response = model.generate_content(prompt, generation_config=generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error generating content with {model_name}: {str(e)}")
            raise

    def generate_json(self, model_name, prompt, temperature=0.7):
        """
        Generates JSON content. Appends instructions to return valid JSON.
        """
        json_prompt = f"{prompt}\n\nReturn the result as a valid JSON object. Do not include markdown formatting like ```json ... ```."
        response_text = self.generate_content(model_name, json_prompt, temperature)
        
        # Clean up potential markdown formatting if the model ignores the instruction
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
