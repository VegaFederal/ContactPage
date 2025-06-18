const AWS = require('aws-sdk');
const { v4: uuidv4 } = require('uuid');

// Initialize AWS clients
const dynamodb = new AWS.DynamoDB.DocumentClient();
const s3 = new AWS.S3();

// Environment variables (set in CloudFormation)
const CONTACTS_TABLE = process.env.CONTACTS_TABLE;
const RESUME_BUCKET = process.env.RESUME_BUCKET;
const CLOUDFRONT_DOMAIN = process.env.CLOUDFRONT_DOMAIN;

exports.getUploadUrlHandler = async (event) => {
    try {
        const body = JSON.parse(event.body);
        const { fileName, fileType } = body;
        
        if (!fileName || !fileType) {
            return {
                statusCode: 400,
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: JSON.stringify({ error: 'fileName and fileType are required' })
            };
        }
        
        // Generate a unique file key
        const fileKey = `resumes/${uuidv4()}-${fileName}`;
        
        // Generate pre-signed URL for S3 upload
        const presignedUrl = s3.getSignedUrl('putObject', {
            Bucket: RESUME_BUCKET,
            Key: fileKey,
            ContentType: fileType,
            Expires: 300 // URL expires in 5 minutes
        });
        
        // Generate the CloudFront URL for the file
        const fileUrl = `https://${CLOUDFRONT_DOMAIN}/${fileKey}`;
        
        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({
                uploadUrl: presignedUrl,
                fileUrl: fileUrl
            })
        };
    } catch (error) {
        console.error('Error generating pre-signed URL:', error);
        return {
            statusCode: 500,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({ error: 'Failed to generate upload URL' })
        };
    }
};

exports.submitContactHandler = async (event) => {
    try {
        const contact = JSON.parse(event.body);
        
        // Validate required fields
        if (!contact.firstName || !contact.lastName || !contact.email) {
            return {
                statusCode: 400,
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                body: JSON.stringify({ error: 'First name, last name, and email are required' })
            };
        }
        
        // Create item for DynamoDB
        const contactItem = {
            id: uuidv4(),
            firstName: contact.firstName,
            lastName: contact.lastName,
            email: contact.email,
            phoneNumber: contact.phoneNumber || null,
            resumeUrl: contact.resumeUrl || null,
            createdAt: new Date().toISOString()
        };
        
        // Save to DynamoDB
        await dynamodb.put({
            TableName: CONTACTS_TABLE,
            Item: contactItem
        }).promise();
        
        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({
                message: 'Contact information saved successfully',
                contactId: contactItem.id
            })
        };
    } catch (error) {
        console.error('Error saving contact:', error);
        return {
            statusCode: 500,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({ error: 'Failed to save contact information' })
        };
    }
};

// Handler for API Gateway
exports.handler = async (event) => {
    const path = event.path;
    
    if (path === '/api/get-upload-url') {
        return await getUploadUrlHandler(event);
    } else if (path === '/api/submit-contact') {
        return await submitContactHandler(event);
    } else {
        return {
            statusCode: 404,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({ error: 'Not found' })
        };
    }
};