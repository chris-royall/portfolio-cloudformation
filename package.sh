#!/bin/bash

# Script to package Python Lambda functions into ZIP files for CloudFormation deployment

echo "Packaging Lambda functions..."

# Package contact form Lambda function
echo "Packaging contact form Lambda function..."
cd lambda/contact-form
zip -r ../../lambda/contact-form.zip lambda_function.py
cd ../..

# Package link selection Lambda function
echo "Packaging link selection Lambda function..."
cd lambda/link-selection
zip -r ../../lambda/link-selection.zip lambda_function.py
cd ../..

echo "Lambda functions packaged successfully!"
echo "ZIP files are available in the lambda directory."
