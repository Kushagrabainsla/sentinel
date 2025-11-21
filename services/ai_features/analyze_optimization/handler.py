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
    """Fetch campaigns from the last N days with calculated metrics."""
    campaigns_table = dynamodb.Table(CAMPAIGNS_TABLE)
    events_table = dynamodb.Table(EVENTS_TABLE)
    
    # Calculate the cutoff timestamp
    cutoff_timestamp = int((datetime.utcnow() - timedelta(days=days)).timestamp())
    logger.info(f"Fetching campaigns created after timestamp: {cutoff_timestamp}")
    
    try:
        # Scan for campaigns created in the last N days
        response = campaigns_table.scan(
            FilterExpression=Attr('created_at').gte(cutoff_timestamp)
        )
        campaigns = response.get('Items', [])
        logger.info(f"Found {len(campaigns)} campaigns in initial scan")
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = campaigns_table.scan(
                FilterExpression=Attr('created_at').gte(cutoff_timestamp),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            campaigns.extend(response.get('Items', []))
        
        logger.info(f"Total campaigns after pagination: {len(campaigns)}")
        
        # For each campaign, fetch events and calculate metrics
        enriched_campaigns = []
        for campaign in campaigns:
            campaign_id = campaign.get('id')
            logger.info(f"Processing campaign {campaign_id}")
            
            # Fetch events for this campaign
            events_response = events_table.query(
                IndexName='campaign_index',
                KeyConditionExpression=Key('campaign_id').eq(campaign_id)
            )
            events = events_response.get('Items', [])
            logger.info(f"Found {len(events)} events for campaign {campaign_id}")
            
            # Calculate metrics
            total_sent = sum(1 for e in events if e.get('type') == 'send_status')
            total_opens = len(set(e.get('recipient_id') for e in events if e.get('type') == 'open'))
            total_clicks = len(set(e.get('recipient_id') for e in events if e.get('type') == 'click'))
            total_bounces = sum(1 for e in events if e.get('type') == 'bounce')
            
            # Calculate rates
            open_rate = (total_opens / total_sent) if total_sent > 0 else 0
            click_rate = (total_clicks / total_sent) if total_sent > 0 else 0
            bounce_rate = (total_bounces / total_sent) if total_sent > 0 else 0
            
            logger.info(f"Campaign {campaign_id} metrics: sent={total_sent}, opens={total_opens}, clicks={total_clicks}, open_rate={open_rate}")
            
            # Add calculated metrics to campaign
            campaign['calculated_open_rate'] = open_rate
            campaign['calculated_click_rate'] = click_rate
            campaign['calculated_bounce_rate'] = bounce_rate
            campaign['total_sent'] = total_sent
            
            enriched_campaigns.append(campaign)
            
        return enriched_campaigns
    except Exception as e:
        logger.error(f"Error fetching campaigns: {str(e)}", exc_info=True)
        return []

def aggregate_metrics(campaigns):
    """Aggregate metrics for the prompt."""
    data_summary = []
    
    for camp in campaigns:
        # Convert timestamp to readable format
        created_at = camp.get('created_at', 0)
        send_time = datetime.fromtimestamp(created_at).isoformat() if created_at else 'N/A'
        
        data_summary.append({
            "subject": camp.get('email_subject', 'N/A'),
            "segment_id": camp.get('segment_id', 'Unknown'),
            "send_time": send_time,
            "open_rate": round(camp.get('calculated_open_rate', 0), 2),
            "click_rate": round(camp.get('calculated_click_rate', 0), 2),
            "bounce_rate": round(camp.get('calculated_bounce_rate', 0), 2),
            "total_sent": camp.get('total_sent', 0)
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
