import json
import os
import uuid
import boto3
import logging
import time
from datetime import datetime
from botocore.config import Config

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configure boto3 with longer timeouts and more retries for VPC environment
boto_config = Config(
    connect_timeout=10,
    read_timeout=10,
    retries={'max_attempts': 4})

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', config=boto_config)
s3 = boto3.client('s3', config=boto_config)

# Environment variables (set in CloudFormation)
CONTACTS_TABLE = os.environ['CONTACTS_TABLE']
RESUME_BUCKET = os.environ['RESUME_BUCKET']
CLOUDFRONT_DOMAIN = os.environ['CLOUDFRONT_DOMAIN']

def get_upload_url_handler(event):
    """Get's a resume (or any file) from the web page and stores it in S3."""
    logger.info(f"Processing upload URL request: {json.dumps(event)}")
    try:
        body = json.loads(event['body'])
        file_name = body.get('fileName')
        file_type = body.get('fileType')
        
        logger.info(f"File details - Name: {file_name}, Type: {file_type}")
        
        if not file_name or not file_type:
            logger.warning("Missing required fields: fileName or fileType")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'fileName and fileType are required'})
            }
        
        file_key = f"resumes/{str(uuid.uuid4())}-{file_name}"
        logger.info(f"Generated file key: {file_key}")
        
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': RESUME_BUCKET,
                'Key': file_key,
                'ContentType': file_type
            },
            ExpiresIn=300
        )
        
        file_url = f"https://{CLOUDFRONT_DOMAIN}/{file_key}"
        logger.info(f"Generated CloudFront URL: {file_url}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'uploadUrl': presigned_url,
                'fileUrl': file_url
            })
        }
    except Exception as e:
        logger.error(f"Error generating pre-signed URL: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to generate upload URL'})
        }

def submit_contact_handler(event):
    """Get the contact information out of the event and store it in the dynamoDB table."""
    logger.info(f"Processing contact submission: {json.dumps(event)}")
    try:
        # Log environment variables
        logger.info(f"CONTACTS_TABLE: {CONTACTS_TABLE}")
        logger.info(f"AWS_REGION: {os.environ.get('AWS_REGION', 'not set')}")
        
        contact = json.loads(event['body'])
        
        if not contact.get('firstName') or not contact.get('lastName') or not contact.get('email'):
            logger.warning("Missing required contact fields")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'First name, last name, and email are required'})
            }
        
        # Create contact item
        contact_id = str(uuid.uuid4())
        contact_item = {
            'id': contact_id,
            'firstName': contact['firstName'],
            'lastName': contact['lastName'],
            'email': contact['email'],
            'phoneNumber': contact.get('phoneNumber'),
            'resumeUrl': contact.get('resumeUrl'),
            'createdAt': datetime.now().isoformat()
        }
        
        table = dynamodb.Table(CONTACTS_TABLE)        
        try:
            logger.info(f"Saving contact to DynamoDB: {json.dumps(contact_item)}")            
            response = table.put_item(Item=contact_item)
            logger.info(f"DynamoDB put_item response: {json.dumps(response)}")
        except Exception as db_error:
            logger.error(f"Error in DynamoDB operations: {str(db_error)}", exc_info=True)
            raise
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Contact information saved successfully',
                'contactId': contact_id
            })
        }
    except Exception as e:
        logger.error(f"Error saving contact: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Failed to save contact information: {str(e)}'})
        }

def lambda_handler(event, context):
    """Lambda handler receives the request from the html page and process the request."""
    logger.info(f"Received event: {json.dumps(event)}")
    
    path = event.get('path', '')
    
    if path == '/api/get-upload-url':
        return get_upload_url_handler(event)
    elif path == '/api/submit-contact':
        return submit_contact_handler(event)
    else:
        logger.warning(f"Invalid path requested: {path}")
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Not found'})
        }