# Kostructure - Prototype Design Document

## AWS Infrastructure Cost Estimator

## Executive Summary

This document outlines the design for a Minimum Viable Product (MVP) prototype of an infrastructure cost estimation tool focused exclusively on AWS. The prototype will demonstrate core functionality with a simplified architecture, serving as a proof-of-concept before building the full-featured platform.

**Timeline**: 6-8 weeks  
**Team Size**: 2-3 developers  
**Target**: Functional prototype with essential features

---

## Prototype Scope

### What's Included (MVP Features)

1. **Terraform Parser** - Parse basic Terraform files for AWS resources
2. **Cost Calculation** - Estimate costs for 10-15 common AWS services
3. **CLI Tool** - Command-line interface for cost estimation
4. **Simple Web UI** - Basic dashboard to view results
5. **Cost Breakdown** - Detailed cost breakdown by resource

### What's Excluded (Future Phases)

- Multi-cloud support (Azure, GCP)
- CloudFormation, CDK, Pulumi parsers
- Real-time cost tracking
- Optimization recommendations
- ML-based forecasting
- CI/CD integrations
- Policy engine
- Team collaboration features
- Advanced analytics

---

## Architecture Overview

### Simplified Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACES                          │
│  ┌──────────────┐              ┌──────────────┐            │
│  │   CLI Tool   │              │   Web UI     │            │
│  └──────────────┘              └──────────────┘            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    REST API (Flask)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  /estimate  │  /resources  │  /breakdown  │  /health │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   CORE SERVICES                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Terraform  │  │     Cost     │  │    Cache     │     │
│  │    Parser    │  │  Calculator  │  │   (Redis)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   DATA STORAGE                              │
│  ┌──────────────┐              ┌──────────────┐            │
│  │   SQLite     │              │  AWS Pricing │            │
│  │  (Estimates) │              │     API      │            │
│  └──────────────┘              └──────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Backend API** | Python + Flask | Fast development, rich ecosystem |
| **Terraform Parser** | Python HCL2 library | Native Python, easy integration |
| **Cost Calculator** | Python | Good for data processing |
| **Database** | SQLite | No setup, file-based, sufficient for prototype |
| **Cache** | Redis (optional) | Speed up pricing API calls |
| **CLI** | Python Click | Simple, powerful CLI framework |
| **Web Frontend** | React + Vite | Fast setup, modern tooling |
| **API Client** | Axios | Standard HTTP client |
| **Deployment** | Docker + Docker Compose | Easy local development |

---

## Detailed Component Design

### 1. Terraform Parser

**Purpose**: Extract AWS resource definitions from Terraform files

**Supported Resources (MVP)**
- `aws_instance` (EC2)
- `aws_db_instance` (RDS)
- `aws_s3_bucket` (S3)
- `aws_ebs_volume` (EBS)
- `aws_lb` (Load Balancer)
- `aws_nat_gateway` (NAT Gateway)
- `aws_vpc` (VPC)
- `aws_lambda_function` (Lambda)
- `aws_dynamodb_table` (DynamoDB)
- `aws_elasticache_cluster` (ElastiCache)

**Input**
```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
  
  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }
  
  tags = {
    Name = "web-server"
  }
}
```

**Output (Normalized)**
```json
{
  "type": "aws_instance",
  "name": "web",
  "attributes": {
    "instance_type": "t3.medium",
    "ami": "ami-0c55b159cbfafe1f0",
    "root_block_device": {
      "volume_size": 30,
      "volume_type": "gp3"
    }
  },
  "region": "us-east-1"
}
```

**Implementation**
```python
# parser.py
import hcl2
import json

class TerraformParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.resources = []
    
    def parse(self):
        with open(self.file_path, 'r') as f:
            tf_dict = hcl2.load(f)
        
        if 'resource' in tf_dict:
            for resource_type, resources in tf_dict['resource'].items():
                for resource_name, attributes in resources.items():
                    self.resources.append({
                        'type': resource_type,
                        'name': resource_name,
                        'attributes': attributes
                    })
        
        return self.resources
    
    def get_aws_resources(self):
        return [r for r in self.resources if r['type'].startswith('aws_')]
```

### 2. Cost Calculator

**Purpose**: Calculate monthly costs for AWS resources

**Pricing Data Source**: AWS Pricing API

**Calculation Logic**

```python
# calculator.py
import boto3
import json

class CostCalculator:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')
        self.cache = {}
    
    def calculate_ec2_cost(self, instance_type, region='us-east-1'):
        # Query AWS Pricing API
        filters = [
            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self._get_location_name(region)},
            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
            {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
            {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'}
        ]
        
        response = self.pricing_client.get_products(
            ServiceCode='AmazonEC2',
            Filters=filters
        )
        
        # Parse pricing
        if response['PriceList']:
            price_item = json.loads(response['PriceList'][0])
            on_demand = price_item['terms']['OnDemand']
            price_dimensions = list(on_demand.values())[0]['priceDimensions']
            hourly_price = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
            monthly_cost = hourly_price * 730  # 730 hours/month average
            return monthly_cost
        
        return 0
    
    def calculate_rds_cost(self, instance_class, engine, storage_gb):
        # Similar logic for RDS
        pass
    
    def calculate_s3_cost(self, storage_gb, requests_per_month):
        # S3 pricing: storage + requests
        storage_cost = storage_gb * 0.023  # $0.023 per GB
        request_cost = (requests_per_month / 1000) * 0.0004  # $0.0004 per 1000 requests
        return storage_cost + request_cost
    
    def calculate_total_cost(self, resources):
        total = 0
        breakdown = []
        
        for resource in resources:
            cost = 0
            if resource['type'] == 'aws_instance':
                cost = self.calculate_ec2_cost(
                    resource['attributes']['instance_type'],
                    resource.get('region', 'us-east-1')
                )
            elif resource['type'] == 'aws_db_instance':
                cost = self.calculate_rds_cost(
                    resource['attributes']['instance_class'],
                    resource['attributes']['engine'],
                    resource['attributes'].get('allocated_storage', 20)
                )
            # ... other resource types
            
            breakdown.append({
                'resource': f"{resource['type']}.{resource['name']}",
                'monthly_cost': round(cost, 2)
            })
            total += cost
        
        return {
            'total_monthly_cost': round(total, 2),
            'breakdown': breakdown
        }
```

**Pricing Assumptions (Simplified)**
- All EC2 instances: On-Demand pricing
- All RDS instances: Single-AZ, On-Demand
- S3: Standard storage class
- Default region: us-east-1
- No data transfer costs (for MVP)
- No reserved instance discounts

### 3. REST API

**Purpose**: Expose cost estimation functionality via HTTP

**Endpoints**

```python
# app.py
from flask import Flask, request, jsonify
from parser import TerraformParser
from calculator import CostCalculator
import os
import uuid

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

@app.route('/api/v1/estimate', methods=['POST'])
def estimate():
    """
    Estimate cost from Terraform files
    
    Request:
    {
        "files": [
            {"name": "main.tf", "content": "..."},
            {"name": "variables.tf", "content": "..."}
        ],
        "region": "us-east-1"
    }
    
    Response:
    {
        "estimate_id": "est_abc123",
        "total_monthly_cost": 245.50,
        "currency": "USD",
        "resources": [...],
        "breakdown": [...]
    }
    """
    data = request.json
    files = data.get('files', [])
    region = data.get('region', 'us-east-1')
    
    # Save files temporarily
    temp_dir = f"/tmp/{uuid.uuid4()}"
    os.makedirs(temp_dir)
    
    all_resources = []
    for file in files:
        file_path = os.path.join(temp_dir, file['name'])
        with open(file_path, 'w') as f:
            f.write(file['content'])
        
        parser = TerraformParser(file_path)
        resources = parser.parse()
        all_resources.extend(resources)
    
    # Calculate costs
    calculator = CostCalculator(region=region)
    result = calculator.calculate_total_cost(all_resources)
    
    # Save to database
    estimate_id = f"est_{uuid.uuid4().hex[:8]}"
    # ... save to SQLite
    
    return jsonify({
        'estimate_id': estimate_id,
        'total_monthly_cost': result['total_monthly_cost'],
        'currency': 'USD',
        'region': region,
        'resources': all_resources,
        'breakdown': result['breakdown']
    })

@app.route('/api/v1/estimates/<estimate_id>', methods=['GET'])
def get_estimate(estimate_id):
    """Get saved estimate by ID"""
    # ... fetch from SQLite
    pass

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### 4. CLI Tool

**Purpose**: Command-line interface for developers

**Commands**

```bash
# Estimate cost from local Terraform files
infracost estimate --path ./terraform/

# Estimate specific file
infracost estimate --file main.tf

# Specify region
infracost estimate --path ./ --region us-west-2

# Output formats
infracost estimate --path ./ --format json
infracost estimate --path ./ --format table

# Show detailed breakdown
infracost estimate --path ./ --breakdown
```

**Implementation**

```python
# cli.py
import click
import requests
import os
from tabulate import tabulate

@click.group()
def cli():
    """Infrastructure Cost Estimator CLI"""
    pass

@cli.command()
@click.option('--path', default='.', help='Path to Terraform files')
@click.option('--file', help='Specific Terraform file')
@click.option('--region', default='us-east-1', help='AWS region')
@click.option('--format', default='table', type=click.Choice(['table', 'json']))
@click.option('--breakdown', is_flag=True, help='Show detailed breakdown')
def estimate(path, file, region, format, breakdown):
    """Estimate infrastructure costs"""
    
    # Read Terraform files
    files = []
    if file:
        with open(file, 'r') as f:
            files.append({'name': os.path.basename(file), 'content': f.read()})
    else:
        for root, dirs, filenames in os.walk(path):
            for filename in filenames:
                if filename.endswith('.tf'):
                    filepath = os.path.join(root, filename)
                    with open(filepath, 'r') as f:
                        files.append({'name': filename, 'content': f.read()})
    
    # Call API
    response = requests.post('http://localhost:5000/api/v1/estimate', json={
        'files': files,
        'region': region
    })
    
    result = response.json()
    
    # Display results
    if format == 'json':
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"\n💰 Total Monthly Cost: ${result['total_monthly_cost']}")
        click.echo(f"Region: {result['region']}")
        click.echo(f"Currency: {result['currency']}\n")
        
        if breakdown:
            table_data = [
                [item['resource'], f"${item['monthly_cost']}"]
                for item in result['breakdown']
            ]
            click.echo(tabulate(table_data, headers=['Resource', 'Monthly Cost'], tablefmt='grid'))

if __name__ == '__main__':
    cli()
```

### 5. Web UI

**Purpose**: Simple web interface for viewing estimates

**Pages**

1. **Home** - Upload Terraform files
2. **Results** - View cost breakdown
3. **History** - List of past estimates

**Implementation**

```jsx
// App.jsx
import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [files, setFiles] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileUpload = (e) => {
    const uploadedFiles = Array.from(e.target.files);
    Promise.all(
      uploadedFiles.map(file => 
        file.text().then(content => ({
          name: file.name,
          content: content
        }))
      )
    ).then(setFiles);
  };

  const handleEstimate = async () => {
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:5000/api/v1/estimate', {
        files: files,
        region: 'us-east-1'
      });
      setResult(response.data);
    } catch (error) {
      console.error('Error:', error);
    }
    setLoading(false);
  };

  return (
    <div className="container">
      <h1>AWS Cost Estimator</h1>
      
      <div className="upload-section">
        <input 
          type="file" 
          multiple 
          accept=".tf"
          onChange={handleFileUpload}
        />
        <button onClick={handleEstimate} disabled={loading || files.length === 0}>
          {loading ? 'Calculating...' : 'Estimate Cost'}
        </button>
      </div>

      {result && (
        <div className="results">
          <h2>Cost Estimate</h2>
          <div className="total-cost">
            <h3>${result.total_monthly_cost}/month</h3>
            <p>Region: {result.region}</p>
          </div>
          
          <h3>Breakdown</h3>
          <table>
            <thead>
              <tr>
                <th>Resource</th>
                <th>Monthly Cost</th>
              </tr>
            </thead>
            <tbody>
              {result.breakdown.map((item, idx) => (
                <tr key={idx}>
                  <td>{item.resource}</td>
                  <td>${item.monthly_cost}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default App;
```

---

## Data Models

### Estimate

```python
# models.py
from datetime import datetime

class Estimate:
    def __init__(self, estimate_id, total_cost, region, resources, breakdown):
        self.estimate_id = estimate_id
        self.total_cost = total_cost
        self.region = region
        self.resources = resources
        self.breakdown = breakdown
        self.created_at = datetime.utcnow()
```

### SQLite Schema

```sql
CREATE TABLE estimates (
    id TEXT PRIMARY KEY,
    total_monthly_cost REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    region TEXT NOT NULL,
    resources TEXT NOT NULL,  -- JSON
    breakdown TEXT NOT NULL,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_created_at ON estimates(created_at DESC);
```

---

## Deployment

### Docker Setup

**Dockerfile (Backend)**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

**docker-compose.yml**
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - AWS_REGION=us-east-1
    volumes:
      - ./data:/app/data
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Local Development

```bash
# Start all services
docker-compose up -d

# Backend: http://localhost:5000
# Frontend: http://localhost:3000

# Stop services
docker-compose down
```

---

## Testing Strategy

### Unit Tests

```python
# test_calculator.py
import unittest
from calculator import CostCalculator

class TestCostCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = CostCalculator()
    
    def test_ec2_cost_calculation(self):
        cost = self.calculator.calculate_ec2_cost('t3.medium', 'us-east-1')
        self.assertGreater(cost, 0)
        self.assertLess(cost, 100)  # Sanity check
    
    def test_s3_cost_calculation(self):
        cost = self.calculator.calculate_s3_cost(100, 10000)
        expected = (100 * 0.023) + (10000 / 1000 * 0.0004)
        self.assertAlmostEqual(cost, expected, places=2)
```

### Integration Tests

```python
# test_api.py
import unittest
from app import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
    
    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
    
    def test_estimate_endpoint(self):
        data = {
            'files': [
                {
                    'name': 'main.tf',
                    'content': 'resource "aws_instance" "test" { instance_type = "t3.micro" }'
                }
            ],
            'region': 'us-east-1'
        }
        response = self.client.post('/api/v1/estimate', json=data)
        self.assertEqual(response.status_code, 200)
        result = response.json
        self.assertIn('total_monthly_cost', result)
```

---

## Success Metrics

### Functional Metrics
- ✅ Parse 10+ AWS resource types from Terraform
- ✅ Calculate costs with <10% error margin vs AWS Calculator
- ✅ Process estimate in <5 seconds
- ✅ CLI returns results in human-readable format
- ✅ Web UI displays cost breakdown

### Technical Metrics
- API response time: <2 seconds
- Parser success rate: >95%
- Test coverage: >80%
- Zero critical bugs

---

## Development Timeline

### Week 1-2: Core Backend
- Set up project structure
- Implement Terraform parser
- Build cost calculator for EC2, RDS, S3
- Unit tests

### Week 3-4: API & CLI
- Build Flask REST API
- Implement CLI tool
- Integration tests
- Docker setup

### Week 5-6: Web UI
- Build React frontend
- Implement file upload
- Display results
- Basic styling

### Week 7-8: Polish & Testing
- End-to-end testing
- Bug fixes
- Documentation
- Demo preparation

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| AWS Pricing API rate limits | High | Implement caching, use static pricing data as fallback |
| Complex Terraform parsing | Medium | Start with simple resources, expand gradually |
| Inaccurate cost estimates | High | Validate against AWS Calculator, document assumptions |
| Scope creep | Medium | Strict MVP scope, defer features to future phases |

---

## Next Steps After Prototype

1. **User Testing** - Get feedback from 5-10 developers
2. **Accuracy Validation** - Compare estimates with actual AWS bills
3. **Feature Prioritization** - Based on user feedback
4. **Architecture Review** - Plan for scale and multi-cloud
5. **Funding/Resources** - Secure budget for full development

---

## Appendix

### AWS Resources Pricing Reference

| Service | Pricing Model | Complexity |
|---------|--------------|------------|
| EC2 | Hourly, varies by instance type | Medium |
| RDS | Hourly + storage | Medium |
| S3 | Storage + requests | Low |
| EBS | GB-month | Low |
| Lambda | Requests + duration | Medium |
| DynamoDB | Read/write capacity | High |
| Load Balancer | Hourly + data processed | Medium |
| NAT Gateway | Hourly + data processed | Low |

### Required Python Packages

```txt
# requirements.txt
flask==3.0.0
python-hcl2==4.3.2
boto3==1.34.0
redis==5.0.1
click==8.1.7
requests==2.31.0
tabulate==0.9.0
pytest==7.4.3
```

### Environment Variables

```bash
# .env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
DATABASE_PATH=./data/estimates.db
REDIS_URL=redis://localhost:6379
API_PORT=5000
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-03-17  
**Author**: Development Team
