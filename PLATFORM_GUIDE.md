# Kostructure - Complete Governance Platform

## Overview
Kostructure is now a complete AWS infrastructure governance platform with cost estimation, policy management, and PR integration.

## Architecture

### Services
1. **API Gateway** (Port 8000)
   - Central API hub
   - Database management
   - Policy CRUD operations
   - PR estimate tracking

2. **Cost Service** (Port 8002)
   - AWS Pricing API integration
   - Real-time cost calculation
   - Multi-region support

3. **Parser Service** (Port 8001)
   - Terraform file parsing
   - Resource extraction
   - Go-based for performance

4. **Policy Service** (Port 8004)
   - Policy validation engine
   - Database-driven policies
   - 8 built-in policies

5. **GitHub Bot** (Port 8003)
   - Webhook handler
   - PR comment automation
   - Estimate tracking

### Databases
- **PostgreSQL**: Policies, estimates, PR tracking
- **Redis**: Caching layer

## Features

### 1. Cost Estimation
- Upload Terraform files or paste code
- Real-time AWS pricing
- Multi-region comparison
- Cost optimization suggestions
- Historical tracking

### 2. Policy Governance
**8 Built-in Policies:**

**Security (5 policies):**
- SEC-001: No Public S3 Buckets (High)
- SEC-002: S3 Encryption Required (High)
- SEC-003: No Public EC2 Instances (Medium)
- SEC-004: RDS Encryption Required (High)
- SEC-005: RDS Public Access Disabled (Critical)

**Cost (2 policies):**
- COST-001: EC2 Instance Size Limit (Medium)
- COST-002: RDS Instance Size Limit (Medium)

**Compliance (1 policy):**
- COMP-001: Required Tags Present (Low)

### 3. Web UI (Port 3000)
**Tabs:**
- Cost Estimate: Upload files, get estimates
- Region Comparison: Compare costs across regions
- Optimization: Get cost-saving recommendations
- **Policies**: Manage governance policies
- **PR Estimates**: View all PR cost estimates
- History: Track past estimates

### 4. GitHub Integration
- Automatic PR comments with:
  - Cost estimates
  - Cost comparison (vs base branch)
  - Policy violations (grouped by severity)
  - Resource breakdown
- PR estimates saved to database
- Visible in web UI

## Usage

### For Developers
1. Create PR with Terraform changes
2. Bot automatically comments with cost + policy violations
3. Fix violations before merge

### For Platform Teams
1. Open http://localhost:3000
2. Go to "Policies" tab
3. Enable/disable policies as needed
4. Changes apply immediately to new PRs

### For Stakeholders
1. Open http://localhost:3000
2. Go to "PR Estimates" tab
3. View all PR costs and violations
4. Click PR links to review on GitHub

## API Endpoints

### Cost Estimation
- `POST /api/v1/estimate` - Calculate cost
- `GET /api/v1/estimates` - List estimates

### Policy Management
- `GET /api/v1/policies` - List all policies
- `PUT /api/v1/policies/{id}` - Update policy (enable/disable)

### PR Tracking
- `GET /api/v1/pr-estimates` - List PR estimates
- `POST /api/v1/pr-estimates` - Save PR estimate

### GitHub Webhook
- `POST /webhook` - GitHub PR webhook

## Database Schema

### policies
- id, name, description
- severity, category, resource_type
- enabled (boolean)
- config (JSONB)

### estimates
- id, total_monthly_cost, currency
- region, resources, breakdown
- resource_count, created_at

### pr_estimates
- id, estimate_id (FK)
- repo_full_name, pr_number
- pr_title, pr_url
- policy_violations (JSONB)
- created_at

## Configuration

### Environment Variables
- `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `REDIS_HOST`, `REDIS_PORT`
- `GITHUB_TOKEN`, `GITHUB_WEBHOOK_SECRET`
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`

### Service URLs
- API Gateway: http://localhost:8000
- Parser: http://localhost:8001
- Cost: http://localhost:8002
- GitHub Bot: http://localhost:8003
- Policy: http://localhost:8004
- Web UI: http://localhost:3000

## Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart api-gateway

# Rebuild after code changes
docker-compose up -d --build
```

## Key Workflows

### 1. Policy Update Workflow
1. User opens web UI → Policies tab
2. Toggles policy on/off
3. API Gateway updates database
4. Policy Service reads from database (cached 60s)
5. Next PR uses updated policies

### 2. PR Review Workflow
1. Developer creates PR with Terraform
2. GitHub sends webhook to bot
3. Bot fetches Terraform files
4. Bot calls API Gateway for estimate
5. API Gateway → Parser → Cost + Policy services
6. Bot posts comment with results
7. Bot saves estimate to database
8. Estimate visible in web UI

### 3. Stakeholder Review Workflow
1. Stakeholder opens web UI
2. Goes to PR Estimates tab
3. Sees all PRs with costs and violations
4. Clicks PR link to review
5. Can adjust policies if needed

## Benefits

✅ **Cost Visibility**: Know infrastructure costs before deployment
✅ **Policy Enforcement**: Automated security and compliance checks
✅ **Stakeholder Control**: Non-technical users can manage policies
✅ **PR Integration**: Seamless GitHub workflow
✅ **Unified Dashboard**: Everything in one place
✅ **Real-time Pricing**: Always up-to-date AWS costs
✅ **Flexible Policies**: Enable/disable as needed

## Future Enhancements
- Custom policy creation
- Policy templates
- Cost budgets and alerts
- Slack/Teams notifications
- Multi-cloud support (Azure, GCP)
- Policy exceptions/overrides
- Approval workflows
