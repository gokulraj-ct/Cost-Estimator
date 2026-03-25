# Kostructure Development Guide

## Architecture Overview

Kostructure uses a microservices architecture with the following components:

### Services

1. **Parser Service (Go)** - Port 8001
   - Parses Terraform files using HCL parser
   - Extracts AWS resource definitions
   - Returns normalized resource data

2. **Cost Service (Python)** - Port 8002
   - Calculates monthly costs for AWS resources
   - Uses pricing data (fallback pricing for prototype)
   - Returns cost breakdown

3. **API Gateway (Python)** - Port 8000
   - Main entry point for all requests
   - Orchestrates parser and cost services
   - Manages PostgreSQL database
   - Stores and retrieves estimates

### Data Flow

```
User Request → API Gateway → Parser Service → Cost Service → Database → Response
```

1. User uploads Terraform files via CLI or Web UI
2. API Gateway receives request
3. Calls Parser Service to extract resources
4. Calls Cost Service to calculate costs
5. Saves estimate to PostgreSQL
6. Returns result to user

### Database Schema

**estimates table:**
- id (VARCHAR) - Primary key
- total_monthly_cost (DECIMAL)
- currency (VARCHAR)
- region (VARCHAR)
- resources (JSONB) - Full resource data
- breakdown (JSONB) - Cost breakdown
- resource_count (INTEGER)
- created_at (TIMESTAMP)

## Development Workflow

### Adding New AWS Resource Support

1. **Parser Service** (`services/parser-service/main.go`)
   - Add resource type to parsing logic
   - Extract relevant attributes

2. **Cost Service** (`services/cost-service/main.py`)
   - Add pricing function for new resource
   - Update `calculate_resource_cost()` function

### Testing

**Test Parser Service:**
```bash
curl -X POST http://localhost:8001/api/v1/parse \
  -H "Content-Type: application/json" \
  -d '{"files":[{"name":"test.tf","content":"resource \"aws_instance\" \"test\" { instance_type = \"t3.micro\" }"}]}'
```

**Test Cost Service:**
```bash
curl -X POST http://localhost:8002/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"resources":[{"type":"aws_instance","name":"test","attributes":{"instance_type":"t3.micro"}}]}'
```

**Test Full Flow:**
```bash
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{"files":[{"name":"main.tf","content":"resource \"aws_instance\" \"web\" { instance_type = \"t3.medium\" }"}],"region":"us-east-1"}'
```

## Deployment

### Production Considerations

1. **Replace fallback pricing with AWS Pricing API**
   - Add AWS credentials
   - Implement proper pricing API calls
   - Add caching with Redis

2. **Add authentication**
   - API keys
   - JWT tokens
   - Rate limiting

3. **Monitoring**
   - Add logging (structured logs)
   - Metrics (Prometheus)
   - Tracing (Jaeger)

4. **Scaling**
   - Deploy to Kubernetes
   - Horizontal pod autoscaling
   - Load balancing

## Troubleshooting

### Services won't start
```bash
# Check Docker logs
docker-compose logs

# Restart specific service
docker-compose restart api-gateway
```

### Database connection errors
```bash
# Check PostgreSQL
docker-compose exec postgres psql -U postgres -d kostructure

# Recreate database
docker-compose down -v
docker-compose up -d
```

### Port conflicts
```bash
# Check what's using ports
lsof -i :8000
lsof -i :3000

# Change ports in docker-compose.yml
```

## Next Steps

1. Implement AWS Pricing API integration
2. Add more AWS resource types
3. Implement optimization recommendations
4. Add cost forecasting
5. Build CI/CD integration
6. Add authentication & authorization
