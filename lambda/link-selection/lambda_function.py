import json
from datetime import datetime

def lambda_handler(event, context):
    # Check for OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': '',
        }

    try:
        # Parse request body
        body = json.loads(event['body'])
        button_clicked = body.get('buttonClicked')
        
        if not button_clicked:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Missing buttonClicked field'})
            }
        
        # Simple console log with timestamp
        timestamp = datetime.now().isoformat()
        print(f"{timestamp} - Link Selected: {button_clicked}")
        
        # Log additional context if available
        if 'headers' in event and 'User-Agent' in event['headers']:
            print(f"User Agent: {event['headers']['User-Agent']}")
            
        if 'requestContext' in event and 'identity' in event['requestContext']:
            identity = event['requestContext']['identity']
            if 'sourceIp' in identity:
                print(f"Source IP: {identity['sourceIp']}")
        
        print("Lambda completed")
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'message': 'Log Recorded'})
        }
    except Exception as e:
        print(f"Error in Lambda: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'message': 'Internal Server Error'})
        }
