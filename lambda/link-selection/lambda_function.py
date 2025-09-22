import json
from datetime import datetime
import logging
import uuid

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    correlation_id = str(uuid.uuid4())
    
    # Log full event information
    logger.info(f"[{correlation_id}] Full event received: {json.dumps(event, default=str)}")
    
    # Check for OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        logger.info(f"[{correlation_id}] CORS preflight request", extra={
            'correlation_id': correlation_id,
            'request_type': 'OPTIONS'
        })
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': '',
        }

    logger.info(f"[{correlation_id}] Link selection request started", extra={
        'correlation_id': correlation_id,
        'request_id': context.aws_request_id,
        'function_name': context.function_name
    })
    
    try:
        # Parse request body
        body = json.loads(event['body'])
        button_clicked = body.get('buttonClicked')
        
        if not button_clicked:
            logger.warning(f"[{correlation_id}] Missing buttonClicked field", extra={
                'correlation_id': correlation_id,
                'validation_error': 'missing_button_clicked'
            })
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'message': 'Missing buttonClicked field'})
            }
        
        # Extract request context
        user_agent = event.get('headers', {}).get('User-Agent', 'unknown')
        source_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
        
        logger.info(f"[{correlation_id}] Link clicked", extra={
            'correlation_id': correlation_id,
            'button_clicked': button_clicked,
            'user_agent': user_agent,
            'source_ip': source_ip,
            'timestamp': datetime.now().isoformat()
        })
        logger.info(f"[{correlation_id}] Link selection processed successfully", extra={
            'correlation_id': correlation_id,
            'status': 'success'
        })
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'message': 'Log Recorded'})
        }
    except Exception as e:
        logger.error(f"[{correlation_id}] Error processing link selection", extra={
            'correlation_id': correlation_id,
            'error_type': type(e).__name__,
            'error_message': str(e)
        }, exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'message': 'Internal Server Error'})
        }
