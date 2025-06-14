#!/bin/bash

# CloudFormation deployment script to deploy AWS services using a single template file

# Default values
REGION="eu-west-2"
STACK_NAME="portfolio"
BUCKET_STACK_NAME="portfolio-bucket"
BUCKET_TEMPLATE_FILE="bucket-template.yaml"
TEMPLATE_FILE="template.yaml"
ENVIRONMENT="local"
DOMAIN_NAME="api.chrisroyall.com"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--environment local|prod] [--region REGION] [--domain DOMAIN_NAME]"
      exit 1
      ;;
  esac
done

# Add Environment to Stack Names
STACK_NAME="$STACK_NAME-$ENVIRONMENT"
BUCKET_STACK_NAME="$BUCKET_STACK_NAME-$ENVIRONMENT"

# Validate environment value
if [[ "$ENVIRONMENT" != "local" && "$ENVIRONMENT" != "prod" ]]; then
  echo "Error: Environment must be either 'local' or 'prod'"
  exit 1
fi

# Check if template files exists
if [ ! -f "$BUCKET_TEMPLATE_FILE" ]; then
    echo "Error: Bucket template file '$BUCKET_TEMPLATE_FILE' not found."
    exit 1
fi
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Error: Template file '$TEMPLATE_FILE' not found."
    exit 1
fi

echo "----------------------------------------"
echo "Packaging and deploying Lambda functions"
echo "Environment: $ENVIRONMENT"

# Package Lambda functions
echo "Packaging Lambda functions..."
chmod +x package.sh
./package.sh

# Check if the ZIP files were created successfully
if [ ! -f "lambda/contact-form.zip" ] || [ ! -f "lambda/link-selection.zip" ]; then
    echo "Error: Lambda ZIP files not created properly."
    echo "Current files in lambda directory:"
    ls -la lambda/
    exit 1
fi

# Deploy the S3 bucket
echo "Deploying S3 bucket..."
aws cloudformation deploy \
  --stack-name $BUCKET_STACK_NAME \
  --template-file $BUCKET_TEMPLATE_FILE \
  --region $REGION \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    Environment=$ENVIRONMENT

# Get the S3 bucket name from the stack outputs
S3_BUCKET=$(aws cloudformation describe-stacks --stack-name $BUCKET_STACK_NAME --region $REGION --query "Stacks[0].Outputs[?OutputKey=='LambdaCodeBucketName'].OutputValue" --output text)

# Upload Lambda code to S3
echo "Uploading Lambda code to S3..."
aws s3 cp lambda/contact-form.zip s3://$S3_BUCKET/ --region $REGION --no-progress > /dev/null 2>&1
aws s3 cp lambda/link-selection.zip s3://$S3_BUCKET/ --region $REGION --no-progress > /dev/null 2>&1

# Verify the files were uploaded successfully
echo "Verifying Lambda code in S3..."
aws s3 ls s3://$S3_BUCKET/contact-form.zip --region $REGION > /dev/null 2>&1 || {
    echo "Error: contact-form.zip not found in S3 bucket"
    exit 1
}
aws s3 ls s3://$S3_BUCKET/link-selection.zip --region $REGION > /dev/null 2>&1 || {
    echo "Error: link-selection.zip not found in S3 bucket"
    exit 1
}


# Deploy CloudFormation stack
echo "----------------------------------------"
echo "Deploying CloudFormation stack"
echo "Template file: $TEMPLATE_FILE"
echo "Stack name: $STACK_NAME"
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"

# Deploy the stack with all resources
echo "Deploying stack..."
aws cloudformation deploy \
  --stack-name $STACK_NAME \
  --template-file $TEMPLATE_FILE \
  --region $REGION \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    Environment=$ENVIRONMENT \
    ExistingApiDomainName=$DOMAIN_NAME \
    BucketStackName=$BUCKET_STACK_NAME

# Check deployment status
if [ "$?" -eq 0 ]; then
    echo "Checking stack status..."
    aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query "Stacks[0].StackStatus" --output text
    exit 0
else
    echo "----------------------------------------"
    echo "Stack '$STACK_NAME' deployment failed."
    exit 1
fi
