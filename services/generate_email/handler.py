import os
import json
import boto3
import google.generativeai as genai


def get_gemini_api_key():
    secret_name = "sentinel_gemini_api_key"  # Hardcoded secret name
    region_name = "us-east-1"            # Update to your AWS region
    client = boto3.client('secretsmanager', region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    secret = response['SecretString']
    return json.loads(secret)['GEMINI_API_KEY']

def lambda_handler(event, context):
    try:
        body = event.get('body')
        if isinstance(body, str):
            body = json.loads(body)
        tone = body.get('tone')
        finalGoal = body.get('finalGoal')
        audiences = body.get('audiences')
        keyPoints = body.get('keyPoints')
        links = body.get('links')

        api_key = get_gemini_api_key()
        if not api_key:
            return {
                'statusCode': 500,
                'body': json.dumps({'key': 'GEMINI_API_KEY environment variable not set'})
            }
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f'''
You are an AI assistant that generates professional HTML email content.

I will provide you with:
- tone: the writing tone to use (e.g., Formal, Friendly, Persuasive)
- finalGoal: the purpose of the email
- audiences: a list of audience types (e.g., Recruiters, Investors, Students)
- keyPoints: a newline-separated list of bullet points to include
- links: an optional list of objects [{{ url, text }}]

Return the following JSON structure:
{{
  "subject": "...",
  "content": "..."   // full HTML string
}}

Instructions:
1. Generate a concise subject line in this format:
   "<finalGoal> for <audiences comma-separated>"
2. Generate an HTML email body that includes:
   - Greeting: “Hello <audiences comma-separated>,”
   - A brief intro sentence explaining the goal.
   - A bullet list using the provided keyPoints.
   - If links exist, generate a section titled “Useful Links:” followed by <ul><li>..</li></ul>.
   - A polite closing: “Best regards, The Team”
   - Well-formatted HTML with <h2>, <p>, and <ul> tags.
3. Maintain the specified tone throughout.
4. IMPORTANT: Return ONLY the JSON object. Do not wrap it in markdown code blocks.

Input:
tone: {tone}
finalGoal: {finalGoal}
audiences: {audiences}
keyPoints: {keyPoints}
links: {json.dumps(links)}
'''

        result = model.generate_content(prompt)
        response = result.response
        text = response.text()
        clean_text = text.replace('```json', '').replace('```', '').strip()

        try:
            json_response = json.loads(clean_text)
            return {
                'statusCode': 200,
                'body': json.dumps(json_response)
            }
        except Exception:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to parse AI response'})
            }
    except Exception as error:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(error)})
        }
