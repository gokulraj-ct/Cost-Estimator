# Using IAM Roles in Development

## Quick Setup (3 Steps)

### Step 1: Create IAM Role & Policy

```bash
# Get your account ID
aws sts get-caller-identity --query Account --output text

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
    }'

# Create role (replace ACCOUNT_ID)
aws iam create-role \
    --role-name KostructureDevRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::ACCOUNT_ID:root"
            },
            "Action": "sts:AssumeRole"
        }]
    }'

# Attach policy to role (replace ACCOUNT_ID)
aws iam attach-role-policy \
    --role-name KostructureDevRole \
    --policy-arn arn:aws:iam::ACCOUNT_ID:policy/KostructurePricingPolicy
```

### Step 2: Configure AWS Profile

Add to `~/.aws/config`:

```ini
[profile kostructure-dev]
role_arn = arn:aws:iam::ACCOUNT_ID:role/KostructureDevRole
source_profile = default
region = us-east-1
```

### Step 3: Update Docker Compose

```yaml
# docker-compose.yml
cost-service:
  environment:
    - AWS_PROFILE=kostructure-dev
  volumes:
    - ~/.aws:/root/.aws:ro
```

Then restart:
```bash
docker-compose restart cost-service
```

---

## Alternative: Use AWS SSO (Recommended)

### Step 1: Configure SSO

```bash
aws configure sso
# Follow prompts:
# - SSO start URL: https://your-org.awsapps.com/start
# - SSO region: us-east-1
# - Profile name: kostructure-sso
```

### Step 2: Login

```bash
aws sso login --profile kostructure-sso
```

### Step 3: Use Profile

```bash
export AWS_PROFILE=kostructure-sso
docker-compose restart cost-service
```

---

## Simplest Option: Use Existing Credentials with Role

### Option A: Assume Role Manually

```bash
# Assume role (replace ACCOUNT_ID)
aws sts assume-role \
    --role-arn arn:aws:iam::ACCOUNT_ID:role/KostructureDevRole \
    --role-session-name kostructure-dev \
    --duration-seconds 3600

# Copy output credentials to .env.aws
```

### Option B: Use aws-vault (Best for Dev)

```bash
# Install aws-vault
brew install aws-vault  # macOS
# OR
sudo apt install aws-vault  # Linux

# Add credentials
aws-vault add kostructure

# Use with docker-compose
aws-vault exec kostructure -- docker-compose up
```

### Option C: Use AWS CLI Credential Process

Add to `~/.aws/config`:

```ini
[profile kostructure-dev]
credential_process = aws sts assume-role --role-arn arn:aws:iam::ACCOUNT_ID:role/KostructureDevRole --role-session-name kostructure --duration-seconds 3600 --query 'Credentials' --output json
```

---

## Current Setup (Easiest)

**Just refresh your credentials:**

```bash
# Option 1: AWS Configure
aws configure
# Enter your Access Key ID and Secret Access Key

# Option 2: AWS SSO
aws sso login

# Option 3: Export environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_SESSION_TOKEN=your_token  # if using temporary credentials

# Restart
docker-compose restart cost-service
```

---

## Verify It's Working

```bash
# Check credentials in container
docker exec kostructure-cost python3 -c "
import boto3
sts = boto3.client('sts')
identity = sts.get_caller_identity()
print(f'Account: {identity[\"Account\"]}')
print(f'ARN: {identity[\"Arn\"]}')
"

# Test pricing API
docker exec kostructure-cost python3 -c "
import boto3
pricing = boto3.client('pricing', region_name='us-east-1')
response = pricing.get_products(
    ServiceCode='AmazonEC2',
    Filters=[{'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': 't3.medium'}],
    MaxResults=1
)
print('✅ Pricing API works!')
"
```

---

## Recommended for Development

**Best Option: AWS SSO**
```bash
aws configure sso
aws sso login
export AWS_PROFILE=your-sso-profile
docker-compose up
```

**Why:**
- ✅ Temporary credentials (auto-refresh)
- ✅ No long-term keys
- ✅ Centralized access management
- ✅ MFA support
- ✅ Audit trail

---

## Quick Fix (Right Now)

Since your credentials are expired:

```bash
# 1. Get fresh credentials
aws configure
# OR
aws sso login

# 2. Verify
aws sts get-caller-identity

# 3. Restart
cd /home/gokul/kostructure
docker-compose restart cost-service

# 4. Test
curl -s -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{"files":[{"name":"test.tf","content":"resource \"aws_instance\" \"web\" { instance_type = \"t3.medium\" }"}]}' \
  | python3 -m json.tool
```

---

## Summary

**Current Setup:**
- ✅ Mounts ~/.aws credentials
- ✅ Supports IAM roles automatically
- ✅ Supports AWS profiles
- ✅ Supports AWS SSO

**To Use Role in Dev:**
1. Create IAM role with pricing permissions
2. Configure AWS profile to assume role
3. Set AWS_PROFILE environment variable
4. Restart service

**Or Just:**
- Refresh your AWS credentials
- Everything works automatically!

