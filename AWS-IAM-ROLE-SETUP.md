# AWS IAM Role Setup for Kostructure

## Why IAM Roles > Hardcoded Credentials

✅ **IAM Roles:**
- No credential management
- Automatic rotation
- More secure
- No expiration issues
- Best practice

❌ **Hardcoded Credentials:**
- Manual rotation
- Can expire
- Security risk
- Need to update .env

---

## How It Works Now

The code uses **boto3's default credential chain**:

1. **Environment variables** (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
2. **AWS credentials file** (~/.aws/credentials)
3. **IAM role** (if running on EC2/ECS/Lambda)
4. **IAM role for service account** (if running on EKS)

**No code changes needed!** boto3 automatically picks the best option.

---

## Deployment Options

### Option 1: Local Development (Current)

**Mount host AWS credentials:**
```yaml
# docker-compose.yml
volumes:
  - ~/.aws:/root/.aws:ro
```

**Refresh credentials:**
```bash
aws configure
# OR
aws sso login
```

**Test:**
```bash
aws sts get-caller-identity
```

---

### Option 2: EC2 Instance (Production)

**1. Create IAM Role:**
```bash
# Create role with trust policy for EC2
aws iam create-role \
  --role-name KostructurePricingRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'
```

**2. Attach Pricing Policy:**
```bash
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

# Attach to role
aws iam attach-role-policy \
  --role-name KostructurePricingRole \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/KostructurePricingPolicy
```

**3. Attach Role to EC2:**
```bash
# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name KostructurePricingProfile

# Add role to profile
aws iam add-role-to-instance-profile \
  --instance-profile-name KostructurePricingProfile \
  --role-name KostructurePricingRole

# Attach to EC2 instance
aws ec2 associate-iam-instance-profile \
  --instance-id i-1234567890abcdef0 \
  --iam-instance-profile Name=KostructurePricingProfile
```

**4. Deploy:**
```bash
# No credentials needed in .env.aws!
# Just set:
USE_AWS_PRICING=true
AWS_DEFAULT_REGION=us-east-1
```

---

### Option 3: ECS/Fargate (Production)

**1. Create Task Execution Role:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "pricing:GetProducts",
      "pricing:DescribeServices"
    ],
    "Resource": "*"
  }]
}
```

**2. Update Task Definition:**
```json
{
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/KostructurePricingRole",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
  ...
}
```

**3. Deploy:**
- No credentials in environment
- Role automatically assumed

---

### Option 4: EKS with IRSA (Best for Kubernetes)

**1. Create OIDC Provider:**
```bash
eksctl utils associate-iam-oidc-provider \
  --cluster kostructure-cluster \
  --approve
```

**2. Create Service Account:**
```bash
eksctl create iamserviceaccount \
  --name kostructure-pricing-sa \
  --namespace default \
  --cluster kostructure-cluster \
  --attach-policy-arn arn:aws:iam::ACCOUNT_ID:policy/KostructurePricingPolicy \
  --approve
```

**3. Update Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cost-service
spec:
  template:
    spec:
      serviceAccountName: kostructure-pricing-sa
      containers:
      - name: cost-service
        image: kostructure-cost:latest
        env:
        - name: USE_AWS_PRICING
          value: "true"
```

---

### Option 5: Lambda (Serverless)

**1. Create Lambda Execution Role:**
```bash
aws iam create-role \
  --role-name KostructureLambdaRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'
```

**2. Attach Policies:**
```bash
# Basic Lambda execution
aws iam attach-role-policy \
  --role-name KostructureLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Pricing API access
aws iam attach-role-policy \
  --role-name KostructureLambdaRole \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/KostructurePricingPolicy
```

**3. Deploy Lambda:**
- Assign role during creation
- No credentials needed

---

## Required IAM Permissions

**Minimal policy for Pricing API:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "pricing:GetProducts",
      "pricing:DescribeServices"
    ],
    "Resource": "*"
  }]
}
```

**Note:** Pricing API doesn't support resource-level permissions, so `"Resource": "*"` is required.

---

## Testing IAM Role

**From EC2/ECS/Lambda:**
```python
import boto3

# This will automatically use IAM role
pricing = boto3.client('pricing', region_name='us-east-1')
response = pricing.get_products(
    ServiceCode='AmazonEC2',
    Filters=[
        {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': 't3.medium'}
    ],
    MaxResults=1
)
print(response)
```

**Check what credentials are being used:**
```python
import boto3

sts = boto3.client('sts')
identity = sts.get_caller_identity()
print(f"Account: {identity['Account']}")
print(f"ARN: {identity['Arn']}")
```

---

## Current Setup

**Local Development:**
```yaml
# docker-compose.yml
volumes:
  - ~/.aws:/root/.aws:ro  # Mount host credentials
```

**To use:**
1. Run `aws configure` or `aws sso login` on host
2. Credentials automatically available in container
3. No .env.aws credentials needed

**Production:**
- Remove volume mount
- Attach IAM role to EC2/ECS/Lambda
- No credentials in code or config

---

## Troubleshooting

### "No credentials found"
```bash
# Check if credentials exist
aws sts get-caller-identity

# If not, configure:
aws configure
```

### "Expired token"
```bash
# Refresh SSO
aws sso login

# Or get new session token
aws sts get-session-token
```

### "Access denied"
```bash
# Check IAM permissions
aws iam get-role --role-name KostructurePricingRole
aws iam list-attached-role-policies --role-name KostructurePricingRole
```

---

## Best Practices

1. ✅ **Use IAM roles** in production (EC2/ECS/Lambda/EKS)
2. ✅ **Mount ~/.aws** for local development
3. ✅ **Never commit** credentials to git
4. ✅ **Use least privilege** permissions
5. ✅ **Rotate credentials** regularly (if using keys)
6. ✅ **Use AWS SSO** for temporary credentials
7. ✅ **Enable CloudTrail** to audit API calls

---

## Summary

**Current Implementation:**
- ✅ Supports IAM roles (automatic)
- ✅ Supports credentials file (mounted)
- ✅ Supports environment variables (optional)
- ✅ No code changes needed
- ✅ boto3 handles everything

**To Deploy:**
1. **Local**: Mount ~/.aws credentials
2. **Production**: Attach IAM role
3. **No credentials in code!**

---

*Last Updated: 2026-03-23*
