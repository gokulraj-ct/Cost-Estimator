# Multi-Cloud Support Architecture

## Current State: AWS Only
- Cost calculation: AWS Pricing API
- Resources: aws_instance, aws_s3_bucket, aws_db_instance, etc.
- Policies: AWS-specific (SEC-001 to SEC-005)

## Proposed Architecture: Cloud-Agnostic

### 1. Cloud Provider Abstraction Layer

```
┌─────────────────────────────────────────────┐
│         Terraform Parser Service            │
│  (Detects cloud provider from resources)    │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│         Cloud Provider Router               │
│  Routes to appropriate pricing service      │
└─────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
    ┌────────┐    ┌────────┐    ┌────────┐
    │  AWS   │    │  GCP   │    │ Azure  │
    │Pricing │    │Pricing │    │Pricing │
    └────────┘    └────────┘    └────────┘
```

### 2. Resource Type Mapping

#### AWS Resources
- `aws_instance` → EC2
- `aws_s3_bucket` → S3
- `aws_db_instance` → RDS

#### GCP Resources
- `google_compute_instance` → Compute Engine
- `google_storage_bucket` → Cloud Storage
- `google_sql_database_instance` → Cloud SQL

#### Azure Resources
- `azurerm_virtual_machine` → Virtual Machines
- `azurerm_storage_account` → Storage Account
- `azurerm_sql_database` → SQL Database

### 3. Plugin System Enhancement

```python
# Base Plugin Interface
class CloudProviderPlugin:
    @property
    def provider_name(self) -> str:
        """AWS, GCP, or Azure"""
        pass
    
    @property
    def resource_prefix(self) -> str:
        """aws_, google_, azurerm_"""
        pass
    
    def get_pricing_service(self):
        """Return provider-specific pricing service"""
        pass
    
    def calculate_cost(self, resource_type, attributes, region):
        """Calculate cost for this provider's resources"""
        pass
```

### 4. Database Schema Updates

#### Add cloud_provider column
```sql
ALTER TABLE estimates ADD COLUMN cloud_provider VARCHAR(20) DEFAULT 'aws';
ALTER TABLE integrations ADD COLUMN cloud_provider VARCHAR(20) DEFAULT 'aws';
```

#### Multi-cloud policies
```sql
-- Policies can now target specific providers
ALTER TABLE policies ADD COLUMN cloud_provider VARCHAR(20) DEFAULT 'all';

-- Example policies:
-- SEC-AWS-001: AWS-specific security
-- SEC-GCP-001: GCP-specific security
-- SEC-AZURE-001: Azure-specific security
-- SEC-MULTI-001: Applies to all clouds
```

### 5. Implementation Plan

#### Phase 1: Abstraction Layer (Week 1-2)
- [ ] Create CloudProviderPlugin base class
- [ ] Refactor AWS plugin to use new interface
- [ ] Add cloud provider detection in parser
- [ ] Update database schema

#### Phase 2: GCP Support (Week 3-4)
- [ ] Implement GCP Pricing API client
- [ ] Create GCP resource plugins:
  - google_compute_instance
  - google_storage_bucket
  - google_sql_database_instance
- [ ] Add GCP-specific policies
- [ ] Test with GCP Terraform files

#### Phase 3: Azure Support (Week 5-6)
- [ ] Implement Azure Pricing API client
- [ ] Create Azure resource plugins:
  - azurerm_virtual_machine
  - azurerm_storage_account
  - azurerm_sql_database
- [ ] Add Azure-specific policies
- [ ] Test with Azure Terraform files

#### Phase 4: Multi-Cloud Features (Week 7-8)
- [ ] Cross-cloud cost comparison
- [ ] Multi-cloud policy enforcement
- [ ] Cloud-agnostic recommendations
- [ ] Migration cost analysis

### 6. Pricing API Integration

#### GCP Pricing API
```python
from google.cloud import billing_v1

class GCPPricingService:
    def __init__(self):
        self.client = billing_v1.CloudCatalogClient()
    
    def get_compute_price(self, machine_type, region):
        # Query GCP Cloud Billing Catalog API
        pass
```

#### Azure Pricing API
```python
import requests

class AzurePricingService:
    def __init__(self):
        self.base_url = "https://prices.azure.com/api/retail/prices"
    
    def get_vm_price(self, vm_size, region):
        # Query Azure Retail Prices API
        pass
```

### 7. Frontend Updates

#### Integration Form
```javascript
// Add cloud provider selection
{
  repo: "user/repo",
  token: "ghp_xxx",
  cloud_provider: "aws", // or "gcp", "azure"
  default_region: "us-east-1" // or "us-central1", "eastus"
}
```

#### Cost Display
```
Total Cost: $100/month
├─ AWS: $60/month (3 resources)
├─ GCP: $30/month (2 resources)
└─ Azure: $10/month (1 resource)
```

### 8. Configuration

#### Environment Variables
```bash
# AWS
USE_AWS_PRICING=true
AWS_DEFAULT_REGION=us-east-1

# GCP
USE_GCP_PRICING=true
GCP_PROJECT_ID=my-project
GCP_DEFAULT_REGION=us-central1

# Azure
USE_AZURE_PRICING=true
AZURE_SUBSCRIPTION_ID=xxx
AZURE_DEFAULT_REGION=eastus
```

### 9. Benefits

1. **Flexibility**: Support any cloud provider
2. **Comparison**: Compare costs across clouds
3. **Migration**: Analyze migration costs
4. **Hybrid**: Support multi-cloud architectures
5. **Future-proof**: Easy to add new providers

### 10. Example: Multi-Cloud Terraform

```hcl
# AWS Resources
resource "aws_instance" "web" {
  instance_type = "t3.medium"
}

# GCP Resources
resource "google_compute_instance" "app" {
  machine_type = "n1-standard-1"
}

# Azure Resources
resource "azurerm_virtual_machine" "db" {
  vm_size = "Standard_B2s"
}
```

**Result**: Single cost estimate covering all three clouds!

## Next Steps

1. ✅ Add budget policies (DONE)
2. 🔄 Implement cloud provider abstraction
3. 🔄 Add GCP support
4. 🔄 Add Azure support
5. 🔄 Multi-cloud dashboard
