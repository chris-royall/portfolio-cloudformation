import json
import logging
import boto3
import uuid
from botocore.exceptions import ClientError

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize SES client
ses = boto3.client('ses')

def lambda_handler(event, context):
    """
    Contact Form Lambda function handler
    """
    correlation_id = str(uuid.uuid4())
    
    # Log full event information
    logger.info(f"[{correlation_id}] Full event received: {json.dumps(event, default=str)}")
    
    logger.debug(json.dumps({
        'correlation_id': correlation_id,
        'message': 'Contact form request started',
        'request_id': context.aws_request_id,
        'function_name': context.function_name
    }))
    
    try:
        # Parse the request body
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = {}
        
        # Extract form data
        name = body.get('name', 'No name provided')
        email = body.get('email', 'No email provided')
        message = body.get('message', 'No message provided')
        
        # Validate required fields
        if not email or '@' not in email:
            logger.warning(json.dumps({
                'correlation_id': correlation_id,
                'message': 'Invalid email validation failed',
                'email_provided': bool(email),
                'validation_error': 'invalid_email'
            }))
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'  # For CORS support
                },
                'body': json.dumps({
                    'message': 'Invalid email address'
                })
            }
        
        if not message:
            logger.warning(json.dumps({
                'correlation_id': correlation_id,
                'message': 'Message validation failed',
                'validation_error': 'empty_message'
            }))
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'  # For CORS support
                },
                'body': json.dumps({
                    'message': 'Message cannot be empty'
                })
            }
        
        # Send email using SES
        logger.debug(json.dumps({
            'correlation_id': correlation_id,
            'message': 'Sending email',
            'has_name': bool(name and name != 'No name provided'),
            'email_domain': email.split('@')[1] if '@' in email else 'unknown'
        }))
        
        send_email(name, email, message, correlation_id)
        
        logger.debug(json.dumps({
            'correlation_id': correlation_id,
            'message': 'Contact form processed successfully',
            'status': 'success'
        }))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # For CORS support
            },
            'body': json.dumps({
                'message': 'Contact form submitted successfully'
            })
        }
        
    except Exception as e:
        logger.error(json.dumps({
            'correlation_id': correlation_id,
            'message': 'Error processing contact form',
            'error_type': type(e).__name__,
            'error_message': str(e)
        }), exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # For CORS support
            },
            'body': json.dumps({
                'message': 'Error processing contact form'
            })
        }

def send_email(name, email, message, correlation_id):
    """
    Send email using Amazon SES
    """
    SENDER = "Portfolio Contact Form <contact@chrisroyall.com>"
    RECIPIENT = "chris@chrisroyall.com"
    SUBJECT = f"Portfolio Contact Form: Message from {name}"
    
    # The email body
    BODY_TEXT = f"""
    You have received a new message from your portfolio contact form:
    
    Name: {name}
    Email: {email}
    
    Message:
    {message}
    """
    
    BODY_HTML = f"""
    <html>
    <head></head>
    <body>
        <h2>New Contact Form Submission</h2>
        <p>You have received a new message from your portfolio contact form:</p>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Message:</strong></p>
        <p>{message}</p>
    </body>
    </html>
    """
    
    try:
        response = ses.send_email(
            Source=SENDER,
            Destination={
                'ToAddresses': [RECIPIENT],
            },
            Message={
                'Subject': {
                    'Data': SUBJECT,
                },
                'Body': {
                    'Text': {
                        'Data': BODY_TEXT,
                    },
                    'Html': {
                        'Data': BODY_HTML,
                    },
                },
            },
            ReplyToAddresses=[email],
        )
        logger.info(json.dumps({
            'correlation_id': correlation_id,
            'message': 'Email sent successfully',
            'ses_message_id': response['MessageId'],
            'recipient': RECIPIENT
        }))
        return True
    except ClientError as e:
        logger.error(json.dumps({
            'correlation_id': correlation_id,
            'message': 'SES error occurred',
            'error_code': e.response['Error']['Code'],
            'error_message': e.response['Error']['Message']
        }))
        raise
