import json
import logging
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize SES client
ses = boto3.client('ses')

def lambda_handler(event, context):
    """
    Contact Form Lambda function handler
    """
    logger.info(f"Contact Form Lambda function invoked with event: {json.dumps(event)}")
    
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
        send_email(name, email, message)
        
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
        logger.error(f"Error processing contact form: {str(e)}")
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

def send_email(name, email, message):
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
        logger.info(f"Email sent! Message ID: {response['MessageId']}")
        return True
    except ClientError as e:
        logger.error(f"Error sending email: {e.response['Error']['Message']}")
        raise
