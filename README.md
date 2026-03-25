# Kostructure 🏗️

**Infrastructure Cost Governance Platform**

Kostructure provides real-time cost estimation and policy governance for Terraform infrastructure changes via GitHub Pull Requests.

## 🚀 Features

- **💰 Cost Estimation**: Calculate monthly costs for AWS resources (EC2, RDS, S3, EBS, ElastiCache, Load Balancers)
- **🔒 Policy Governance**: Enforce security, cost, compliance, and budget policies
- **🔗 GitHub Integration**: Automatic PR comments with cost estimates and policy violations
- **📊 Per-Repository Configuration**: Custom tokens, regions, and settings per repo
- **💵 Budget Enforcement**: Set monthly cost limits and get violations
- **🌐 Multi-Cloud Ready**: Architecture designed for AWS, GCP, and Azure support
- **🔌 Plugin System**: Extensible cost calculation plugins
- **⚡ Fallback Pricing**: Works without AWS credentials using static pricing

## 📋 Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   GitHub    │────▶│  GitHub Bot  │────▶│ API Gateway │
│     PR      │     │   (Webhook)  │     │   (Flask)   │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                    ┌───────────────────────────┼───────────────────────┐
                    ▼                           ▼                       ▼
            ┌──────────────┐          ┌──────────────┐       ┌──────────────┐
            │    Parser    │          │     Cost     │       │    Policy    │
            │   Service    │          │   Service    │       │   Service    │
            │     (Go)     │          │   (Python)   │       │   (Python)   │
            └──────────────┘          └──────────────┘       └──────────────┘
                    │                           │                       │
                    └───────────────────────────┴───────────────────────┘
                                                │
                                        ┌───────┴────────┐
                                        ▼                ▼
                                  ┌──────────┐    ┌─────────┐
                                  │PostgreSQL│    │  Redis  │
                                  └──────────┘    └─────────┘
```

## 🛠️ Services

- **API Gateway**: Central API, database management, orchestration
- **Parser Service**: Terraform file parsing (Go)
- **Cost Service**: AWS cost calculation with plugin system
- **Policy Service**: Policy validation engine
- **GitHub Bot**: Webhook handler and PR comment poster
- **Frontend**: React dashboard for viewing estimates and policies

## 🏃 Quick Start

### Prerequisites
- Docker & Docker Compose
- GitHub account with a repository
- (Optional) AWS credentials for real-time pricing

### 1. Clone Repository
```bash
git clone https://github.com/gokulraj-ct/kostructure.git
cd kostructure
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Access Dashboard
```
http://localhost:3000
```

### 5. Configure GitHub Webhook
1. Go to your repo → Settings → Webhooks → Add webhook
2. Payload URL: `http://your-server:8003/webhook`
3. Content type: `application/json`
4. Events: Pull requests
5. Add webhook

## 📊 Cost Estimation Example

```hcl
resource "aws_instance" "web" {
  instance_type = "t3.medium"
}

resource "aws_db_instance" "database" {
  instance_class = "db.t3.small"
  allocated_storage = 20
}
```

**Result**: PR comment with:
- Total monthly cost: $57.49
- Per-resource breakdown
- Policy violations (if any)
- Budget warnings

## 🔒 Policy Types

### Security Policies
- No public S3 buckets
- S3 encryption required
- No public EC2 instances
- RDS encryption required
- RDS public access disabled

### Cost Policies
- EC2 instance size limits
- RDS instance size limits

### Budget Policies
- Monthly cost limits (Development: $100, Production: $500)

### Compliance Policies
- Required tags (Environment, Owner, Project)

## 🔌 Plugin System

Add new resource types easily:

```python
class MyResourcePlugin(ResourcePlugin):
    @property
    def resource_type(self) -> str:
        return 'aws_my_resource'
    
    def calculate_cost(self, attributes, region):
        # Your cost calculation logic
        return monthly_cost
```

## 🌐 Multi-Cloud Support (Roadmap)

- ✅ AWS (Current)
- 🔄 GCP (Planned)
- 🔄 Azure (Planned)

See [MULTI_CLOUD_ARCHITECTURE.md](MULTI_CLOUD_ARCHITECTURE.md) for details.

## 📁 Project Structure

```
kostructure/
├── services/
│   ├── api-gateway/       # Central API (Python/Flask)
│   ├── parser-service/    # Terraform parser (Go)
│   ├── cost-service/      # Cost calculation (Python)
│   ├── policy-service/    # Policy validation (Python)
│   └── github-bot/        # Webhook handler (Python)
├── web/                   # React frontend
├── docker-compose.yml     # Service orchestration
└── README.md
```

## 🔧 Configuration

### Per-Repository Integration

```bash
# Add integration via API
curl -X POST http://localhost:8000/api/v1/integrations \
  -H "Content-Type: application/json" \
  -d '{
    "repo_full_name": "user/repo",
    "github_token": "ghp_xxx",
    "default_region": "us-east-1",
    "description": "Production infrastructure"
  }'
```

### Budget Policies

```bash
# Update budget limit
curl -X PUT http://localhost:8000/api/v1/policies/BUDGET-001 \
  -H "Content-Type: application/json" \
  -d '{"config": {"monthly_limit": 200}}'
```

## 📖 Documentation

- [Architecture](ARCHITECTURE.md)
- [Plugin System](PLUGIN-SYSTEM.md)
- [GitHub Integration](GITHUB-INTEGRATION.md)
- [Multi-Cloud Architecture](MULTI_CLOUD_ARCHITECTURE.md)
- [Features](FEATURES.md)

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines.

## 📄 License

MIT License

## 🙏 Acknowledgments

Built with:
- Flask (Python)
- Go
- React
- PostgreSQL
- Redis
- Docker

---

**Made with ❤️ for Infrastructure Engineers**
