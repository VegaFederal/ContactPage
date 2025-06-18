# Contact Page Application

A web application for collecting contact information with resume upload functionality.

## Architecture

This application uses the following AWS services:

- **S3**: Stores static website files and uploaded resumes
- **CloudFront**: Serves the website and provides CDN capabilities
- **API Gateway**: Handles API requests
- **Lambda**: Processes form submissions and file uploads
- **DynamoDB**: Stores contact information

## Features

- Contact form with required fields (First Name, Last Name, Email)
- Optional fields (Phone Number)
- Resume upload capability
- Secure file storage in S3
- Contact information storage in DynamoDB

## Deployment

### Prerequisites

- AWS CLI installed and configured
- Node.js and npm installed
- GitHub account for CI/CD

### Local Deployment

1. Update the configuration in `scripts/config/project-config.json`
2. Run the deployment script:

```bash
cd scripts
chmod +x deploy.sh
./deploy.sh [environment]
```

Where `[environment]` is one of: `dev`, `test`, or `prod`. If not specified, it defaults to `dev`.

### CI/CD Deployment

The application is automatically deployed via GitHub Actions when changes are pushed to the main branch.

To manually trigger a deployment:

1. Go to the GitHub repository
2. Click on "Actions"
3. Select the "CI/CD Pipeline" workflow
4. Click "Run workflow"
5. Select the action (deploy/cleanup) and environment (dev/test/prod)
6. Click "Run workflow"

## Development

### Web Application

The web application is located in the `src/web` directory. It consists of:

- `index.html`: The contact form
- `styles.css`: Styling for the form
- `script.js`: JavaScript for form submission and file uploads

### Lambda Function

The Lambda function is located in the `src/lambda/contact-processor` directory. It handles:

- Contact form submissions
- Generating pre-signed URLs for file uploads
- Storing contact information in DynamoDB

### Infrastructure

The infrastructure is defined using CloudFormation templates in the `infrastructure/cloudformation` directory:

- `main-template.yaml`: Main template that orchestrates nested stacks
- `templates/contact-page.yaml`: Resources for the contact page application
- `templates/security-groups.yaml`: Security group configurations
- `templates/load-balancer.yaml`: Load balancer configurations

## Cleanup

To clean up all resources:

```bash
cd scripts
chmod +x deploy.sh
./deploy.sh [environment] cleanup
```

Or use the GitHub Actions workflow with the "cleanup" action selected.