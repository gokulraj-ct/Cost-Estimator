# Kostructure - Infrastructure Cost Governance Platform

**Real-time cost estimation and policy governance for Terraform infrastructure changes via GitHub Pull Requests**

---

## 📋 Table of Contents
- [Vision](#-vision)
- [Current Setup](#-current-setup)
- [What We've Achieved](#-what-weve-achieved)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Features](#-features)
- [Roadmap](#-roadmap)

---

## 🎯 Vision

**The Problem:**
- Infrastructure changes can lead to unexpected cloud costs
- No visibility into cost impact before deployment
- Policy violations discovered too late
- Manual cost estimation is time-consuming and error-prone

**Our Solution:**
Kostructure provides **automated cost estimation and policy governance** directly in GitHub Pull Requests, giving teams instant feedback on infrastructure changes before they're deployed.

**Future Vision:**
- Multi-cloud support (AWS, GCP, Azure)
- AI-powered cost optimization recommendations
- Historical cost trend analysis
- Team budget allocation and tracking
- Integration with CI/CD pipelines

---

## 🏗️ Current Setup

### Architecture Overview
```
GitHub PR → Webhook → GitHub Bot → API Gateway
                                        ↓
                    ┌──────────────────┼──────────────────┐
                    ↓                  ↓                  ↓
              Parser Service    Cost Service      Policy Service
                  (Go)            (Python)           (Python)
                    ↓                  ↓                  ↓
                    └──────────────────┴──────────────────┘
                                       ↓
                              PostgreSQL + Redis
```

### Services

1. **API Gateway** (Python/Flask)
   - Central orchestration layer
   - Database management
   - REST API endpoints
   - Per-repository integration management

2. **Parser Service** (Go)
   - Terraform file parsing
   - Resource extraction
   - Fast and efficient

3. **Cost Service** (Python)
   - Plugin-based cost calculation
   - AWS Pricing API integration
   - Fallback static pricing
   - 6 resource type plugins

4. **Policy Service** (Python)
   - Policy validation engine
   - Security, cost, budget, compliance checks
   - Configurable rules

5. **GitHub Bot** (Python)
   - Webhook handler
   - PR comment posting
   - Integration with GitHub API

6. **Frontend** (React/Next.js)
   - Dashboard for viewing estimates
   - Policy management UI
   - Integration configuration

### Database Schema
- **integrations**: Per-repo GitHub tokens and settings
- **policies**: Configurable governance rules
- **pr_estimates**: Historical cost estimates
- **estimate_resources**: Per-resource cost breakdown

---

## ✅ What We've Achieved

### Core Features Implemented

#### 1. Cost Estimation ✅
- **6 AWS Resource Types Supported:**
  - EC2 Instances (t3, t2, m5, c5 families)
  - RDS Databases (PostgreSQL, MySQL, etc.)
  - S3 Buckets
  - EBS Volumes (gp2, gp3, io1, io2)
  - ElastiCache Clusters (Redis, Memcached)
  - Application Load Balancers

- **Pricing Modes:**
  - Real-time AWS Pricing API (when credentials available)
  - Fallback static pricing (works without AWS credentials)
  - Per-region pricing support

- **Cost Breakdown:**
  - Total monthly cost
  - Per-resource cost details
  - Instance type and configuration info

#### 2. Policy Governance ✅
- **10 Built-in Policies:**
  
  **Security (5 policies):**
  - SEC-001: No public S3 buckets
  - SEC-002: S3 encryption required
  - SEC-003: No public EC2 instances
  - SEC-004: RDS encryption required
  - SEC-005: RDS public access disabled
  
  **Cost (2 policies):**
  - COST-001: EC2 instance size limits
  - COST-002: RDS instance size limits
  
  **Budget (2 policies):**
  - BUDGET-001: Development monthly limit ($100)
  - BUDGET-002: Production monthly limit ($500)
  
  **Compliance (1 policy):**
  - COMP-001: Required tags (Environment, Owner, Project)

- **Policy Features:**
  - Enable/disable per policy
  - Configurable severity levels (low, medium, high, critical)
  - JSON-based configuration
  - Category-based organization

#### 3. GitHub Integration ✅
- **Webhook Support:**
  - Automatic PR comment posting
  - Real-time cost estimates on PR open/update
  - Policy violation warnings

- **Per-Repository Configuration:**
  - Custom GitHub tokens per repo
  - Default region settings
  - Repository-specific descriptions
  - Multiple repo support

- **PR Comments Include:**
  - Total monthly cost
  - Per-resource breakdown
  - Policy violations by severity
  - Visual formatting with emojis

#### 4. Plugin System ✅
- **Extensible Architecture:**
  - Base plugin interface
  - Easy to add new resource types
  - Automatic plugin registration
  - Fallback pricing support

- **Current Plugins:**
  - EC2Plugin
  - RDSPlugin
  - S3Plugin
  - LoadBalancerPlugin
  - ElastiCachePlugin
  - EBSPlugin

#### 5. Budget Enforcement ✅
- **Monthly Cost Limits:**
  - Set per-environment budgets
  - Automatic violation detection
  - Configurable thresholds
  - Critical alerts for overages

#### 6. Infrastructure ✅
- **Containerized Deployment:**
  - Docker Compose orchestration
  - 6 microservices
  - PostgreSQL database
  - Redis caching
  - Health checks

- **Configuration:**
  - Environment-based config
  - Secrets management
  - AWS credentials support
  - Per-service configuration

---

## 🏛️ Architecture

### Plugin System
```python
class ResourcePlugin:
    @property
    def resource_type(self) -> str
    
    @property
    def display_name(self) -> str
    
    def calculate_cost(self, attributes, region) -> float
```

### Cost Calculation Flow
1. GitHub webhook triggers on PR
2. Parser extracts Terraform resources
3. Cost service calculates per-resource costs
4. Policy service validates against rules
5. Results saved to database
6. GitHub bot posts PR comment

### Policy Validation
- Policies loaded from database
- Applied to matching resource types
- Violations categorized by severity
- Budget policies check total cost

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- GitHub account
- (Optional) AWS credentials for real-time pricing

### Installation

1. **Clone Repository**
```bash
git clone https://github.com/gokulraj-ct/Cost-Estimator.git
cd Cost-Estimator
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your values:
# - POSTGRES_PASSWORD
# - GITHUB_TOKEN
# - GITHUB_WEBHOOK_SECRET
```

3. **Start Services**
```bash
docker-compose up -d
```

4. **Access Dashboard**
```
http://localhost:3000
```

5. **Configure GitHub Webhook**
- Go to repo → Settings → Webhooks → Add webhook
- Payload URL: `http://your-server:8003/webhook`
- Content type: `application/json`
- Events: Pull requests
- Secret: (your GITHUB_WEBHOOK_SECRET)

### Add Repository Integration

```bash
curl -X POST http://localhost:8000/api/v1/integrations \
  -H "Content-Type: application/json" \
  -d '{
    "repo_full_name": "user/repo",
    "github_token": "ghp_xxx",
    "default_region": "us-east-1",
    "description": "Production infrastructure"
  }'
```

---

## 🎨 Features

### Cost Estimation
- ✅ Real-time AWS pricing
- ✅ Fallback static pricing
- ✅ Per-resource breakdown
- ✅ Monthly cost totals
- ✅ Region-specific pricing

### Policy Governance
- ✅ Security policies
- ✅ Cost policies
- ✅ Budget policies
- ✅ Compliance policies
- ✅ Configurable rules
- ✅ Severity levels

### GitHub Integration
- ✅ Webhook support
- ✅ PR comments
- ✅ Per-repo configuration
- ✅ Multiple repo support

### Plugin System
- ✅ Extensible architecture
- ✅ 6 resource types
- ✅ Easy to add new plugins
- ✅ Fallback pricing

### Infrastructure
- ✅ Microservices architecture
- ✅ Docker containerization
- ✅ PostgreSQL database
- ✅ Redis caching
- ✅ Health checks

---

## 🗺️ Roadmap

### Phase 1: Multi-Cloud Support (8 weeks)
- [ ] Cloud provider abstraction layer
- [ ] GCP support (Compute Engine, Cloud Storage, Cloud SQL)
- [ ] Azure support (VMs, Storage, SQL Database)
- [ ] Multi-cloud cost comparison
- [ ] Cross-cloud policy enforcement

### Phase 2: Advanced Features (6 weeks)
- [ ] Historical cost trend analysis
- [ ] Cost optimization recommendations
- [ ] Budget allocation by team/project
- [ ] Slack/Teams notifications
- [ ] Email alerts

### Phase 3: AI & Analytics (8 weeks)
- [ ] AI-powered cost predictions
- [ ] Anomaly detection
- [ ] Resource right-sizing recommendations
- [ ] Cost forecasting
- [ ] Usage pattern analysis

### Phase 4: Enterprise Features (6 weeks)
- [ ] SSO/SAML authentication
- [ ] Role-based access control
- [ ] Audit logging
- [ ] Custom policy creation UI
- [ ] API rate limiting
- [ ] Multi-tenancy

### Phase 5: CI/CD Integration (4 weeks)
- [ ] Jenkins plugin
- [ ] GitLab CI integration
- [ ] CircleCI integration
- [ ] GitHub Actions
- [ ] Terraform Cloud integration

---

## 📊 Example Output

### PR Comment
```
💰 Kostructure Cost Estimate

📊 Total Monthly Cost: $176.10

📦 Resources (8):
- aws_instance.web (t3.medium): $30.37
- aws_instance.app (t3.large): $60.74
- aws_db_instance.database (db.t3.small): $27.12
- aws_elasticache_cluster.redis: $12.41
- aws_lb.main: $32.86
- aws_ebs_volume.data (100GB gp3): $8.00
- aws_s3_bucket.data: $2.30
- aws_s3_bucket.logs: $2.30

⚠️ Policy Violations (1)

Budget:
- Monthly Cost Limit - Development (BUDGET-001)
  Total cost $176.10 exceeds limit $100.00
```

---

## 🛠️ Technology Stack

- **Backend:** Python (Flask), Go
- **Frontend:** React, Next.js, TypeScript
- **Database:** PostgreSQL
- **Cache:** Redis
- **Containerization:** Docker, Docker Compose
- **Cloud:** AWS (with GCP/Azure planned)

---

## 📝 Configuration

### Update Budget Limits
```bash
curl -X PUT http://localhost:8000/api/v1/policies/BUDGET-001 \
  -H "Content-Type: application/json" \
  -d '{"config": {"monthly_limit": 200}}'
```

### Enable/Disable Policies
```bash
curl -X PUT http://localhost:8000/api/v1/policies/SEC-001 \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

---

## 🤝 Contributing

We welcome contributions! Areas where you can help:
- Add new resource type plugins
- Improve cost calculation accuracy
- Add GCP/Azure support
- Enhance UI/UX
- Write tests
- Improve documentation

---

## 📄 License

MIT License

---

**Built with ❤️ for Infrastructure Engineers**
