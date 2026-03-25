# Multi-Cloud Architecture (Future Vision)

## Overview
This document outlines the planned architecture for supporting multiple cloud providers (AWS, GCP, Azure).

## Current State
- ✅ AWS only (EC2, RDS, S3, EBS, ElastiCache, Load Balancers)
- ✅ Plugin-based architecture (ready for extension)

## Planned Architecture

### Cloud Provider Abstraction
```python
class CloudProviderPlugin:
    @property
    def provider_name(self) -> str  # "aws", "gcp", "azure"
    
    @property
    def resource_prefix(self) -> str  # "aws_", "google_", "azurerm_"
    
    def calculate_cost(self, resource_type, attributes, region) -> float
```

### Resource Mapping

| AWS | GCP | Azure |
|-----|-----|-------|
| aws_instance | google_compute_instance | azurerm_virtual_machine |
| aws_s3_bucket | google_storage_bucket | azurerm_storage_account |
| aws_db_instance | google_sql_database_instance | azurerm_sql_database |

## Implementation Plan

### Phase 1: Abstraction Layer (2 weeks)
- Create CloudProviderPlugin base class
- Refactor AWS plugins to use new interface
- Add cloud provider detection in parser

### Phase 2: GCP Support (2 weeks)
- Implement GCP Pricing API client
- Create GCP resource plugins
- Add GCP-specific policies

### Phase 3: Azure Support (2 weeks)
- Implement Azure Pricing API client
- Create Azure resource plugins
- Add Azure-specific policies

### Phase 4: Multi-Cloud Features (2 weeks)
- Cross-cloud cost comparison
- Multi-cloud policy enforcement
- Migration cost analysis

## Benefits
- Compare costs across clouds
- Support hybrid/multi-cloud architectures
- Migration planning and analysis
- Vendor lock-in prevention
