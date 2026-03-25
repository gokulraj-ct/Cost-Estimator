#!/bin/bash
# Quick script to use IAM role in development

echo "🔧 Kostructure - Use IAM Role in Development"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS credentials not configured or expired"
    echo ""
    echo "Run one of:"
    echo "  aws configure"
    echo "  aws sso login"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✅ AWS Account: $ACCOUNT_ID"
echo ""

# Option 1: Use existing profile
echo "Option 1: Use existing AWS profile"
echo "  export AWS_PROFILE=your-profile-name"
echo "  docker-compose restart cost-service"
echo ""

# Option 2: Create role profile
echo "Option 2: Create role-based profile"
echo ""
echo "Add to ~/.aws/config:"
echo ""
echo "[profile kostructure-dev]"
echo "role_arn = arn:aws:iam::${ACCOUNT_ID}:role/KostructureDevRole"
echo "source_profile = default"
echo "region = us-east-1"
echo ""
echo "Then:"
echo "  export AWS_PROFILE=kostructure-dev"
echo "  docker-compose restart cost-service"
echo ""

# Option 3: Use SSO
echo "Option 3: Use AWS SSO (Recommended)"
echo "  aws configure sso"
echo "  aws sso login"
echo "  export AWS_PROFILE=your-sso-profile"
echo "  docker-compose restart cost-service"
echo ""

read -p "Do you want to create the IAM role now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Creating IAM role..."
    
    # Create policy
    aws iam create-policy \
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
        }' 2>/dev/null && echo "✅ Policy created" || echo "ℹ️  Policy already exists"
    
    # Create role
    aws iam create-role \
        --role-name KostructureDevRole \
        --assume-role-policy-document "{
            \"Version\": \"2012-10-17\",
            \"Statement\": [{
                \"Effect\": \"Allow\",
                \"Principal\": {
                    \"AWS\": \"arn:aws:iam::${ACCOUNT_ID}:root\"
                },
                \"Action\": \"sts:AssumeRole\"
            }]
        }" 2>/dev/null && echo "✅ Role created" || echo "ℹ️  Role already exists"
    
    # Attach policy
    aws iam attach-role-policy \
        --role-name KostructureDevRole \
        --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/KostructurePricingPolicy" 2>/dev/null && echo "✅ Policy attached" || echo "ℹ️  Policy already attached"
    
    echo ""
    echo "✅ IAM role setup complete!"
    echo ""
    echo "Add to ~/.aws/config:"
    echo ""
    echo "[profile kostructure-dev]"
    echo "role_arn = arn:aws:iam::${ACCOUNT_ID}:role/KostructureDevRole"
    echo "source_profile = default"
    echo "region = us-east-1"
    echo ""
fi
