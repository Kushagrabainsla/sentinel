import json
import os
import logging
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configure boto3 to disable SSL verification (workaround for certificate issues in Lambda layer)
boto_config = Config(
    signature_version='v4',
    retries={'max_attempts': 3, 'mode': 'standard'}
)

# Create DynamoDB resource with SSL verification disabled
dynamodb = boto3.resource('dynamodb', config=boto_config, verify=False)

CAMPAIGNS_TABLE = os.environ.get('CAMPAIGNS_TABLE')
EVENTS_TABLE = os.environ.get('EVENTS_TABLE')

def get_campaign_details(campaign_id):
    """Fetch campaign details and all events."""
    campaigns_table = dynamodb.Table(CAMPAIGNS_TABLE)
    events_table = dynamodb.Table(EVENTS_TABLE)
    
    try:
        # Get campaign details
        campaign_response = campaigns_table.get_item(Key={'id': campaign_id})
        campaign = campaign_response.get('Item')
        
        if not campaign:
            return None, None
        
        # Get all events for this campaign
        events_response = events_table.query(
            IndexName='campaign_index',
            KeyConditionExpression=Key('campaign_id').eq(campaign_id)
        )
        events = events_response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in events_response:
            events_response = events_table.query(
                IndexName='campaign_index',
                KeyConditionExpression=Key('campaign_id').eq(campaign_id),
                ExclusiveStartKey=events_response['LastEvaluatedKey']
            )
            events.extend(events_response.get('Items', []))
        
        return campaign, events
        
    except Exception as e:
        logger.error(f"Error fetching campaign details: {str(e)}", exc_info=True)
        return None, None

def calculate_metrics(events):
    """Calculate detailed metrics from events."""
    total_sent = sum(1 for e in events if e.get('type') == 'send_status')
    unique_opens = set(e.get('recipient_id') for e in events if e.get('type') == 'open')
    unique_clicks = set(e.get('recipient_id') for e in events if e.get('type') == 'click')
    total_bounces = sum(1 for e in events if e.get('type') == 'bounce')
    
    total_opens = len(unique_opens)
    total_clicks = len(unique_clicks)
    
    open_rate = (total_opens / total_sent) if total_sent > 0 else 0
    click_rate = (total_clicks / total_sent) if total_sent > 0 else 0
    bounce_rate = (total_bounces / total_sent) if total_sent > 0 else 0
    click_to_open_rate = (total_clicks / total_opens) if total_opens > 0 else 0
    
    return {
        'total_sent': total_sent,
        'total_opens': total_opens,
        'total_clicks': total_clicks,
        'total_bounces': total_bounces,
        'open_rate': round(open_rate, 4),
        'click_rate': round(click_rate, 4),
        'bounce_rate': round(bounce_rate, 4),
        'click_to_open_rate': round(click_to_open_rate, 4)
    }

def analyze_performance_breakdown(events):
    """Analyze performance by time, device, and location."""
    breakdown = {
        'by_time': {},
        'by_device': {},
        'by_browser': {}
    }
    
    for event in events:
        if event.get('type') not in ['open', 'click']:
            continue
            
        try:
            raw_data = json.loads(event.get('raw', '{}'))
            
            # By hour of day
            hour = raw_data.get('hour_of_day', 'Unknown')
            if hour not in breakdown['by_time']:
                breakdown['by_time'][hour] = {'opens': 0, 'clicks': 0}
            if event.get('type') == 'open':
                breakdown['by_time'][hour]['opens'] += 1
            elif event.get('type') == 'click':
                breakdown['by_time'][hour]['clicks'] += 1
            
            # By device type
            device = raw_data.get('device_type', 'Unknown')
            if device not in breakdown['by_device']:
                breakdown['by_device'][device] = {'opens': 0, 'clicks': 0}
            if event.get('type') == 'open':
                breakdown['by_device'][device]['opens'] += 1
            elif event.get('type') == 'click':
                breakdown['by_device'][device]['clicks'] += 1
            
            # By browser
            browser = raw_data.get('browser', 'Unknown')
            if browser not in breakdown['by_browser']:
                breakdown['by_browser'][browser] = {'opens': 0, 'clicks': 0}
            if event.get('type') == 'open':
                breakdown['by_browser'][browser]['opens'] += 1
            elif event.get('type') == 'click':
                breakdown['by_browser'][browser]['clicks'] += 1
                
        except Exception as e:
            logger.warning(f"Error parsing event data: {str(e)}")
            continue
    
    return breakdown

def analyze_campaign(event, context):
    """Lambda handler for single campaign analysis."""
    logger.info("Starting single campaign analysis")
    
    try:
        # Get campaign_id from query parameters
        campaign_id = event.get('queryStringParameters', {}).get('campaign_id')
        
        if not campaign_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'campaign_id parameter is required'})
            }
        
        logger.info(f"Analyzing campaign: {campaign_id}")
        
        # Fetch campaign and events
        campaign, events = get_campaign_details(campaign_id)
        
        if not campaign:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Campaign not found'})
            }
        
        if not events:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'campaign_id': campaign_id,
                    'campaign_name': campaign.get('name', 'N/A'),
                    'message': 'No events found for this campaign'
                })
            }
        
        # Calculate metrics
        metrics = calculate_metrics(events)
        
        # Analyze performance breakdown
        performance_breakdown = analyze_performance_breakdown(events)
        
        # Lazy import Gemini client
        from shared.gemini_client import GeminiClient
        gemini_client = GeminiClient()
        
        # Construct prompt for AI analysis
        created_at = campaign.get('created_at', 0)
        created_at_int = int(created_at) if created_at else 0
        send_time = datetime.fromtimestamp(created_at_int).isoformat() if created_at_int else 'N/A'
        
        prompt = f"""
        You are an expert Email Marketing Analyst. Analyze this specific campaign in detail:
        
        **Campaign Details:**
        - Name: {campaign.get('name', 'N/A')}
        - Subject: {campaign.get('email_subject', 'N/A')}
        - Sent: {send_time}
        - Segment ID: {campaign.get('segment_id', 'N/A')}
        
        **Performance Metrics:**
        {json.dumps(metrics, indent=2)}
        
        **Performance Breakdown:**
        {json.dumps(performance_breakdown, indent=2)}
        
        Provide a detailed analysis including:
        1. **Strengths**: What worked well in this campaign?
        2. **Weaknesses**: What didn't work or could be improved?
        3. **Specific Recommendations**: Actionable steps to improve future similar campaigns
        4. **Timing Insights**: Best times for engagement based on the data
        5. **Device/Browser Insights**: Any patterns in device or browser usage
        
        Return your analysis as a JSON object with these keys: strengths (array), weaknesses (array), recommendations (array of objects with title, description, impact_prediction), timing_insights (array), device_insights (array).
        """
        
        # Get AI analysis
        logger.info("Calling Gemini API for campaign analysis")
        ai_analysis = gemini_client.generate_json('gemini-flash-latest', prompt, temperature=0.7)
        
        # Construct response
        response_data = {
            'campaign_id': campaign_id,
            'campaign_name': campaign.get('name', 'N/A'),
            'campaign_subject': campaign.get('email_subject', 'N/A'),
            'sent_at': send_time,
            'metrics': metrics,
            'performance_breakdown': performance_breakdown,
            'ai_insights': ai_analysis,
            'total_events': len(events)
        }
        
        logger.info(f"Successfully analyzed campaign {campaign_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        logger.error(f"Error in campaign analysis: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
