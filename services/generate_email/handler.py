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
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'POST,OPTIONS'
                },
                'body': ''
            }

        body = event.get('body')
        if isinstance(body, str):
            body = json.loads(body)
            
        tone = body.get('tone')
        tones = body.get('tones')
        finalGoal = body.get('finalGoal')
        audiences = body.get('audiences')
        keyPoints = body.get('keyPoints')
        links = body.get('links')

        api_key = get_gemini_api_key()
        if not api_key:
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'key': 'GEMINI_API_KEY environment variable not set'})
            }
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Support both single tone (legacy) and multiple tones (A/B test)
        tones_array = tones if tones else ([tone] if tone else ['Professional'])
        is_multiple_tones = len(tones_array) > 1

        prompt = ""
        
        if is_multiple_tones:
            # A/B Testing: Generate multiple variations
            prompt = f'''
            You are an AI assistant that generates professional HTML email content.

            I will provide you with:
            - tones: a list of writing tones to use (generate one email for each tone)
            - finalGoal: the purpose of the email
            - audiences: a list of audience types (e.g., Recruiters, Investors, Students)
            - keyPoints: a newline-separated list of bullet points to include
            - links: an optional list of objects [{{ url, text }}]

            Return a JSON array with one object per tone:

            [
              {{
                "subject": "...",
                "content": "...",   // full HTML string
                "tone": "Professional"
              }},
              {{
                "subject": "...",
                "content": "...",
                "tone": "Friendly"
              }},
              ...
            ]

            Instructions:
            1. For each tone, generate a unique subject line that reflects that tone.
            2. Generate an HTML email body that includes:
               - Greeting appropriate to the tone
               - A brief intro sentence explaining the goal in that tone
               - A bullet list using the provided keyPoints (use <ul><li> tags)
               - **IMPORTANT**: If links array is provided and not empty, you MUST include a "Useful Links" or "Learn More" section with clickable links using this format:
                 <h3>Useful Links</h3>
                 <ul>
                   <li><a href="URL" style="color: #2563eb; text-decoration: underline;">LINK_TEXT</a></li>
                 </ul>
               - A polite closing appropriate to the tone
               - Well-formatted HTML with <h2>, <p>, and <ul> tags
            3. Make each variation distinctly different in tone and style.
            4. IMPORTANT: Return ONLY the JSON array. Do not wrap it in markdown code blocks.

            Input:
            tones: {json.dumps(tones_array)}
            finalGoal: {finalGoal}
            audiences: {audiences}
            keyPoints: {keyPoints}
            links: {json.dumps(links)}
            {chr(10) + '⚠️ CRITICAL: The links array has ' + str(len(links)) + ' link(s). You MUST include ALL of them in the email body!' if links and len(links) > 0 else ''}
            '''
        else:
            # Single tone (legacy)
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
            tone: {tones_array[0]}
            finalGoal: {finalGoal}
            audiences: {audiences}
            keyPoints: {keyPoints}
            links: {json.dumps(links)}
            {chr(10) + '⚠️ CRITICAL: The links array has ' + str(len(links)) + ' link(s). You MUST include ALL of them in the email body!' if links and len(links) > 0 else ''}
            '''

        print(f"🔍 Email Generation Request: tones={tones_array}, links={len(links) if links else 0}")

        result = model.generate_content(prompt)
        text = result.text
        clean_text = text.replace('```json', '').replace('```', '').strip()

        try:
            json_response = json.loads(clean_text)
            
            response_body = {}
            if is_multiple_tones:
                # Ensure json_response is a list
                if isinstance(json_response, dict):
                    json_response = [json_response]
                
                # Ensure we have at least one item to avoid index errors
                first_item = json_response[0] if json_response and len(json_response) > 0 else {}
                
                response_body = {
                    'subject': first_item.get('subject', ''),
                    'content': first_item.get('content', ''),
                    'variations': json_response
                }
            else:
                response_body = json_response

            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps(response_body)
            }
        except Exception as e:
            print(f"Failed to parse AI response: {text}")
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'Failed to parse AI response'})
            }
    except Exception as error:
        print(f"Error: {str(error)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(error)})
        }
