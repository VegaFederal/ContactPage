#!/bin/bash
set -e

# Configuration
ENVIRONMENT=${1:-dev}
STACK_NAME="contact-page-${ENVIRONMENT}"
TEMPLATE_BUCKET="contact-page-templates-${ENVIRONMENT}"
DEPLOYMENT_BUCKET="contact-page-deployment-${ENVIRONMENT}"
REGION=$(aws configure get region)
if [ -z "$REGION" ]; then
  REGION="us-east-1"
fi

echo "Deploying to environment: ${ENVIRONMENT} in region: ${REGION}"

# Create buckets if they don't exist
echo "Creating/verifying S3 buckets..."
aws s3api head-bucket --bucket ${TEMPLATE_BUCKET} 2>/dev/null || aws s3 mb s3://${TEMPLATE_BUCKET} --region ${REGION}
aws s3api head-bucket --bucket ${DEPLOYMENT_BUCKET} 2>/dev/null || aws s3 mb s3://${DEPLOYMENT_BUCKET} --region ${REGION}

# Package Lambda function
echo "Packaging Lambda function..."
cd ../src/lambda/contact-processor
npm install
zip -r contact-processor.zip index.js node_modules package.json
aws s3 cp contact-processor.zip s3://${DEPLOYMENT_BUCKET}/${ENVIRONMENT}/lambda/
rm contact-processor.zip
cd ../../../scripts

# Upload web assets
echo "Uploading web assets..."
aws s3 sync ../src/web/ s3://${DEPLOYMENT_BUCKET}/${ENVIRONMENT}/web/

# Upload CloudFormation templates
echo "Uploading CloudFormation templates..."
aws s3 cp ../infrastructure/cloudformation/templates/ s3://${TEMPLATE_BUCKET}/templates/ --recursive

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file ../infrastructure/cloudformation/main-template.yaml \
  --stack-name ${STACK_NAME} \
  --parameter-overrides \
    Environment=${ENVIRONMENT} \
    TemplateBucket=${TEMPLATE_BUCKET} \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region ${REGION}

# Get outputs
echo "Deployment complete. Stack outputs:"
aws cloudformation describe-stacks --stack-name ${STACK_NAME} --query "Stacks[0].Outputs" --output table --region ${REGION}

# Get CloudFront URL
CLOUDFRONT_URL=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME} --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionDomainName'].OutputValue" --output text --region ${REGION})
echo "Website URL: https://${CLOUDFRONT_URL}"