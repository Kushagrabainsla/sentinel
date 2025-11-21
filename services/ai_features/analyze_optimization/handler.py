import json
import os
import boto3
import logging
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key, Attr
# from shared.gemini_client import GeminiClient

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
dynamodb = boto3.resource('dynamodb')
# gemini_client = GeminiClient()  # Moved inside handler

# Environment variables
CAMPAIGNS_TABLE = os.environ.get('CAMPAIGNS_TABLE')
EVENTS_TABLE = os.environ.get('EVENTS_TABLE')
INSIGHTS_TABLE = os.environ.get('INSIGHTS_TABLE')

def get_campaign_data(days=30):
    """Fetch campaigns from the last N days."""
    table = dynamodb.Table(CAMPAIGNS_TABLE)
    
    # Calculate the cutoff date
    cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    # Scan for campaigns (assuming small scale for now, otherwise use GSI with date)
    # In a real production app, we should use a GSI on 'created_at' or similar.
    # For this task, we'll scan and filter in memory or use FilterExpression if possible.
    # Assuming 'send_time' is the key date field.
    
    try:
        response = table.scan(
            FilterExpression=Attr('send_time').gte(cutoff_date)
        )
        items = response.get('Items', [])
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Attr('send_time').gte(cutoff_date),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))
            
        return items
    except Exception as e:
        logger.error(f"Error fetching campaigns: {str(e)}")
        return []

def aggregate_metrics(campaigns):
    """Aggregate metrics for the prompt."""
    data_summary = []
    
    for camp in campaigns:
        data_summary.append({
            "subject": camp.get('subject_line', 'N/A'),
            "segment": camp.get('audience_segment', 'Unknown'),
            "send_time": camp.get('send_time', 'N/A'),
            "open_rate": float(camp.get('open_rate', 0)),
            "click_rate": float(camp.get('click_rate', 0)),
            "bounce_rate": float(camp.get('bounce_rate', 0))
        })
        
    return data_summary

def analyze_optimization_agent(event, context):
    """Lambda handler for optimization agent."""
    logger.info("Starting optimization analysis")
    
    try:
        # Lazy import and init to catch deployment errors
        from shared.gemini_client import GeminiClient
        gemini_client = GeminiClient()

        # 1. Fetch Data
        campaigns = get_campaign_data(days=30)
        if not campaigns:
            logger.info("No campaigns found in the last 30 days.")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "No sufficient data to analyze."})
            }
            
        # 2. Aggregate Data
        metrics_summary = aggregate_metrics(campaigns)
        
        # 3. Construct Prompt
        prompt = f"""
        You are an expert Email Marketing Optimization Agent.
        Analyze the following campaign performance data from the last 30 days:
        
        {json.dumps(metrics_summary, indent=2)}
        
        Identify patterns in open rates, click rates, and engagement based on:
        - Time of day and day of week
        - Subject line patterns (length, keywords, tone)
        - Audience segments
        
        Provide 3-5 concrete, data-backed recommendations to improve future campaigns.
        
        Return the output as a JSON object with the following structure:
        {{
            "optimal_send_times": ["string", "string"],
            "subject_line_best_practices": ["string", "string"],
            "audience_segment_insights": ["string", "string"],
            "recommendations": [
                {{
                    "title": "string",
                    "description": "string",
                    "impact_prediction": "string"
                }}
            ]
        }}
        """
        
        # 4. Call Gemini
        # Using gemini-flash-latest for better availability and speed
        analysis_result = gemini_client.generate_json("gemini-flash-latest", prompt)
        
        # 5. Store Results
        insights_table = dynamodb.Table(INSIGHTS_TABLE)
        insight_item = {
            "insight_id": str(datetime.utcnow().timestamp()), # Simple ID
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": analysis_result,
            "campaign_count": len(campaigns)
        }
        insights_table.put_item(Item=insight_item)
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(insight_item)
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_optimization_agent: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
