import json
import logging
# from shared.gemini_client import GeminiClient

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize client
    """Lambda handler for generating subject lines."""
    logger.info("Starting subject line generation")
    
    try:
        # Lazy import and init to catch deployment errors
        from shared.gemini_client import GeminiClient
        gemini_client = GeminiClient()

        # 1. Parse Input
        body = json.loads(event.get('body', '{}'))
        content = body.get('content')
        audience = body.get('audience')
        goal = body.get('goal')
        
        if not content or not audience or not goal:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Missing required fields: content, audience, goal"})
            }
            
        # 2. Construct Prompt
        prompt = f"""
        You are an expert Email Marketing Copywriter.
        Generate 5 diverse, high-converting subject lines for the following campaign:
        
        - **Content/Description**: {content}
        - **Target Audience**: {audience}
        - **Campaign Goal**: {goal}
        
        Constraints:
        - Keep subject lines under 60 characters.
        - Use a mix of styles: Emotional, Curiosity, Direct, Benefit-focused, Urgency.
        - Avoid spam trigger words (e.g., "Free", "Guarantee", "$$$").
        
        Return the output as a JSON array of objects with the following structure:
        [
            {{
                "subject_line": "string",
                "style": "string",
                "explanation": "string (briefly explain why this works)"
            }}
        ]
        """
        
        # 3. Call Gemini
        # Using gemini-flash-latest for speed and cost efficiency
        suggestions = gemini_client.generate_json("gemini-flash-latest", prompt)
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Error in generate_subject_lines: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
