import json
import boto3
import os
import logging
import uuid
from decimal import Decimal

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    """
    Lambda function to retrieve projects from DynamoDB
    """
    correlation_id = str(uuid.uuid4())
    
    # Log full event information
    logger.info(f"[{correlation_id}] Full event received: {json.dumps(event, default=str)}")
    
    logger.debug(json.dumps({
        'correlation_id': correlation_id,
        'message': 'Projects request started',
        'request_id': context.aws_request_id,
        'function_name': context.function_name
    }))
    
    try:
        # Get table name from environment variable
        table_name = os.environ.get('PROJECTS_TABLE')
        if not table_name:
            logger.error(json.dumps({
                'correlation_id': correlation_id,
                'message': 'PROJECTS_TABLE environment variable not set',
                'error_type': 'configuration_error'
            }))
            raise ValueError("PROJECTS_TABLE environment variable not set")
        
        # Initialize DynamoDB resource
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Scan the table to get all projects
        logger.debug(json.dumps({
            'correlation_id': correlation_id,
            'message': 'Scanning DynamoDB table',
            'table_name': table_name
        }))
        
        response = table.scan()
        projects = response['Items']
        
        # Sort projects by sort_id column
        projects.sort(key=lambda x: x.get('sort_id', 0))
        
        logger.info(json.dumps({
            'correlation_id': correlation_id,
            'message': 'Projects retrieved successfully',
            'project_count': len(projects),
            'status': 'success'
        }))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps(projects, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error(json.dumps({
            'correlation_id': correlation_id,
            'message': 'Error retrieving projects',
            'error_type': type(e).__name__,
            'error_message': str(e)
        }), exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Error retrieving projects'
            })
        }