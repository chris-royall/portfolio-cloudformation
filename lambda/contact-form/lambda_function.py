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
    
    logger.info(f"[{correlation_id}] Contact form request started", extra={
        'correlation_id': correlation_id,
        'request_id': context.aws_request_id,
        'function_name': context.function_name
    })
    
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
            logger.warning(f"[{correlation_id}] Invalid email validation failed", extra={
                'correlation_id': correlation_id,
                'email_provided': bool(email),
                'validation_error': 'invalid_email'
            })
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
            logger.warning(f"[{correlation_id}] Message validation failed", extra={
                'correlation_id': correlation_id,
                'validation_error': 'empty_message'
            })
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
        logger.info(f"[{correlation_id}] Sending email", extra={
            'correlation_id': correlation_id,
            'has_name': bool(name and name != 'No name provided'),
            'email_domain': email.split('@')[1] if '@' in email else 'unknown'
        })
        
        send_email(name, email, message, correlation_id)
        
        logger.info(f"[{correlation_id}] Contact form processed successfully", extra={
            'correlation_id': correlation_id,
            'status': 'success'
        })
        
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
        logger.error(f"[{correlation_id}] Error processing contact form", extra={
            'correlation_id': correlation_id,
            'error_type': type(e).__name__,
            'error_message': str(e)
        }, exc_info=True)
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
        logger.info(f"[{correlation_id}] Email sent successfully", extra={
            'correlation_id': correlation_id,
            'ses_message_id': response['MessageId'],
            'recipient': RECIPIENT
        })
        return True
    except ClientError as e:
        logger.error(f"[{correlation_id}] SES error occurred", extra={
            'correlation_id': correlation_id,
            'error_code': e.response['Error']['Code'],
            'error_message': e.response['Error']['Message']
        })
        raise
