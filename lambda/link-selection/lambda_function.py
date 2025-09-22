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
        logger.debug(json.dumps({
            'correlation_id': correlation_id,
            'message': 'CORS preflight request',
            'request_type': 'OPTIONS'
        }))
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': '',
        }

    logger.debug(json.dumps({
        'correlation_id': correlation_id,
        'message': 'Link selection request started',
        'request_id': context.aws_request_id,
        'function_name': context.function_name
    }))
    
    try:
        # Parse request body
        body = json.loads(event['body'])
        button_clicked = body.get('buttonClicked')
        
        if not button_clicked:
            logger.error(json.dumps({
                'correlation_id': correlation_id,
                'message': 'Missing buttonClicked field',
                'validation_error': 'missing_button_clicked'
            }))
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'message': 'Missing buttonClicked field'})
            }
                
        logger.info(json.dumps({
            'correlation_id': correlation_id,
            'message': 'Link clicked',
            'button_clicked': button_clicked,
            'timestamp': datetime.now().isoformat()
        }))
        logger.debug(json.dumps({
            'correlation_id': correlation_id,
            'message': 'Link selection processed successfully',
            'status': 'success'
        }))
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'message': 'Log Recorded'})
        }
    except Exception as e:
        logger.error(json.dumps({
            'correlation_id': correlation_id,
            'message': 'Error processing link selection',
            'error_type': type(e).__name__,
            'error_message': str(e)
        }), exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'message': 'Internal Server Error'})
        }
