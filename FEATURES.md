# Kostructure Features

## Core Features
- Parse Terraform files and extract AWS resources
- Calculate real-time costs using AWS Pricing API
- Support for EC2 instances with accurate hourly pricing
- Support for RDS databases with engine-specific pricing
- CLI tool for quick cost estimates
- Web UI for interactive cost analysis
- REST API for programmatic access
- Microservices architecture (Parser, Cost Calculator, API Gateway)
- PostgreSQL database for storing estimates
- Redis caching for improved performance

## Plugin System
- Modular plugin architecture for easy extensibility
- Each AWS resource type as independent plugin
- Auto-discovery and registration of plugins
- Automatic validation of required attributes
- Community-friendly plugin development
- 3-step process to add new resources

## Cost Optimization
- Multi-region cost comparison across 5 major AWS regions
- Automatic identification of cheapest region
- Reserved Instance savings recommendations (40% savings)
- Spot Instance suggestions for non-critical workloads (70% savings)
- Right-sizing recommendations for oversized instances
- Total potential savings calculation
- Impact assessment for each optimization

## Reporting & Export
- CSV export for cost estimates
- CSV export for optimization reports
- CSV export for region comparison
- Professional report formatting with timestamps
- Detailed cost breakdown by resource
- Summary statistics and totals

## API Endpoints
- `/api/v1/estimate` - Calculate infrastructure costs
- `/api/v1/plugins` - List available resource plugins
- `/api/v1/compare-regions` - Compare costs across regions
- `/api/v1/optimize` - Get cost optimization suggestions
- `/api/v1/export/csv` - Export estimate to CSV
- `/api/v1/export/optimization-csv` - Export optimization report
- `/api/v1/export/region-comparison-csv` - Export region comparison

## Technical Features
- Docker Compose deployment
- AWS IAM role authentication
- Regional pricing support
- Error handling with clear messages
- Validation of required resource attributes
- Caching for improved performance
- CORS support for web integration
