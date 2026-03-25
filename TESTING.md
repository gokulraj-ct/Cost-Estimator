# Kostructure - Testing Guide

## Quick Start

```bash
# 1. Start services
docker-compose up -d

# 2. Run test suite
./test.sh

# 3. Try examples
./cli/kostructure estimate --path examples/production.tf
```

## Sample Files

All sample files are in `examples/` directory:

| File | Resources | Monthly Cost | Use Case |
|------|-----------|--------------|----------|
| `basic-ec2.tf` | 1 | ~$15 | Single server |
| `database.tf` | 1 | ~$31 | Database only |
| `dev-environment.tf` | 3 | ~$25 | Development |
| `microservices.tf` | 6 | ~$125 | Microservices |
| `production.tf` | 7 | ~$300 | Production HA |
| `simple-webapp.tf` | 4 | ~$110 | Web application |

## Testing Methods

### 1. CLI Tool

```bash
# Single file
./cli/kostructure estimate --path examples/basic-ec2.tf

# Directory (all .tf files)
./cli/kostructure estimate --path examples/

# JSON output
./cli/kostructure estimate --path examples/production.tf --format json

# Different region
./cli/kostructure estimate --path examples/basic-ec2.tf --region us-west-2
```

### 2. Web UI

```bash
# Start web server
cd web-simple
python3 -m http.server 3000

# Open browser
# http://localhost:3000

# Upload any .tf file from examples/
# Click "Estimate Cost"
```

### 3. API Direct

```bash
# Basic request
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "files": [{
      "name": "test.tf",
      "content": "resource \"aws_instance\" \"web\" { instance_type = \"t3.medium\" }"
    }],
    "region": "us-east-1"
  }' | python3 -m json.tool

# Get saved estimate
curl http://localhost:8000/api/v1/estimates/est_abc123 | python3 -m json.tool

# List all estimates
curl http://localhost:8000/api/v1/estimates | python3 -m json.tool
```

## Create Custom Test Files

### Example 1: Simple EC2
```hcl
resource "aws_instance" "my_server" {
  instance_type = "t3.large"
}
```

### Example 2: Database + Storage
```hcl
resource "aws_db_instance" "db" {
  instance_class    = "db.t3.medium"
  allocated_storage = 100
}

resource "aws_s3_bucket" "backup" {
}
```

### Example 3: Complete Stack
```hcl
resource "aws_instance" "app" {
  instance_type = "t3.medium"
}

resource "aws_db_instance" "db" {
  instance_class    = "db.t3.small"
  allocated_storage = 50
}

resource "aws_lb" "lb" {
}

resource "aws_s3_bucket" "assets" {
}
```

Save as `my-test.tf` and run:
```bash
./cli/kostructure estimate --path my-test.tf
```

## Expected Results

### Basic EC2 (t3.small)
```
💰 Total Monthly Cost: $15.18 USD
📍 Region: us-east-1
📦 Resources: 1

📊 Cost Breakdown:
+-------------------+--------------+--------------+
|     RESOURCE      |     TYPE     | MONTHLY COST |
+-------------------+--------------+--------------+
| aws_instance.app  | aws_instance | $15.18       |
+-------------------+--------------+--------------+
```

### Production Stack
```
💰 Total Monthly Cost: $299.83 USD
📍 Region: us-east-1
📦 Resources: 7

📊 Cost Breakdown:
+---------------------------+-----------------+--------------+
|         RESOURCE          |      TYPE       | MONTHLY COST |
+---------------------------+-----------------+--------------+
| aws_instance.web1         | aws_instance    | $60.74       |
| aws_instance.web2         | aws_instance    | $60.74       |
| aws_db_instance.prod_db   | aws_db_instance | $122.28      |
| aws_s3_bucket.data        | aws_s3_bucket   | $2.30        |
| aws_lb.main               | aws_lb          | $16.43       |
| aws_nat_gateway.main      | aws_nat_gateway | $37.35       |
+---------------------------+-----------------+--------------+
```

## Troubleshooting

### Services not running
```bash
docker-compose ps
docker-compose logs api-gateway
docker-compose restart
```

### CLI not working
```bash
./build-cli.sh
chmod +x cli/kostructure
```

### Web UI not loading
```bash
# Check if port 3000 is available
lsof -i :3000

# Restart web server
cd web-simple
python3 -m http.server 3000
```

### API errors
```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# View logs
docker-compose logs -f
```

## Performance

- **CLI**: < 1 second per estimate
- **API**: < 2 seconds per request
- **Web UI**: Instant results
- **Database**: Stores all estimates for history

## Next Steps

1. ✅ Test all sample files
2. ✅ Create your own Terraform files
3. ✅ Try the Web UI
4. ✅ Explore the API
5. 📝 Check `DESIGN.md` for architecture details
6. 📝 See `docs/DEVELOPMENT.md` for extending features

## Support

- Check `README.md` for setup instructions
- See `examples/README.md` for more sample files
- Run `./test.sh` to verify everything works
