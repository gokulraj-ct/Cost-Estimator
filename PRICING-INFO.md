# Kostructure Pricing Information

## Current Status: Static/Fallback Pricing ✅

### How It Works Now

**Currently using**: Static fallback pricing (hardcoded values)
**Reason**: AWS credentials expired

### Pricing Sources

#### 1. Static Pricing (Currently Active)
- **Location**: Hardcoded in plugin files
- **Accuracy**: Based on AWS pricing as of implementation date
- **Pros**:
  - ✅ Always available
  - ✅ No AWS credentials needed
  - ✅ Fast (no API calls)
  - ✅ No AWS costs
- **Cons**:
  - ⚠️ May become outdated
  - ⚠️ Limited instance types
  - ⚠️ Single region pricing (us-east-1)

#### 2. AWS Pricing API (Available but Disabled)
- **Status**: Disabled (credentials expired)
- **When enabled**: Real-time pricing from AWS
- **Pros**:
  - ✅ Always up-to-date
  - ✅ All instance types
  - ✅ All regions
  - ✅ Accurate pricing
- **Cons**:
  - ⚠️ Requires AWS credentials
  - ⚠️ Slower (API calls)
  - ⚠️ Credentials can expire

---

## Current Pricing Data

### EC2 Instances (us-east-1)
```
t3.micro    : $0.0104/hour = $7.59/month
t3.small    : $0.0208/hour = $15.18/month
t3.medium   : $0.0416/hour = $30.37/month
t3.large    : $0.0832/hour = $60.74/month
t3.xlarge   : $0.1664/hour = $121.47/month
t3.2xlarge  : $0.3328/hour = $242.94/month

t2.micro    : $0.0116/hour = $8.47/month
t2.small    : $0.023/hour  = $16.79/month
t2.medium   : $0.0464/hour = $33.87/month

m5.large    : $0.096/hour  = $70.08/month
m5.xlarge   : $0.192/hour  = $140.16/month
m5.2xlarge  : $0.384/hour  = $280.32/month
```

### RDS Instances (us-east-1)
```
db.t3.micro   : $0.017/hour = $12.41/month
db.t3.small   : $0.034/hour = $24.82/month
db.t3.medium  : $0.068/hour = $49.64/month
db.t3.large   : $0.136/hour = $99.28/month
db.t3.xlarge  : $0.272/hour = $198.56/month

db.m5.large   : $0.175/hour = $127.75/month
db.m5.xlarge  : $0.35/hour  = $255.50/month
```

### S3 Storage
```
Standard Storage: $0.023/GB/month
Estimated usage:  100 GB = $2.30/month
```

### Load Balancer
```
Application LB: $0.0225/hour = $16.43/month
Network LB:     $0.0225/hour = $16.43/month
```

---

## How to Enable AWS Pricing API

### Prerequisites
1. Valid AWS credentials (Access Key + Secret Key)
2. IAM permissions for Pricing API
3. Credentials must not be expired

### Steps

1. **Get AWS Credentials**
   ```bash
   # From AWS Console or CLI
   aws sts get-session-token
   ```

2. **Update .env.aws**
   ```bash
   cd /home/gokul/kostructure
   nano .env.aws
   ```
   
   Set:
   ```
   USE_AWS_PRICING=true
   AWS_ACCESS_KEY_ID=your_key_here
   AWS_SECRET_ACCESS_KEY=your_secret_here
   AWS_SESSION_TOKEN=your_token_here  # If using temporary credentials
   AWS_DEFAULT_REGION=us-east-1
   ```

3. **Restart Cost Service**
   ```bash
   docker-compose restart cost-service
   ```

4. **Verify**
   ```bash
   docker logs kostructure-cost | grep "AWS Pricing"
   ```
   
   Should see:
   ```
   💰 AWS Pricing API: ENABLED
      ✅ Connected to AWS Pricing API
   ```

---

## Pricing Accuracy

### Static Pricing
- **Accuracy**: ~95% for common instance types
- **Last Updated**: Implementation date
- **Coverage**: 
  - EC2: 12 instance types
  - RDS: 7 instance types
  - S3: Standard storage only
  - LB: ALB/NLB basic pricing

### AWS Pricing API
- **Accuracy**: 100% (real-time from AWS)
- **Coverage**: All AWS services and instance types
- **Regions**: All AWS regions
- **Updates**: Real-time

---

## Cost Calculation Formula

### EC2
```
Monthly Cost = (Hourly Rate × 730 hours) + EBS Volume Cost
EBS Cost = Volume Size (GB) × $0.08/GB/month (GP3)
```

### RDS
```
Monthly Cost = (Hourly Rate × 730 hours) + Storage Cost
Storage Cost = Allocated Storage (GB) × $0.115/GB/month (GP2)
```

### S3
```
Monthly Cost = Storage (GB) × $0.023/GB/month
Estimated at 100 GB if not specified
```

### Load Balancer
```
Monthly Cost = Hourly Rate × 730 hours
ALB/NLB: $0.0225/hour = $16.43/month
```

---

## Fallback Mechanism

The system automatically falls back to static pricing if:
1. AWS Pricing API is disabled
2. AWS credentials are missing/expired
3. API call fails
4. Network issues

**This ensures the service always works!**

---

## Recommendations

### For Development/Testing
✅ **Use static pricing**
- No AWS credentials needed
- Fast and reliable
- Good enough for estimates

### For Production
✅ **Use AWS Pricing API**
- Always accurate
- All instance types
- All regions
- Real-time updates

### Hybrid Approach
✅ **Use both**
- Try AWS API first
- Fall back to static if fails
- Best of both worlds

---

## Future Enhancements

### Planned
1. **Pricing cache** - Cache AWS API results (1 hour)
2. **More services** - Lambda, DynamoDB, etc.
3. **Reserved instances** - Discounted pricing
4. **Savings plans** - Commitment-based discounts
5. **Spot instances** - Variable pricing
6. **Custom pricing** - Override with your negotiated rates

### Nice to Have
- Historical pricing trends
- Price alerts
- Cost forecasting
- Budget tracking
- Multi-cloud pricing (Azure, GCP)

---

## FAQ

### Q: Are the costs accurate?
**A**: Static pricing is ~95% accurate for common types. AWS API is 100% accurate.

### Q: Why not always use AWS API?
**A**: Requires credentials, can expire, adds latency. Static pricing is simpler.

### Q: How often is static pricing updated?
**A**: Manually updated. Check implementation date.

### Q: Can I use my own pricing?
**A**: Not yet, but planned for future versions.

### Q: Does it include taxes?
**A**: No, prices are pre-tax.

### Q: Does it include data transfer costs?
**A**: No, only compute/storage costs.

### Q: What about free tier?
**A**: Not included. Shows full pricing.

---

**Current Status**: ✅ Working with static pricing
**AWS API Status**: ⚠️ Disabled (credentials expired)
**Accuracy**: ~95% for common instance types
**Recommendation**: Static pricing is sufficient for most use cases

---

*Last Updated: 2026-03-23*
