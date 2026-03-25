# Backend Request Flow - Step by Step

## Example: Estimating Cost for a Terraform File

Let's trace what happens when you run:
```bash
./cli/kostructure estimate --path examples/production.tf
```

---

## Step-by-Step Flow

### Step 1: CLI Reads File
```
📁 CLI (Go)
├─ Reads: examples/production.tf
├─ Content:
│  resource "aws_instance" "web1" { instance_type = "t3.large" }
│  resource "aws_db_instance" "prod_db" { instance_class = "db.t3.large", allocated_storage = 200 }
│  ...
└─ Prepares JSON payload
```

**Output:**
```json
{
  "files": [
    {
      "name": "production.tf",
      "content": "resource \"aws_instance\" \"web1\" { ... }"
    }
  ],
  "region": "us-east-1"
}
```

---

### Step 2: CLI → API Gateway
```
🌐 HTTP POST Request
├─ URL: http://localhost:8000/api/v1/estimate
├─ Method: POST
├─ Headers: Content-Type: application/json
└─ Body: { files: [...], region: "us-east-1" }
```

**Time: ~10ms**

---

### Step 3: API Gateway Receives Request
```
🔧 API Gateway (Python/Flask) - Port 8000
├─ Endpoint: /api/v1/estimate
├─ Validates request
├─ Extracts: files, region
└─ Logs: "Received estimate request with 1 file(s)"
```

**Code executed:**
```python
@app.route('/api/v1/estimate', methods=['POST'])
def estimate():
    data = request.json
    files = data.get('files', [])
    region = data.get('region', 'us-east-1')
```

---

### Step 4: API Gateway → Parser Service
```
📡 Internal HTTP Request
├─ From: API Gateway (8000)
├─ To: Parser Service (8001)
├─ URL: http://parser-service:8001/api/v1/parse
└─ Body: { files: [...], region: "us-east-1" }
```

**Code executed:**
```python
parse_response = requests.post(
    f'{PARSER_SERVICE}/api/v1/parse',
    json={'files': files, 'region': region}
)
```

**Time: ~50ms**

---

### Step 5: Parser Service Processes
```
⚙️ Parser Service (Go) - Port 8001
├─ Receives Terraform content
├─ Uses regex to extract resources:
│  ├─ Finds: resource "aws_instance" "web1"
│  ├─ Extracts: type=aws_instance, name=web1
│  ├─ Attributes: instance_type="t3.large"
│  └─ Repeats for all resources
└─ Returns normalized JSON
```

**Processing:**
```go
// Regex matches resource blocks
resourceRegex := regexp.MustCompile(`resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([^}]*)\}`)
matches := resourceRegex.FindAllStringSubmatch(content, -1)

// For each match:
// - Extract type (aws_instance)
// - Extract name (web1)
// - Parse attributes (instance_type = "t3.large")
```

**Output:**
```json
{
  "resources": [
    {
      "type": "aws_instance",
      "name": "web1",
      "attributes": { "instance_type": "t3.large" },
      "region": "us-east-1"
    },
    {
      "type": "aws_instance",
      "name": "web2",
      "attributes": { "instance_type": "t3.large" },
      "region": "us-east-1"
    },
    {
      "type": "aws_db_instance",
      "name": "prod_db",
      "attributes": {
        "instance_class": "db.t3.large",
        "allocated_storage": "200"
      },
      "region": "us-east-1"
    },
    ...
  ],
  "count": 7
}
```

**Time: ~100ms**

---

### Step 6: API Gateway → Cost Service
```
📡 Internal HTTP Request
├─ From: API Gateway (8000)
├─ To: Cost Service (8002)
├─ URL: http://cost-service:8002/api/v1/calculate
└─ Body: { resources: [...], region: "us-east-1" }
```

**Code executed:**
```python
cost_response = requests.post(
    f'{COST_SERVICE}/api/v1/calculate',
    json={'resources': resources, 'region': region}
)
```

**Time: ~30ms**

---

### Step 7: Cost Service Calculates
```
💰 Cost Service (Python) - Port 8002
├─ Receives parsed resources
├─ For each resource:
│  ├─ aws_instance.web1 (t3.large)
│  │  ├─ Lookup: PRICING['ec2']['t3.large'] = $0.0832/hour
│  │  ├─ Calculate: $0.0832 × 730 hours = $60.74/month
│  │  └─ Add to breakdown
│  │
│  ├─ aws_db_instance.prod_db (db.t3.large, 200GB)
│  │  ├─ Instance: $0.136/hour × 730 = $99.28
│  │  ├─ Storage: 200GB × $0.115 = $23.00
│  │  ├─ Total: $122.28/month
│  │  └─ Add to breakdown
│  │
│  └─ ... (repeat for all 7 resources)
│
└─ Sum total: $299.83/month
```

**Processing:**
```python
def calculate_ec2_cost(attrs):
    instance_type = attrs.get('instance_type', 't3.micro')
    hourly = PRICING['ec2'].get(instance_type, 0.0416)
    monthly = hourly * 730
    return monthly

def calculate_rds_cost(attrs):
    instance_class = attrs.get('instance_class', 'db.t3.micro')
    storage = int(attrs.get('allocated_storage', 20))
    hourly = PRICING['rds'].get(instance_class, 0.034)
    monthly = hourly * 730
    monthly += storage * 0.115  # Storage cost
    return monthly
```

**Output:**
```json
{
  "total_monthly_cost": 299.83,
  "currency": "USD",
  "region": "us-east-1",
  "breakdown": [
    {
      "resource": "aws_instance.web1",
      "type": "aws_instance",
      "monthly_cost": 60.74,
      "details": { "instance_type": "t3.large" }
    },
    {
      "resource": "aws_instance.web2",
      "type": "aws_instance",
      "monthly_cost": 60.74,
      "details": { "instance_type": "t3.large" }
    },
    {
      "resource": "aws_db_instance.prod_db",
      "type": "aws_db_instance",
      "monthly_cost": 122.28,
      "details": { "instance_class": "db.t3.large", "storage_gb": 200 }
    },
    ...
  ],
  "resource_count": 7
}
```

**Time: ~50ms**

---

### Step 8: API Gateway Saves to Database
```
💾 PostgreSQL Database
├─ Generate estimate ID: est_abc12345
├─ INSERT INTO estimates:
│  ├─ id: est_abc12345
│  ├─ total_monthly_cost: 299.83
│  ├─ currency: USD
│  ├─ region: us-east-1
│  ├─ resources: [JSON array]
│  ├─ breakdown: [JSON array]
│  ├─ resource_count: 7
│  └─ created_at: 2026-03-17 08:42:59
└─ COMMIT
```

**SQL executed:**
```sql
INSERT INTO estimates (
    id, total_monthly_cost, currency, region, 
    resources, breakdown, resource_count
) VALUES (
    'est_abc12345',
    299.83,
    'USD',
    'us-east-1',
    '[{"type":"aws_instance",...}]',
    '[{"resource":"aws_instance.web1",...}]',
    7
);
```

**Time: ~20ms**

---

### Step 9: API Gateway Returns Response
```
📤 HTTP Response
├─ Status: 200 OK
├─ Content-Type: application/json
└─ Body: {
     "estimate_id": "est_abc12345",
     "total_monthly_cost": 299.83,
     "currency": "USD",
     "region": "us-east-1",
     "resource_count": 7,
     "resources": [...],
     "breakdown": [...]
   }
```

**Time: ~10ms**

---

### Step 10: CLI Displays Results
```
📊 CLI Output (Go)
├─ Parses JSON response
├─ Formats as table
└─ Prints to terminal:

============================================================
💰 Total Monthly Cost: $299.83 USD
📍 Region: us-east-1
📦 Resources: 7
🆔 Estimate ID: est_abc12345
============================================================

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

**Time: ~20ms**

---

## Total Time Breakdown

| Step | Component | Time | Action |
|------|-----------|------|--------|
| 1 | CLI | 10ms | Read file |
| 2 | Network | 10ms | HTTP request |
| 3 | API Gateway | 5ms | Validate |
| 4 | Network | 50ms | Call parser |
| 5 | Parser Service | 100ms | Parse Terraform |
| 6 | Network | 30ms | Call cost service |
| 7 | Cost Service | 50ms | Calculate costs |
| 8 | PostgreSQL | 20ms | Save to DB |
| 9 | Network | 10ms | Return response |
| 10 | CLI | 20ms | Format output |
| **TOTAL** | | **~305ms** | **End-to-end** |

---

## Architecture Diagram

```
┌─────────────┐
│   CLI Tool  │ (Go)
│  Port: N/A  │
└──────┬──────┘
       │ HTTP POST
       │ /api/v1/estimate
       ▼
┌─────────────────────────────────────────┐
│         API Gateway (Python)            │
│            Port: 8000                   │
│  ┌─────────────────────────────────┐   │
│  │ 1. Validate request             │   │
│  │ 2. Call Parser Service          │───┼──┐
│  │ 3. Call Cost Service            │   │  │
│  │ 4. Save to PostgreSQL           │───┼──┼──┐
│  │ 5. Return response              │   │  │  │
│  └─────────────────────────────────┘   │  │  │
└─────────────────────────────────────────┘  │  │
                                             │  │
       ┌─────────────────────────────────────┘  │
       │                                        │
       ▼                                        │
┌─────────────────┐                            │
│ Parser Service  │ (Go)                       │
│   Port: 8001    │                            │
│  ┌───────────┐  │                            │
│  │ Parse TF  │  │                            │
│  │ Extract   │  │                            │
│  │ Resources │  │                            │
│  └───────────┘  │                            │
└─────────────────┘                            │
                                               │
       ┌───────────────────────────────────────┘
       │
       ▼
┌─────────────────┐
│  Cost Service   │ (Python)
│   Port: 8002    │
│  ┌───────────┐  │
│  │ Calculate │  │
│  │ Costs     │  │
│  │ Breakdown │  │
│  └───────────┘  │
└─────────────────┘
       │
       │ (Optional: Check cache)
       ▼
┌─────────────────┐
│  Redis Cache    │
│   Port: 6379    │
│  ┌───────────┐  │
│  │ Pricing   │  │
│  │ Data      │  │
│  └───────────┘  │
└─────────────────┘

       │
       │ (Save estimate)
       ▼
┌─────────────────┐
│  PostgreSQL     │
│   Port: 5432    │
│  ┌───────────┐  │
│  │ estimates │  │
│  │ table     │  │
│  └───────────┘  │
└─────────────────┘
```

---

## Real Example with Logs

Run this to see actual logs:

```bash
# Terminal 1: Watch logs
docker-compose logs -f api-gateway parser-service cost-service

# Terminal 2: Make request
./cli/kostructure estimate --path examples/production.tf
```

**You'll see:**
```
parser-service  | 🚀 Parser Service starting on :8001
cost-service    | 🚀 Cost Service starting on port 8002
api-gateway     | 🚀 API Gateway starting on port 8000

api-gateway     | 127.0.0.1 - - [17/Mar/2026 08:42:59] "POST /api/v1/estimate HTTP/1.1" 200 -
parser-service  | Parsed 7 resources from 1 file(s)
cost-service    | Calculated costs for 7 resources: $299.83
api-gateway     | Saved estimate: est_abc12345
```

---

## Key Takeaways

1. **Microservices**: Each service has one job
   - Parser: Extract resources
   - Cost: Calculate prices
   - Gateway: Orchestrate & store

2. **Fast**: Total time ~300ms for 7 resources

3. **Scalable**: Each service can scale independently

4. **Reliable**: PostgreSQL stores all estimates

5. **Cacheable**: Redis can cache pricing data (not implemented in prototype)

6. **Observable**: All services log their actions

---

## File-by-File Explanation

### 1. Parser Service Files

#### `services/parser-service/main.go`
**Purpose**: Parse Terraform files and extract AWS resources

**What it does:**
- Receives Terraform file content via HTTP POST
- Uses regex to find `resource "type" "name" { ... }` blocks
- Extracts resource type (e.g., `aws_instance`)
- Extracts resource name (e.g., `web`)
- Parses attributes (e.g., `instance_type = "t3.medium"`)
- Returns normalized JSON with all resources

**Key Functions:**
```go
// Main HTTP handler
router.POST("/api/v1/parse", func(c *gin.Context) {
    // 1. Receive files
    // 2. Parse each file
    // 3. Return resources
})

// Parsing logic
func (p *SimpleTerraformParser) ParseContent(content string) []Resource {
    // Uses regex to match: resource "aws_instance" "web" { ... }
    resourceRegex := regexp.MustCompile(`resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([^}]*)\}`)
    // Extracts type, name, and attributes
}

// Attribute extraction
func parseAttributes(body string) map[string]interface{} {
    // Matches: instance_type = "t3.medium"
    // Matches: allocated_storage = 100
}
```

**Input Example:**
```json
{
  "files": [
    {
      "name": "main.tf",
      "content": "resource \"aws_instance\" \"web\" { instance_type = \"t3.medium\" }"
    }
  ]
}
```

**Output Example:**
```json
{
  "resources": [
    {
      "type": "aws_instance",
      "name": "web",
      "attributes": {
        "instance_type": "t3.medium"
      },
      "region": "us-east-1"
    }
  ],
  "count": 1
}
```

**Why Go?**
- Fast compilation and execution
- Excellent regex performance
- Low memory footprint
- Easy to deploy (single binary)

---

#### `services/parser-service/go.mod`
**Purpose**: Go module dependencies

**What it does:**
- Defines module name: `github.com/kostructure/parser-service`
- Lists dependencies:
  - `gin-gonic/gin` - HTTP web framework
  - All transitive dependencies

**Why these dependencies?**
- Gin: Fast, minimal HTTP framework with routing

---

#### `services/parser-service/Dockerfile`
**Purpose**: Build and package parser service

**What it does:**
```dockerfile
# Stage 1: Build
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod main.go ./
RUN go mod tidy          # Download dependencies
RUN go build -o parser-service main.go  # Compile

# Stage 2: Runtime
FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/parser-service .  # Copy binary only
CMD ["./parser-service"]
```

**Why multi-stage?**
- Builder stage: ~300MB (includes Go compiler)
- Runtime stage: ~15MB (only binary + Alpine)
- Smaller images = faster deployment

---

### 2. Cost Service Files

#### `services/cost-service/main.py`
**Purpose**: Calculate AWS infrastructure costs

**What it does:**
- Receives parsed resources from API Gateway
- For each resource, calculates monthly cost
- Uses pricing lookup tables (fallback pricing)
- Returns total cost and detailed breakdown

**Key Functions:**
```python
# Main endpoint
@app.route('/api/v1/calculate', methods=['POST'])
def calculate():
    # 1. Receive resources
    # 2. Calculate cost for each
    # 3. Return total + breakdown

# EC2 cost calculation
def calculate_ec2_cost(attrs):
    instance_type = attrs.get('instance_type', 't3.micro')
    hourly = PRICING['ec2'].get(instance_type, 0.0416)
    monthly = hourly * 730  # 730 hours/month average
    return monthly

# RDS cost calculation
def calculate_rds_cost(attrs):
    instance_class = attrs.get('instance_class', 'db.t3.micro')
    storage = int(attrs.get('allocated_storage', 20))
    
    # Instance cost
    hourly = PRICING['rds'].get(instance_class, 0.034)
    monthly = hourly * 730
    
    # Storage cost
    monthly += storage * 0.115  # $0.115 per GB/month
    
    return monthly

# S3 cost calculation
def calculate_s3_cost(attrs):
    # Estimate: 100GB storage + 10K requests
    storage_cost = 100 * 0.023  # $0.023 per GB
    request_cost = (10000 / 1000) * 0.0004  # $0.0004 per 1K requests
    return storage_cost + request_cost
```

**Pricing Data:**
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
    's3_storage': 0.023,  # per GB
    'ebs_gp3': 0.08,      # per GB
}
```

**Input Example:**
```json
{
  "resources": [
    {
      "type": "aws_instance",
      "name": "web",
      "attributes": {
        "instance_type": "t3.medium"
      }
    }
  ],
  "region": "us-east-1"
}
```

**Output Example:**
```json
{
  "total_monthly_cost": 30.37,
  "currency": "USD",
  "region": "us-east-1",
  "breakdown": [
    {
      "resource": "aws_instance.web",
      "type": "aws_instance",
      "monthly_cost": 30.37,
      "details": {
        "instance_type": "t3.medium"
      }
    }
  ],
  "resource_count": 1
}
```

**Why Python?**
- Excellent for data processing
- Easy to add complex calculations
- Rich ecosystem for future ML features
- Fast development

---

#### `services/cost-service/requirements.txt`
**Purpose**: Python dependencies

**What it does:**
```
flask==3.0.0           # Web framework
flask-cors==4.0.0      # CORS support
psycopg2-binary==2.9.9 # PostgreSQL (not used in cost service)
redis==5.0.1           # Redis client (for future caching)
boto3==1.34.0          # AWS SDK (for future AWS Pricing API)
requests==2.31.0       # HTTP client
python-dotenv==1.0.0   # Environment variables
```

**Why these?**
- Flask: Lightweight web framework
- Redis: For caching pricing data (future)
- Boto3: To call real AWS Pricing API (future)

---

#### `services/cost-service/Dockerfile`
**Purpose**: Package cost service

**What it does:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8002
CMD ["python", "main.py"]
```

**Why Python 3.11-slim?**
- Slim: ~120MB (vs ~900MB for full Python)
- 3.11: Latest stable with performance improvements

---

### 3. API Gateway Files

#### `services/api-gateway/main.py`
**Purpose**: Orchestrate all services and manage database

**What it does:**
- Main entry point for all requests
- Calls Parser Service to parse Terraform
- Calls Cost Service to calculate costs
- Saves estimates to PostgreSQL
- Returns combined response

**Key Functions:**
```python
# Main orchestration endpoint
@app.route('/api/v1/estimate', methods=['POST'])
def estimate():
    # Step 1: Parse Terraform files
    parse_response = requests.post(
        f'{PARSER_SERVICE}/api/v1/parse',
        json={'files': files, 'region': region}
    )
    resources = parse_response.json()['resources']
    
    # Step 2: Calculate costs
    cost_response = requests.post(
        f'{COST_SERVICE}/api/v1/calculate',
        json={'resources': resources, 'region': region}
    )
    cost_data = cost_response.json()
    
    # Step 3: Save to database
    estimate_id = f"est_{uuid.uuid4().hex[:8]}"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO estimates 
        (id, total_monthly_cost, currency, region, resources, breakdown, resource_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (estimate_id, cost_data['total_monthly_cost'], ...))
    conn.commit()
    
    # Step 4: Return response
    return jsonify({
        'estimate_id': estimate_id,
        'total_monthly_cost': cost_data['total_monthly_cost'],
        ...
    })

# Database initialization
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS estimates (
            id VARCHAR(50) PRIMARY KEY,
            total_monthly_cost DECIMAL(10,2) NOT NULL,
            currency VARCHAR(3) DEFAULT 'USD',
            region VARCHAR(50) NOT NULL,
            resources JSONB NOT NULL,
            breakdown JSONB NOT NULL,
            resource_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

# Get saved estimate
@app.route('/api/v1/estimates/<estimate_id>', methods=['GET'])
def get_estimate(estimate_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM estimates WHERE id = %s', (estimate_id,))
    row = cur.fetchone()
    return jsonify({...})

# List all estimates
@app.route('/api/v1/estimates', methods=['GET'])
def list_estimates():
    limit = request.args.get('limit', 10, type=int)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, total_monthly_cost, currency, region, resource_count, created_at
        FROM estimates
        ORDER BY created_at DESC
        LIMIT %s
    ''', (limit,))
    rows = cur.fetchall()
    return jsonify({'estimates': [...], 'total': total})
```

**Environment Variables:**
```python
PARSER_SERVICE_URL = os.getenv('PARSER_SERVICE_URL', 'http://localhost:8001')
COST_SERVICE_URL = os.getenv('COST_SERVICE_URL', 'http://localhost:8002')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'kostructure')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
```

**Why API Gateway pattern?**
- Single entry point for clients
- Hides internal service complexity
- Can add authentication, rate limiting
- Manages database transactions
- Easier to monitor and log

---

#### `services/api-gateway/requirements.txt`
**Purpose**: Python dependencies

**What it does:**
```
flask==3.0.0           # Web framework
flask-cors==4.0.0      # CORS for web UI
psycopg2-binary==2.9.9 # PostgreSQL driver
redis==5.0.1           # Redis client
requests==2.31.0       # Call other services
python-dotenv==1.0.0   # Environment variables
```

---

### 4. CLI Tool Files

#### `cli/main.go`
**Purpose**: Command-line interface for users

**What it does:**
- Reads Terraform files from disk
- Sends files to API Gateway
- Receives cost estimate
- Formats and displays results as table or JSON

**Key Functions:**
```go
// Main command structure
var rootCmd = &cobra.Command{
    Use:   "kostructure",
    Short: "AWS Infrastructure Cost Estimator",
}

var estimateCmd = &cobra.Command{
    Use:   "estimate",
    Short: "Estimate infrastructure costs",
    Run:   runEstimate,
}

// Main estimation logic
func runEstimate(cmd *cobra.Command, args []string) {
    // 1. Read Terraform files from --path
    files, err := readTerraformFiles(path)
    
    // 2. Create request
    req := EstimateRequest{
        Files:  files,
        Region: region,
    }
    
    // 3. Call API
    resp, err := http.Post(apiURL+"/api/v1/estimate", "application/json", jsonData)
    
    // 4. Parse response
    var result EstimateResponse
    json.Unmarshal(body, &result)
    
    // 5. Display results
    if format == "json" {
        fmt.Println(string(body))
    } else {
        displayTable(result)
    }
}

// Read all .tf files in directory
func readTerraformFiles(dir string) ([]FileContent, error) {
    filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
        if strings.HasSuffix(info.Name(), ".tf") {
            content, _ := ioutil.ReadFile(path)
            files = append(files, FileContent{
                Name:    info.Name(),
                Content: string(content),
            })
        }
    })
}

// Display as formatted table
func displayTable(result EstimateResponse) {
    fmt.Printf("💰 Total Monthly Cost: $%.2f %s\n", result.TotalMonthlyCost, result.Currency)
    fmt.Printf("📍 Region: %s\n", result.Region)
    fmt.Printf("📦 Resources: %d\n", result.ResourceCount)
    
    table := tablewriter.NewWriter(os.Stdout)
    table.SetHeader([]string{"Resource", "Type", "Monthly Cost"})
    for _, item := range result.Breakdown {
        table.Append([]string{
            item.Resource,
            item.Type,
            fmt.Sprintf("$%.2f", item.MonthlyCost),
        })
    }
    table.Render()
}
```

**Flags:**
```go
--path, -p     Path to Terraform files (default: ".")
--region, -r   AWS region (default: "us-east-1")
--format, -f   Output format: table or json (default: "table")
--breakdown, -b Show detailed breakdown (default: true)
```

**Usage Examples:**
```bash
# Single file
./kostructure estimate --path main.tf

# Directory
./kostructure estimate --path ./terraform/

# JSON output
./kostructure estimate --path ./ --format json

# Different region
./kostructure estimate --path ./ --region us-west-2
```

**Why Go for CLI?**
- Single binary (no dependencies)
- Fast startup time
- Cross-platform (Linux, Mac, Windows)
- Excellent CLI libraries (Cobra)

---

#### `cli/go.mod`
**Purpose**: Go module dependencies

**What it does:**
```
module github.com/kostructure/cli

require (
    github.com/spf13/cobra v1.8.0           # CLI framework
    github.com/olekukonko/tablewriter v0.0.5 # ASCII tables
)
```

**Why these?**
- Cobra: Industry-standard CLI framework (used by kubectl, docker)
- Tablewriter: Beautiful ASCII tables

---

### 5. Web UI Files

#### `web-simple/index.html`
**Purpose**: Simple web interface

**What it does:**
- File upload interface
- Calls API Gateway via JavaScript
- Displays results in browser

**Key Components:**
```html
<!-- File upload -->
<input type="file" id="fileInput" multiple accept=".tf">

<!-- Estimate button -->
<button onclick="estimateCost()">Estimate Cost</button>

<!-- Results display -->
<div id="results">
  <div id="totalCost">$0.00</div>
  <table id="breakdown"></table>
</div>
```

**JavaScript Logic:**
```javascript
async function estimateCost() {
    // 1. Read uploaded files
    const files = await Promise.all(
        selectedFiles.map(async file => ({
            name: file.name,
            content: await file.text()
        }))
    );
    
    // 2. Call API
    const response = await fetch('http://localhost:8000/api/v1/estimate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ files, region: 'us-east-1' })
    });
    
    // 3. Display results
    const data = await response.json();
    document.getElementById('totalCost').textContent = 
        `$${data.total_monthly_cost.toFixed(2)}`;
    
    // 4. Show breakdown table
    data.breakdown.forEach(item => {
        // Add row to table
    });
}
```

**Why simple HTML?**
- No build step required
- Works immediately
- Easy to understand
- Can be served by any web server

---

### 6. Infrastructure Files

#### `docker-compose.yml`
**Purpose**: Orchestrate all services

**What it does:**
- Defines 5 services: postgres, redis, parser, cost, api-gateway
- Sets up networking between services
- Configures environment variables
- Manages volumes for data persistence

**Key Sections:**
```yaml
services:
  # Database
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: kostructure
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
  
  # Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  # Services
  parser-service:
    build: ./services/parser-service
    ports:
      - "8001:8001"
    depends_on:
      - redis
  
  cost-service:
    build: ./services/cost-service
    ports:
      - "8002:8002"
    depends_on:
      - redis
  
  api-gateway:
    build: ./services/api-gateway
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      parser-service:
        condition: service_started
      cost-service:
        condition: service_started
    environment:
      - PARSER_SERVICE_URL=http://parser-service:8001
      - COST_SERVICE_URL=http://cost-service:8002
      - POSTGRES_HOST=postgres
```

**Why Docker Compose?**
- Single command to start everything
- Automatic networking between services
- Easy environment configuration
- Perfect for development and testing

---

#### `Dockerfile` (each service)
**Purpose**: Package each service as container

**Parser Service:**
```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod main.go ./
RUN go mod tidy
RUN go build -o parser-service main.go

# Runtime stage
FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/parser-service .
EXPOSE 8001
CMD ["./parser-service"]
```

**Cost/API Gateway Services:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8002  # or 8000 for api-gateway
CMD ["python", "main.py"]
```

**Why containers?**
- Consistent environment
- Easy deployment
- Isolated dependencies
- Portable across systems

---

### 7. Configuration Files

#### `.env` files
**Purpose**: Environment-specific configuration

**Example:**
```bash
# Flask
FLASK_ENV=development
API_PORT=8000

# Database
DATABASE_PATH=../data/kostructure.db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=kostructure
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Services
PARSER_SERVICE_URL=http://localhost:8001
COST_SERVICE_URL=http://localhost:8002

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

**Why .env files?**
- Separate config from code
- Different settings per environment
- Secure (not committed to git)

---

### 8. Build Scripts

#### `build-cli.sh`
**Purpose**: Build CLI without local Go installation

**What it does:**
```bash
docker run --rm \
  -v "$(pwd)/cli:/app" \
  -w /app \
  golang:1.21-alpine \
  sh -c "go mod tidy && go build -o kostructure main.go"
```

**Why Docker for building?**
- No need to install Go locally
- Consistent build environment
- Works on any system with Docker

---

#### `start.sh`
**Purpose**: Start all services with health checks

**What it does:**
```bash
# Build services
docker-compose build

# Start services
docker-compose up -d

# Wait for services
sleep 10

# Check health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

---

#### `test.sh`
**Purpose**: Verify everything works

**What it does:**
```bash
# Check services running
curl http://localhost:8000/health

# Test CLI
./cli/kostructure estimate --path examples/basic-ec2.tf

# Test API
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{"files":[...]}'
```

---

## File Organization Summary

```
kostructure/
├── services/
│   ├── parser-service/
│   │   ├── main.go           # Go parser logic
│   │   ├── go.mod            # Go dependencies
│   │   └── Dockerfile        # Container build
│   ├── cost-service/
│   │   ├── main.py           # Python cost calculator
│   │   ├── requirements.txt  # Python dependencies
│   │   └── Dockerfile        # Container build
│   └── api-gateway/
│       ├── main.py           # Python orchestrator
│       ├── requirements.txt  # Python dependencies
│       └── Dockerfile        # Container build
├── cli/
│   ├── main.go               # Go CLI tool
│   └── go.mod                # Go dependencies
├── web-simple/
│   └── index.html            # Simple web UI
├── examples/
│   └── *.tf                  # Sample Terraform files
├── docker-compose.yml        # Service orchestration
├── build-cli.sh              # CLI build script
├── start.sh                  # Startup script
└── test.sh                   # Test script
```

Each file has a specific purpose in the microservices architecture!
