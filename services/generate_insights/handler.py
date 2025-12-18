import os
import json
import boto3
import google.generativeai as genai

def get_gemini_api_key():
    secret_name = "sentinel_config"  # Unified secret name
    region_name = "us-east-1"
    client = boto3.client('secretsmanager', region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    secret = response['SecretString']
    return json.loads(secret).get('GEMINI_API_KEY')

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

        campaign = body.get('campaign')
        stats = body.get('stats')

        if not campaign or not stats:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'Missing campaign or stats data'})
            }

        api_key = get_gemini_api_key()
        if not api_key:
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'GEMINI_API_KEY not configured'})
            }

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Format stats for the prompt
        avg_time_to_open = f"{round(stats.get('avg_time_to_open'))} min" if stats.get('avg_time_to_open') else 'N/A'
        avg_time_to_click = f"{round(stats.get('avg_time_to_click'))} min" if stats.get('avg_time_to_click') else 'N/A'

        campaign_type = 'Scheduled' if campaign.get('type') == 'S' else 'Immediate'
        event_counts = stats.get('event_counts', {})

        prompt = f'''
        You are an expert email marketing analyst. Analyze the following campaign performance and provide actionable insights.
        Campaign Details:
        - Subject: "{campaign.get('email_subject')}"
        - Body Preview: "{campaign.get('email_body', '')[:500]}..."
        - Type: {campaign_type}
        - Status: {campaign.get('status')}
        Performance Stats:
        - Total Events: {stats.get('total_events')}
        - Sent: {event_counts.get('sent', 0)}
        - Opened: {event_counts.get('open', 0)}
        - Clicked: {event_counts.get('click', 0)}
        - Unique Opens: {stats.get('unique_opens')}
        - Unique Clicks: {stats.get('unique_clicks')}
        - Avg Time to Open: {avg_time_to_open}
        - Avg Time to Click: {avg_time_to_click}
        Please provide a concise report in Markdown format with the following sections:
        1. **Executive Summary**: A 2-3 sentence overview of the campaign's performance.
        2. **Key Strengths**: What worked well? (e.g., high open rate, good subject line).
        3. **Areas for Improvement**: What could be better? (e.g., low click-through rate).
        4. **Actionable Recommendations**: 3 specific things to try in the next campaign. For each, provide ONE concrete example.
        Return the response as a valid JSON object with the following structure:
        {{
          "executive_summary": "...",
          "key_strengths": ["strength 1", "strength 2"],
          "areas_for_improvement": ["improvement 1", "improvement 2"],
          "actionable_recommendations": [
            {{ "recommendation": "...", "example": "..." }},
            {{ "recommendation": "...", "example": "..." }},
            {{ "recommendation": "...", "example": "..." }}
          ]
        }}
        IMPORTANT: Return ONLY the JSON object. Do not wrap it in markdown code blocks.
        '''

        result = model.generate_content(prompt)
        text = result.text
        clean_text = text.replace('```json', '').replace('```', '').strip()

        try:
            json_response = json.loads(clean_text)
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'report': json_response})
            }
        except Exception:
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'Failed to parse AI response'})
            }

    except Exception as error:
        print(f"Error generating insights: {str(error)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(error)})
        }