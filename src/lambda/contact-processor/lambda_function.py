import json
import os
import uuid
import boto3
from datetime import datetime

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Environment variables (set in CloudFormation)
CONTACTS_TABLE = os.environ['CONTACTS_TABLE']
RESUME_BUCKET = os.environ['RESUME_BUCKET']
CLOUDFRONT_DOMAIN = os.environ['CLOUDFRONT_DOMAIN']

def get_upload_url_handler(event):
    try:
        body = json.loads(event['body'])
        file_name = body.get('fileName')
        file_type = body.get('fileType')
        
        if not file_name or not file_type:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'fileName and fileType are required'})
            }
        
        # Generate a unique file key
        file_key = f"resumes/{str(uuid.uuid4())}-{file_name}"
        
        # Generate pre-signed URL for S3 upload
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': RESUME_BUCKET,
                'Key': file_key,
                'ContentType': file_type
            },
            ExpiresIn=300  # URL expires in 5 minutes
        )
        
        # Generate the CloudFront URL for the file
        file_url = f"https://{CLOUDFRONT_DOMAIN}/{file_key}"
        
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
        print(f"Error generating pre-signed URL: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to generate upload URL'})
        }

def submit_contact_handler(event):
    try:
        contact = json.loads(event['body'])
        
        # Validate required fields
        if not contact.get('firstName') or not contact.get('lastName') or not contact.get('email'):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'First name, last name, and email are required'})
            }
        
        # Create item for DynamoDB
        table = dynamodb.Table(CONTACTS_TABLE)
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
        
        # Save to DynamoDB
        table.put_item(Item=contact_item)
        
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
        print(f"Error saving contact: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to save contact information'})
        }

def lambda_handler(event, context):
    path = event.get('path', '')
    
    if path == '/api/get-upload-url':
        return get_upload_url_handler(event)
    elif path == '/api/submit-contact':
        return submit_contact_handler(event)
    else:
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Not found'})
        }