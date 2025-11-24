import json
import sys
import os

# Add shared directory and parent services directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from gemini_client import GeminiClient
from common import get_campaigns_table, get_events_table, convert_decimals

def lambda_handler(event, context):
    """
    Generate AI insights for a campaign
    
    POST /v1/ai/campaigns/{id}/insights
    
    Request body:
    {
        "campaign": { ... },  // Campaign object
        "stats": { ... }      // Campaign stats
    }
    
    Response:
    {
        "report": {
            "executive_summary": "...",
            "key_strengths": ["...", "..."],
            "areas_for_improvement": ["...", "..."],
            "actionable_recommendations": [
                {"recommendation": "...", "example": "..."},
                ...
            ]
        }
    }
    """
    print(f"📊 Campaign Insights Request: {json.dumps(event, default=str)}")
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        campaign = body.get('campaign', {})
        stats = body.get('stats', {})
        
        # Build prompt
        prompt = f"""
You are an expert email marketing analyst. Analyze the following campaign performance and provide actionable insights.

Campaign Details:
- Subject: "{campaign.get('email_subject', '')}"
- Body Preview: "{campaign.get('email_body', '')[:500]}..."
- Type: {'Scheduled' if campaign.get('type') == 'S' else 'Immediate'}
- Status: {campaign.get('status', '')}

Performance Stats:
- Total Events: {stats.get('total_events', 0)}
- Sent: {stats.get('event_counts', {}).get('sent', 0)}
- Opened: {stats.get('event_counts', {}).get('open', 0)}
- Clicked: {stats.get('event_counts', {}).get('click', 0)}
- Unique Opens: {stats.get('unique_opens', 0)}
- Unique Clicks: {stats.get('unique_clicks', 0)}
- Avg Time to Open: {str(round(stats.get('avg_time_to_open', 0))) + ' min' if stats.get('avg_time_to_open') else 'N/A'}
- Avg Time to Click: {str(round(stats.get('avg_time_to_click', 0))) + ' min' if stats.get('avg_time_to_click') else 'N/A'}

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
"""
        
        print(f"🔍 Generating insights for campaign: {campaign.get('name', 'Unknown')}")
        
        # Generate insights using Gemini
        client = GeminiClient()
        json_response = client.generate_json('gemini-2.0-flash-exp', prompt)
        
        print(f"✅ Generated insights successfully")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'report': json_response})
        }
            
    except Exception as e:
        print(f"❌ Error generating insights: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
