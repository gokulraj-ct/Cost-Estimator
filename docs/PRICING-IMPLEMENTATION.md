# Pricing Implementation - Static vs Dynamic

## Current Implementation (Prototype)

### Static Pricing
The prototype uses **hardcoded pricing** for fast development:

```python
PRICING = {
    'ec2': {
        't3.micro': 0.0104,   # $/hour
        't3.small': 0.0208,
        't3.medium': 0.0416,
        't3.large': 0.0832,
    },
    'rds': {
        'db.t3.micro': 0.017,
        'db.t3.small': 0.034,
        'db.t3.medium': 0.068,
    },
}

def calculate_ec2_cost(attrs):
    instance_type = attrs.get('instance_type', 't3.micro')
    hourly = PRICING['ec2'].get(instance_type, 0.0416)  # Static lookup
    monthly = hourly * 730
    return monthly
```

**Pros:**
- ✅ Fast (no API calls)
- ✅ No AWS credentials needed
- ✅ Works offline
- ✅ Good for prototype/demo

**Cons:**
- ❌ Prices may be outdated
- ❌ Limited instance types
- ❌ No regional pricing differences
- ❌ No spot/reserved pricing

---

## Production Implementation

### Dynamic Pricing with AWS Pricing API

Here's how to add **real-time pricing**:

```python
import boto3
import json
from functools import lru_cache

class AWSPricingService:
    def __init__(self, region='us-east-1'):
        self.region = region
        # AWS Pricing API is only available in us-east-1
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')
        self.cache = {}
    
    @lru_cache(maxsize=1000)
    def get_ec2_price(self, instance_type, region='us-east-1'):
        """
        Get real-time EC2 pricing from AWS Pricing API
        
        Args:
            instance_type: e.g., 't3.medium'
            region: AWS region
        
        Returns:
            Hourly price in USD
        """
        # Map region code to location name
        location_map = {
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'EU (Ireland)',
            'eu-central-1': 'EU (Frankfurt)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
        }
        
        location = location_map.get(region, 'US East (N. Virginia)')
        
        try:
            # Query AWS Pricing API
            response = self.pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
                    {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                    {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                    {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                    {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
                ],
                MaxResults=1
            )
            
            if not response['PriceList']:
                # Fallback to static pricing
                return PRICING['ec2'].get(instance_type, 0.0416)
            
            # Parse pricing data
            price_item = json.loads(response['PriceList'][0])
            on_demand = price_item['terms']['OnDemand']
            price_dimensions = list(on_demand.values())[0]['priceDimensions']
            hourly_price = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
            
            return hourly_price
        
        except Exception as e:
            print(f"Error fetching price for {instance_type}: {e}")
            # Fallback to static pricing
            return PRICING['ec2'].get(instance_type, 0.0416)
    
    @lru_cache(maxsize=1000)
    def get_rds_price(self, instance_class, engine, region='us-east-1'):
        """Get real-time RDS pricing"""
        location_map = {
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
        }
        
        location = location_map.get(region, 'US East (N. Virginia)')
        
        try:
            response = self.pricing_client.get_products(
                ServiceCode='AmazonRDS',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_class},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
                    {'Type': 'TERM_MATCH', 'Field': 'databaseEngine', 'Value': engine},
                    {'Type': 'TERM_MATCH', 'Field': 'deploymentOption', 'Value': 'Single-AZ'}
                ],
                MaxResults=1
            )
            
            if not response['PriceList']:
                return PRICING['rds'].get(instance_class, 0.034)
            
            price_item = json.loads(response['PriceList'][0])
            on_demand = price_item['terms']['OnDemand']
            price_dimensions = list(on_demand.values())[0]['priceDimensions']
            hourly_price = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
            
            return hourly_price
        
        except Exception as e:
            print(f"Error fetching RDS price: {e}")
            return PRICING['rds'].get(instance_class, 0.034)


# Updated cost calculation with dynamic pricing
def calculate_ec2_cost_dynamic(attrs, region='us-east-1'):
    """Calculate EC2 cost with real AWS pricing"""
    instance_type = attrs.get('instance_type', 't3.micro')
    
    # Get real-time price
    pricing_service = AWSPricingService(region)
    hourly_price = pricing_service.get_ec2_price(instance_type, region)
    
    # Calculate monthly cost
    monthly_cost = hourly_price * 730
    
    return monthly_cost


def calculate_rds_cost_dynamic(attrs, region='us-east-1'):
    """Calculate RDS cost with real AWS pricing"""
    instance_class = attrs.get('instance_class', 'db.t3.micro')
    engine = attrs.get('engine', 'postgres')
    storage = int(attrs.get('allocated_storage', 20))
    
    # Get real-time instance price
    pricing_service = AWSPricingService(region)
    hourly_price = pricing_service.get_rds_price(instance_class, engine, region)
    monthly_cost = hourly_price * 730
    
    # Add storage cost (this is relatively stable)
    storage_cost = storage * 0.115  # gp2 storage
    
    return monthly_cost + storage_cost
```

---

## Hybrid Approach (Recommended)

Use **Redis cache** + **AWS Pricing API** for best performance:

```python
import redis
import json
from datetime import timedelta

class CachedPricingService:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        self.cache_ttl = 86400  # 24 hours
    
    def get_ec2_price(self, instance_type, region='us-east-1'):
        """Get EC2 price with Redis caching"""
        cache_key = f"price:ec2:{instance_type}:{region}"
        
        # Try cache first
        cached_price = self.redis_client.get(cache_key)
        if cached_price:
            return float(cached_price)
        
        # Fetch from AWS Pricing API
        hourly_price = self._fetch_ec2_price_from_aws(instance_type, region)
        
        # Cache for 24 hours
        self.redis_client.setex(cache_key, self.cache_ttl, str(hourly_price))
        
        return hourly_price
    
    def _fetch_ec2_price_from_aws(self, instance_type, region):
        """Fetch price from AWS Pricing API"""
        # Same implementation as above
        pass
```

**Benefits:**
- ✅ Real-time pricing
- ✅ Fast (cached)
- ✅ Automatic updates (24h TTL)
- ✅ Fallback to static if API fails

---

## Implementation Steps

### Step 1: Update Cost Service

```python
# services/cost-service/main.py

import os
USE_DYNAMIC_PRICING = os.getenv('USE_DYNAMIC_PRICING', 'false').lower() == 'true'

if USE_DYNAMIC_PRICING:
    pricing_service = AWSPricingService()
else:
    pricing_service = None  # Use static pricing

def calculate_ec2_cost(attrs, region='us-east-1'):
    instance_type = attrs.get('instance_type', 't3.micro')
    
    if USE_DYNAMIC_PRICING and pricing_service:
        hourly = pricing_service.get_ec2_price(instance_type, region)
    else:
        # Fallback to static pricing
        hourly = PRICING['ec2'].get(instance_type, 0.0416)
    
    monthly = hourly * 730
    return monthly
```

### Step 2: Add AWS Credentials

```bash
# .env
USE_DYNAMIC_PRICING=true
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
```

### Step 3: Update docker-compose.yml

```yaml
cost-service:
  build: ./services/cost-service
  environment:
    - USE_DYNAMIC_PRICING=true
    - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
    - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    - AWS_REGION=us-east-1
```

---

## Comparison

| Feature | Static Pricing | Dynamic Pricing | Cached Dynamic |
|---------|---------------|-----------------|----------------|
| Speed | ⚡ Instant | 🐌 2-5s per request | ⚡ Instant (after cache) |
| Accuracy | ⚠️ May be outdated | ✅ Always current | ✅ Current (24h) |
| AWS Credentials | ❌ Not needed | ✅ Required | ✅ Required |
| Offline | ✅ Works | ❌ Fails | ⚠️ Uses cache |
| Cost | 💰 Free | 💰 API calls | 💰 Minimal |
| Regional Pricing | ❌ No | ✅ Yes | ✅ Yes |
| Spot/Reserved | ❌ No | ✅ Possible | ✅ Possible |

---

## Recommendation for Production

**Use Hybrid Approach:**

1. **Default**: Static pricing (fast, no credentials)
2. **Optional**: Enable dynamic pricing via environment variable
3. **Cache**: Use Redis to cache API responses (24 hours)
4. **Fallback**: If API fails, use static pricing

**Implementation:**
```python
def get_price(instance_type, region):
    # 1. Try Redis cache
    cached = redis.get(f"price:{instance_type}:{region}")
    if cached:
        return cached
    
    # 2. Try AWS Pricing API
    try:
        price = fetch_from_aws_api(instance_type, region)
        redis.setex(f"price:{instance_type}:{region}", 86400, price)
        return price
    except:
        # 3. Fallback to static
        return STATIC_PRICING.get(instance_type, default)
```

---

## Want Me to Implement This?

I can add dynamic pricing to the prototype with:
- ✅ AWS Pricing API integration
- ✅ Redis caching
- ✅ Environment variable toggle
- ✅ Fallback to static pricing

Should I implement it?
