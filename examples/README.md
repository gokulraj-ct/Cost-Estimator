# Kostructure Sample Terraform Files

Test Kostructure with these sample infrastructure configurations.

## Available Examples

### 1. Basic EC2 (`basic-ec2.tf`)
**Cost: ~$15/month**
- Single t3.small EC2 instance
- Perfect for testing the basics

```bash
./cli/kostructure estimate --path examples/basic-ec2.tf
```

### 2. Database (`database.tf`)
**Cost: ~$31/month**
- RDS db.t3.small instance
- 50GB storage
- Good for small applications

```bash
./cli/kostructure estimate --path examples/database.tf
```

### 3. Dev Environment (`dev-environment.tf`)
**Cost: ~$25/month**
- t3.micro EC2 instance
- db.t3.micro RDS (20GB)
- S3 bucket
- Minimal cost development setup

```bash
./cli/kostructure estimate --path examples/dev-environment.tf
```

### 4. Microservices (`microservices.tf`)
**Cost: ~$125/month**
- API server (t3.medium)
- Worker server (t3.small)
- Redis cluster (2 nodes)
- PostgreSQL database (100GB)
- S3 storage
- Load balancer
- Complete microservices stack

```bash
./cli/kostructure estimate --path examples/microservices.tf
```

### 5. Production (`production.tf`)
**Cost: ~$300/month**
- 2x t3.large web servers
- db.t3.large database (200GB)
- S3 bucket
- Load balancer
- NAT gateway
- High-availability production setup

```bash
./cli/kostructure estimate --path examples/production.tf
```

### 6. Simple Web App (`simple-webapp.tf`)
**Cost: ~$110/month**
- t3.medium web server
- db.t3.medium PostgreSQL (100GB)
- S3 bucket for assets
- Application load balancer
- Standard web application

```bash
./cli/kostructure estimate --path examples/simple-webapp.tf
```

## Test All Examples

```bash
# Test each file
for file in examples/*.tf; do
    echo "Testing: $file"
    ./cli/kostructure estimate --path "$file"
    echo ""
done
```

## Using with Web UI

1. Start the web UI:
   ```bash
   cd web-simple
   python3 -m http.server 3000
   ```

2. Open http://localhost:3000

3. Upload any `.tf` file from the `examples/` folder

4. Click "Estimate Cost" to see the breakdown

## Create Your Own

Copy any example and modify:

```bash
cp examples/basic-ec2.tf my-infrastructure.tf
# Edit my-infrastructure.tf
./cli/kostructure estimate --path my-infrastructure.tf
```

## Supported Resources

- `aws_instance` - EC2 instances
- `aws_db_instance` - RDS databases
- `aws_s3_bucket` - S3 storage
- `aws_lb` - Load balancers
- `aws_nat_gateway` - NAT gateways
- `aws_elasticache_cluster` - ElastiCache
- `aws_ebs_volume` - EBS volumes
- `aws_lambda_function` - Lambda functions
- `aws_dynamodb_table` - DynamoDB tables
- `aws_vpc` - VPCs

## Cost Breakdown

All estimates include:
- Compute costs (hourly rates × 730 hours/month)
- Storage costs (per GB/month)
- Data transfer estimates
- On-Demand pricing (no reserved instances)

**Note:** Actual AWS costs may vary based on:
- Reserved instance discounts
- Spot instance pricing
- Data transfer volumes
- Regional pricing differences
- Additional features and configurations
