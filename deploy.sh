#!/bin/bash

# CloudFormation deployment script to deploy AWS services using a single template file

# Default values
REGION="eu-west-2"
STACK_NAME="portfolio"
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
    --region)
      REGION="$2"
      shift 2
      ;;
    --domain)
      DOMAIN_NAME="$2"
      shift 2
      ;;
    AWS_PROFILE=*)
      AWS_PROFILE="${1#*=}"
      shift
      ;;
    environment=*)
      ENVIRONMENT="${1#*=}"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--environment local|prod] [--region REGION] [--domain DOMAIN_NAME] [AWS_PROFILE=profile] [environment=env]"
      exit 1
      ;;
  esac
done

# Set AWS profile if provided
if [ -n "$AWS_PROFILE" ]; then
  PROFILE_ARG="--profile $AWS_PROFILE"
fi

# Add Environment to Stack Names
STACK_NAME="$STACK_NAME-$ENVIRONMENT"

# Validate environment value
if [[ "$ENVIRONMENT" != "local" && "$ENVIRONMENT" != "prod" ]]; then
  echo "Error: Environment must be either 'local' or 'prod'"
  exit 1
fi

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Error: Template file '$TEMPLATE_FILE' not found."
    exit 1
fi

echo "----------------------------------------"
echo "Packaging and deploying Lambda functions"
echo "Environment: $ENVIRONMENT"

# Package Lambda functions
echo "Packaging Lambda functions..."
cd lambda/contact-form && zip -r ../contact-form.zip . && cd ../..
cd lambda/link-selection && zip -r ../link-selection.zip . && cd ../..
cd lambda/projects && zip -r ../projects.zip . && cd ../..

# Check if the ZIP files were created successfully
if [ ! -f "lambda/contact-form.zip" ] || [ ! -f "lambda/link-selection.zip" ] || [ ! -f "lambda/projects.zip" ]; then
    echo "Error: Lambda ZIP files not created properly."
    exit 1
fi


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
  $PROFILE_ARG

# Check deployment status
if [ "$?" -eq 0 ]; then
    echo "Checking stack status..."
    aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query "Stacks[0].StackStatus" --output text $PROFILE_ARG
    
    # Update Lambda function code
    echo "Updating Lambda function code..."

    # Get function names from CloudFormation stack outputs
    CONTACT_FORM_FUNCTION=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION $PROFILE_ARG --query 'Stacks[0].Outputs[?OutputKey==`ContactFormFunction`].OutputValue' --output text)
    LINK_SELECTION_FUNCTION=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION $PROFILE_ARG --query 'Stacks[0].Outputs[?OutputKey==`LinkSelectionFunction`].OutputValue' --output text)
    PROJECTS_FUNCTION=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION $PROFILE_ARG --query 'Stacks[0].Outputs[?OutputKey==`ProjectsFunction`].OutputValue' --output text)
    
    # Update Lambda function code
    aws lambda update-function-code --function-name "$CONTACT_FORM_FUNCTION" --zip-file fileb://lambda/contact-form.zip --region $REGION $PROFILE_ARG > /dev/null
    aws lambda update-function-code --function-name "$LINK_SELECTION_FUNCTION" --zip-file fileb://lambda/link-selection.zip --region $REGION $PROFILE_ARG > /dev/null
    aws lambda update-function-code --function-name "$PROJECTS_FUNCTION" --zip-file fileb://lambda/projects.zip --region $REGION $PROFILE_ARG > /dev/null
    
    echo "Deployment completed successfully."
    exit 0
else
    echo "----------------------------------------"
    echo "Stack '$STACK_NAME' deployment failed."
    exit 1
fi
