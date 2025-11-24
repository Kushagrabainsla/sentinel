import json
import sys
import os

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from gemini_client import GeminiClient

def lambda_handler(event, context):
    """
    Generate email content using Gemini AI
    
    Request body:
    {
        "tone": "Professional",  // Single tone (legacy)
        "tones": ["Professional", "Friendly", "Exciting"],  // Multiple tones for A/B test
        "finalGoal": "Announce new feature",
        "audiences": ["Developers", "Managers"],
        "keyPoints": "Feature X is live\\nImproves performance\\nEasy to use",
        "links": [{"url": "https://docs.example.com", "text": "Documentation"}]
    }
    
    Response:
    {
        "subject": "...",
        "content": "...",  // HTML string
        "variations": [...]  // Only for A/B test (multiple tones)
    }
    """
    print(f"📧 Email Generation Request: {json.dumps(event, default=str)}")
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        tone = body.get('tone')
        tones = body.get('tones')
        final_goal = body.get('finalGoal', '')
        audiences = body.get('audiences', [])
        key_points = body.get('keyPoints', '')
        links = body.get('links', [])
        
        # Support both single tone (legacy) and multiple tones (A/B test)
        tones_array = tones if tones else ([tone] if tone else ['Professional'])
        is_multiple_tones = len(tones_array) > 1
        
        # Build prompt
        if is_multiple_tones:
            # A/B Testing: Generate multiple variations
            prompt = f"""
You are an AI assistant that generates professional HTML email content.

I will provide you with:
- tones: a list of writing tones to use (generate one email for each tone)
- finalGoal: the purpose of the email
- audiences: a list of audience types (e.g., Recruiters, Investors, Students)
- keyPoints: a newline-separated list of bullet points to include
- links: an optional list of objects [{{"url", "text"}}]

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
finalGoal: {final_goal}
audiences: {audiences}
keyPoints: {key_points}
links: {json.dumps(links)}
{'⚠️ CRITICAL: The links array has ' + str(len(links)) + ' link(s). You MUST include ALL of them in the email body!' if links else ''}
"""
        else:
            # Single tone (legacy)
            prompt = f"""
You are an AI assistant that generates professional HTML email content.

I will provide you with:
- tone: the writing tone to use (e.g., Formal, Friendly, Persuasive)
- finalGoal: the purpose of the email
- audiences: a list of audience types (e.g., Recruiters, Investors, Students)
- keyPoints: a newline-separated list of bullet points to include
- links: an optional list of objects [{{"url", "text"}}]

Return the following JSON structure:

{{
  "subject": "...",
  "content": "..."   // full HTML string
}}

Instructions:
1. Generate a concise subject line in this format:
   "<finalGoal> for <audiences comma-separated>"

2. Generate an HTML email body that includes:
   - Greeting: "Hello <audiences comma-separated>,"
   - A brief intro sentence explaining the goal.
   - A bullet list using the provided keyPoints (use <ul><li> tags).
   - **IMPORTANT**: If links array is provided and not empty, you MUST include a "Useful Links" or "Learn More" section with clickable links using this format:
     <h3>Useful Links</h3>
     <ul>
       <li><a href="URL" style="color: #2563eb; text-decoration: underline;">LINK_TEXT</a></li>
     </ul>
   - A polite closing: "Best regards, The Team"
   - Well-formatted HTML with <h2>, <p>, and <ul> tags.

3. Maintain the specified tone throughout.
4. IMPORTANT: Return ONLY the JSON object. Do not wrap it in markdown code blocks.

Input:
tone: {tones_array[0]}
finalGoal: {final_goal}
audiences: {audiences}
keyPoints: {key_points}
links: {json.dumps(links)}
{'⚠️ CRITICAL: The links array has ' + str(len(links)) + ' link(s). You MUST include ALL of them in the email body!' if links else ''}
"""
        
        # Log request details
        print(f"🔍 Request Details: tones={tones_array}, finalGoal={final_goal[:50]}..., linksCount={len(links)}")
        
        # Generate content using Gemini
        client = GeminiClient()
        json_response = client.generate_json('gemini-2.0-flash-exp', prompt)
        
        print(f"✅ Generated response: hasSubject={bool(json_response.get('subject') or (isinstance(json_response, list) and json_response[0].get('subject')))}")
        
        # Format response
        if is_multiple_tones:
            # Return variations array
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'subject': json_response[0].get('subject', ''),
                    'content': json_response[0].get('content', ''),
                    'variations': json_response
                })
            }
        else:
            # Return single result
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(json_response)
            }
            
    except Exception as e:
        print(f"❌ Error generating email: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
