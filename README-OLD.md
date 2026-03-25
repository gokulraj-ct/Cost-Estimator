# Kostructure

AWS Infrastructure Cost Estimator - Production Stack Prototype

## Overview

Kostructure analyzes Terraform files and estimates AWS infrastructure costs using a microservices architecture.

## Architecture

- **Parser Service** (Go) - Fast Terraform parsing
- **Cost Service** (Python) - Cost calculations
- **API Gateway** (Python/Flask) - Request routing & database
- **CLI Tool** (Go) - Command-line interface
- **Web UI** (Next.js + React) - Modern web interface
- **PostgreSQL** - Persistent storage
- **Redis** - Caching layer

## Quick Start

### Start Backend Services

```bash
cd kostructure

# Start all backend services
docker-compose up -d

# Check health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

### Use CLI Tool

```bash
# Build CLI (one-time)
./build-cli.sh

# Estimate costs
./cli/kostructure estimate --path ./examples

# JSON output
./cli/kostructure estimate --path ./examples --format json
```

### Use Web UI

```bash
# Start simple web UI
cd web-simple
python3 -m http.server 3000

# Open browser: http://localhost:3000
```

### Test API Directly

```bash
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "files": [{
      "name": "main.tf",
      "content": "resource \"aws_instance\" \"web\" { instance_type = \"t3.medium\" }"
    }],
    "region": "us-east-1"
  }'
```

### Access Points

- **API Gateway**: http://localhost:8000
- **Web UI**: http://localhost:3000
- **Parser Service**: http://localhost:8001
- **Cost Service**: http://localhost:8002
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### CLI Usage

```bash
# Build CLI
cd cli
go build -o kostructure

# Estimate costs
./kostructure estimate --path ../examples --region us-east-1

# JSON output
./kostructure estimate --path ../examples --format json
```

## Project Structure

```
kostructure/
├── services/
│   ├── parser-service/    # Go - Terraform parser
│   ├── cost-service/      # Python - Cost calculator
│   └── api-gateway/       # Python - API & database
├── cli/                   # Go - CLI tool
├── web/                   # Next.js - Web UI
├── examples/              # Sample Terraform files
├── docker-compose.yml     # Infrastructure setup
└── DESIGN.md             # Design document
```

## API Endpoints

### API Gateway (Port 8000)

- `GET /health` - Health check
- `POST /api/v1/estimate` - Estimate costs
- `GET /api/v1/estimates` - List estimates
- `GET /api/v1/estimates/:id` - Get estimate by ID

### Parser Service (Port 8001)

- `GET /health` - Health check
- `POST /api/v1/parse` - Parse Terraform files

### Cost Service (Port 8002)

- `GET /health` - Health check
- `POST /api/v1/calculate` - Calculate costs

## Development

### Local Development (without Docker)

**Parser Service:**
```bash
cd services/parser-service
go run main.go
```

**Cost Service:**
```bash
cd services/cost-service
pip install -r requirements.txt
python main.py
```

**API Gateway:**
```bash
cd services/api-gateway
pip install -r requirements.txt
python main.py
```

**Web UI:**
```bash
cd web
npm install
npm run dev
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Parser Service | Go + Gin | Fast IaC parsing |
| Cost Service | Python + Flask | Cost calculations |
| API Gateway | Python + Flask | Routing & database |
| Database | PostgreSQL | Persistent storage |
| Cache | Redis | Fast data access |
| Web Frontend | Next.js + React | User interface |
| CLI | Go + Cobra | Command-line tool |

## License

MIT
