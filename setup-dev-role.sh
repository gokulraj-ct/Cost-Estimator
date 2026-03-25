#!/bin/bash
# Setup IAM Role for Local Development

set -e

echo "🔧 Setting up IAM Role for Kostructure Development"
echo ""

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

if [ -z "$ACCOUNT_ID" ]; then
    echo "❌ AWS credentials not configured. Run: aws configure"
    exit 1
fi

echo "✅ AWS Account: $ACCOUNT_ID"
echo ""

# Create IAM policy for Pricing API
echo "📝 Creating IAM policy..."
POLICY_ARN=$(aws iam create-policy \
    --policy-name KostructurePricingPolicy \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "pricing:GetProducts",
                "pricing:DescribeServices"
            ],
            "Resource": "*"
        }]
    }' \
    --query 'Policy.Arn' \
    --output text 2>/dev/null || \
    echo "arn:aws:iam::${ACCOUNT_ID}:policy/KostructurePricingPolicy")

echo "✅ Policy ARN: $POLICY_ARN"
echo ""

# Create IAM role for local development
echo "📝 Creating IAM role..."
ROLE_NAME="KostructureDevRole"

aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document "{
        \"Version\": \"2012-10-17\",
        \"Statement\": [{
            \"Effect\": \"Allow\",
            \"Principal\": {
                \"AWS\": \"arn:aws:iam::${ACCOUNT_ID}:root\"
            },
            \"Action\": \"sts:AssumeRole\"
        }]
    }" 2>/dev/null || echo "Role already exists"

echo "✅ Role: $ROLE_NAME"
echo ""

# Attach policy to role
echo "📝 Attaching policy to role..."
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn $POLICY_ARN 2>/dev/null || echo "Policy already attached"

echo "✅ Policy attached"
echo ""

# Get role ARN
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
echo "✅ Role ARN: $ROLE_ARN"
echo ""

# Update AWS config to use role
echo "📝 Updating ~/.aws/config..."
cat >> ~/.aws/config << AWSCONFIG

[profile kostructure-dev]
role_arn = ${ROLE_ARN}
source_profile = default
region = us-east-1
AWSCONFIG

echo "✅ AWS profile 'kostructure-dev' created"
echo ""

# Test role assumption
echo "🧪 Testing role assumption..."
aws sts get-caller-identity --profile kostructure-dev

echo ""
echo "✅ Setup complete!"
echo ""
echo "To use the role:"
echo "  export AWS_PROFILE=kostructure-dev"
echo "  docker-compose restart cost-service"
echo ""
echo "Or update docker-compose.yml:"
echo "  environment:"
echo "    - AWS_PROFILE=kostructure-dev"
