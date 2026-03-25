# Kostructure - High-Level Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         KOSTRUCTURE PLATFORM                             │
│                   AWS Infrastructure Cost Estimator                      │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACES                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  Web UI     │  │  CLI Tool   │  │  GitHub Bot │  │  REST API   │   │
│  │  (Port 3000)│  │  (Binary)   │  │  (Webhook)  │  │  (Direct)   │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                │                │                │            │
│         └────────────────┴────────────────┴────────────────┘            │
│                                  │                                       │
└──────────────────────────────────┼───────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (Port 8000)                          │
├──────────────────────────────────────────────────────────────────────────┤
│  • Request routing                                                        │
│  • Database operations (PostgreSQL)                                       │
│  • Cost history storage                                                   │
│  • Response aggregation                                                   │
└────────────┬─────────────────────────────────────┬───────────────────────┘
             │                                     │
             ▼                                     ▼
┌────────────────────────────┐      ┌────────────────────────────────────┐
│  PARSER SERVICE (Port 8001)│      │  COST SERVICE (Port 8002)          │
├────────────────────────────┤      ├────────────────────────────────────┤
│  • Terraform parsing (Go)  │      │  • Cost calculation (Python)       │
│  • HCL syntax analysis     │      │  • AWS Pricing API integration     │
│  • Resource extraction     │      │  • Plugin architecture             │
│  • Region detection        │      │  • Fallback pricing                │
│  • Validation              │      │  • Multi-region support            │
└────────────┬───────────────┘      └────────────┬───────────────────────┘
             │                                   │
             │                                   │
             └───────────┬───────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         DATA & CACHE LAYER                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────┐         ┌──────────────────────────┐       │
│  │  PostgreSQL (Port 5432) │         │  Redis (Port 6379)       │       │
│  ├─────────────────────────┤         ├──────────────────────────┤       │
│  │  • Cost estimates       │         │  • Parsing cache         │       │
│  │  • History tracking     │         │  • Rate limiting         │       │
│  │  • Metadata storage     │         │  • Session data          │       │
│  └─────────────────────────┘         └──────────────────────────┘       │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL INTEGRATIONS                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │  AWS Pricing API │    │  GitHub API      │    │  ngrok Tunnel    │  │
│  │  (us-east-1)     │    │  (Webhooks)      │    │  (Public URL)    │  │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘  │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. User Interfaces

#### Web UI (Port 3000)
- **Technology**: HTML, CSS, JavaScript, Chart.js
- **Features**:
  - Multi-file drag & drop upload
  - Interactive cost charts (doughnut, bar)
  - Cost history tracking
  - Region comparison
  - Optimization suggestions
  - CSV export
- **Access**: http://localhost:3000

#### CLI Tool
- **Technology**: Go
- **Features**:
  - Local file analysis
  - Terminal output
  - Batch processing
- **Usage**: `./kostructure estimate --path <file>`

#### GitHub Bot (Port 8003)
- **Technology**: Python Flask
- **Features**:
  - Webhook handler
  - PR comment posting
  - Automatic cost estimates on PRs
  - Signature verification
- **Trigger**: Pull request events

#### REST API
- **Direct access** to API Gateway
- **Authentication**: Optional API keys
- **Rate limiting**: Configurable

---

### 2. Core Services

#### API Gateway (Port 8000)
- **Technology**: Python Flask
- **Responsibilities**:
  - Route requests to microservices
  - Aggregate responses
  - Database operations
  - Cost history management
- **Endpoints**:
  - `POST /api/v1/estimate` - Calculate costs
  - `GET /api/v1/estimates` - Get history
  - `GET /api/v1/estimates/<id>` - Get specific estimate
  - `GET /health` - Health check

#### Parser Service (Port 8001)
- **Technology**: Go
- **Responsibilities**:
  - Parse Terraform HCL files
  - Extract AWS resources
  - Detect regions from provider blocks
  - Validate syntax
  - Cache parsed results
- **Output**: Structured resource list with attributes

#### Cost Service (Port 8002)
- **Technology**: Python
- **Responsibilities**:
  - Calculate monthly costs
  - Query AWS Pricing API
  - Fallback to static pricing
  - Plugin-based architecture
  - Multi-region support
- **Plugins**:
  - EC2 (aws_instance)
  - RDS (aws_db_instance)
  - S3 (aws_s3_bucket)
  - Load Balancer (aws_lb)

---

### 3. Data Layer

#### PostgreSQL (Port 5432)
- **Schema**:
  ```sql
  estimates (
    id VARCHAR PRIMARY KEY,
    total_monthly_cost DECIMAL,
    currency VARCHAR,
    region VARCHAR,
    resources JSONB,
    breakdown JSONB,
    resource_count INTEGER,
    created_at TIMESTAMP
  )
  ```

#### Redis (Port 6379)
- **Usage**:
  - Parsing cache (TTL: 1 hour)
  - Rate limiting counters
  - Session storage

---

### 4. External Integrations

#### AWS Pricing API
- **Region**: us-east-1
- **Purpose**: Real-time pricing data
- **Fallback**: Static pricing when unavailable
- **Credentials**: AWS access keys (optional)

#### GitHub API
- **Purpose**: 
  - Fetch PR files
  - Post comments
  - Webhook verification
- **Authentication**: GitHub token

#### ngrok
- **Purpose**: Expose local bot to GitHub webhooks
- **URL**: Dynamic (changes on restart)
- **Usage**: Development/testing

---

## Data Flow

### Cost Estimation Flow

```
┌─────────┐
│  User   │
└────┬────┘
     │ 1. Upload .tf files
     ▼
┌─────────────────┐
│   API Gateway   │
└────┬────────────┘
     │ 2. Send files
     ▼
┌─────────────────┐
│ Parser Service  │ ──────► Redis (Cache)
└────┬────────────┘
     │ 3. Return resources
     ▼
┌─────────────────┐
│   API Gateway   │
└────┬────────────┘
     │ 4. Send resources
     ▼
┌─────────────────┐
│  Cost Service   │ ──────► AWS Pricing API
└────┬────────────┘
     │ 5. Return costs
     ▼
┌─────────────────┐
│   API Gateway   │ ──────► PostgreSQL (Save)
└────┬────────────┘
     │ 6. Return estimate
     ▼
┌─────────┐
│  User   │
└─────────┘
```

### GitHub Bot Flow

```
┌──────────────┐
│  Developer   │
└──────┬───────┘
       │ 1. Create/Update PR
       ▼
┌──────────────┐
│    GitHub    │
└──────┬───────┘
       │ 2. Send webhook
       ▼
┌──────────────┐
│    ngrok     │
└──────┬───────┘
       │ 3. Forward to bot
       ▼
┌──────────────┐
│ GitHub Bot   │
└──────┬───────┘
       │ 4. Fetch .tf files
       ▼
┌──────────────┐
│    GitHub    │
└──────┬───────┘
       │ 5. Return files
       ▼
┌──────────────┐
│ GitHub Bot   │
└──────┬───────┘
       │ 6. Call estimate API
       ▼
┌──────────────┐
│ API Gateway  │ ──► Parser ──► Cost Service
└──────┬───────┘
       │ 7. Return estimate
       ▼
┌──────────────┐
│ GitHub Bot   │
└──────┬───────┘
       │ 8. Post comment
       ▼
┌──────────────┐
│    GitHub    │
└──────┬───────┘
       │ 9. Comment appears
       ▼
┌──────────────┐
│  Developer   │
└──────────────┘
```

---

## Technology Stack

### Backend
- **Python 3.11**: API Gateway, Cost Service, GitHub Bot
- **Go 1.21**: Parser Service, CLI Tool
- **Flask**: Web framework
- **PostgreSQL 16**: Database
- **Redis 7**: Cache & rate limiting

### Frontend
- **HTML5/CSS3**: Web UI structure
- **JavaScript (Vanilla)**: Interactivity
- **Chart.js 4.4**: Data visualization

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Orchestration
- **ngrok**: Local tunnel

### External APIs
- **AWS Pricing API**: Real-time pricing
- **GitHub API**: PR integration

---

## Key Features Implemented

### ✅ Core Functionality
1. Terraform file parsing (HCL)
2. AWS resource cost calculation
3. Multi-region support
4. Cost history tracking
5. Region detection from provider blocks

### ✅ User Experience
1. Web UI with charts
2. Multi-file upload (drag & drop)
3. Cost breakdown visualization
4. CSV export
5. Responsive design

### ✅ Integrations
1. GitHub PR comments
2. Webhook handling
3. AWS Pricing API
4. Fallback pricing

### ✅ Advanced Features
1. Region comparison
2. Cost optimization suggestions
3. Plugin architecture
4. Caching layer
5. Database persistence

### ✅ Developer Tools
1. CLI tool
2. REST API
3. Health checks
4. Error handling

---

## Deployment Architecture

### Development (Current)
```
┌─────────────────────────────────────┐
│         Local Machine               │
├─────────────────────────────────────┤
│  Docker Containers:                 │
│  • api-gateway                      │
│  • parser-service                   │
│  • cost-service                     │
│  • github-bot                       │
│  • postgres                         │
│  • redis                            │
│  • web                              │
├─────────────────────────────────────┤
│  ngrok → GitHub Webhooks            │
└─────────────────────────────────────┘
```

### Production (Recommended)
```
┌─────────────────────────────────────────────┐
│              AWS Cloud                      │
├─────────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐   │
│  │  Application Load Balancer          │   │
│  └────────────┬────────────────────────┘   │
│               │                             │
│  ┌────────────┴────────────────────────┐   │
│  │  ECS/Fargate Cluster                │   │
│  │  • API Gateway (Auto-scaling)       │   │
│  │  • Parser Service (Auto-scaling)    │   │
│  │  • Cost Service (Auto-scaling)      │   │
│  │  • GitHub Bot (Single instance)     │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  RDS PostgreSQL (Multi-AZ)          │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  ElastiCache Redis (Cluster)        │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  S3 (Static web assets)             │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  CloudFront (CDN)                   │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## Security Features

### Implemented
- ✅ CORS enabled
- ✅ Environment variables for secrets
- ✅ GitHub webhook signature verification
- ✅ Database connection pooling
- ✅ Input validation

### Available (Disabled by default)
- API key authentication
- Rate limiting (Redis-based)
- JWT tokens (ready to implement)

---

## Performance Optimizations

1. **Caching**: Redis caches parsed Terraform files (1 hour TTL)
2. **Connection Pooling**: PostgreSQL connection reuse
3. **Async Processing**: Non-blocking API calls
4. **Fallback Pricing**: Static pricing when AWS API unavailable
5. **Microservices**: Independent scaling of components

---

## Monitoring & Observability

### Health Checks
- `/health` endpoint on all services
- Docker health checks
- Service dependency checks

### Logging
- Container logs via Docker
- Flask debug mode (development)
- Error tracking in responses

---

## Future Enhancements

### Planned
1. User authentication & authorization
2. Multi-cloud support (Azure, GCP)
3. Cost alerts & notifications
4. Terraform state file support
5. CI/CD pipeline integration
6. Advanced analytics dashboard
7. Cost forecasting
8. Budget tracking
9. Team collaboration features
10. Terraform plan integration

---

## Port Reference

| Service        | Port | Protocol | Purpose                |
|----------------|------|----------|------------------------|
| Web UI         | 3000 | HTTP     | User interface         |
| API Gateway    | 8000 | HTTP     | Main API               |
| Parser Service | 8001 | HTTP     | Terraform parsing      |
| Cost Service   | 8002 | HTTP     | Cost calculation       |
| GitHub Bot     | 8003 | HTTP     | Webhook handler        |
| PostgreSQL     | 5432 | TCP      | Database               |
| Redis          | 6379 | TCP      | Cache & rate limiting  |
| ngrok          | 4040 | HTTP     | Tunnel web interface   |

---

## Environment Variables

### Required
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `REDIS_HOST`, `REDIS_PORT`

### Optional
- `GITHUB_TOKEN` - For GitHub bot
- `GITHUB_WEBHOOK_SECRET` - For webhook verification
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` - For AWS Pricing API
- `USE_AWS_PRICING` - Enable/disable AWS API (true/false)
- `DISABLE_AUTH` - Disable authentication (true/false)
- `DISABLE_RATE_LIMIT` - Disable rate limiting (true/false)

---

**Built with ❤️ for AWS infrastructure cost transparency**
