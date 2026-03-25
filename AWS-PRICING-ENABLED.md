# ✅ AWS Pricing API - ENABLED

## Status: ACTIVE

```
🚀 Cost Service: Running
💰 AWS Pricing API: ENABLED
✅ Connected to AWS Pricing API
🔑 Using IAM Role: KostructurePricingRole
```

## Credentials

- **Role:** `arn:aws:iam::730335384723:role/KostructurePricingRole`
- **Session:** Valid for 1 hour
- **Stored in:** `.env.aws`
- **Expires:** 2026-03-18 06:22:19 UTC

## Test Results

```bash
# t3.small
./cli/kostructure estimate --path examples/basic-ec2.tf
Result: $15.18/month ✅

# t3.xlarge
Cost: $121.47/month ✅

# Production stack (7 resources)
Result: $299.83/month ✅
```

## How It Works

1. Cost service reads credentials from `.env.aws`
2. Calls AWS Pricing API for real-time prices
3. Caches results (LRU cache)
4. Falls back to static if API fails

## Renew Credentials (After 1 Hour)

When credentials expire, run:

```bash
aws sts assume-role \
  --role-arn arn:aws:iam::730335384723:role/KostructurePricingRole \
  --role-session-name kostructure-session \
  --duration-seconds 3600
```

Then update `.env.aws` with new credentials and restart:

```bash
docker-compose restart cost-service
```

## Verify It's Working

```bash
# Check logs
docker logs kostructure-cost

# Should see:
# ✅ AWS Pricing API initialized
# ✅ Connected to AWS Pricing API

# Test estimate
./cli/kostructure estimate --path examples/production.tf
```

---

**AWS Pricing API is now ACTIVE and working!** 🎉
