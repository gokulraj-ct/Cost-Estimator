# Plugin System

Kostructure uses a plugin-based architecture where each AWS resource type is a separate, independent module.

## Architecture

```
plugins/
├── base.py          # Base plugin interface
├── registry.py      # Plugin registry
├── __init__.py      # Auto-discovery
├── ec2.py           # EC2 plugin
├── rds.py           # RDS plugin
└── [your-plugin].py # Add new plugins here
```

## Creating a New Plugin

### 1. Create Plugin File

Create `plugins/your_resource.py`:

```python
from typing import Dict, Any
from plugins.base import ResourcePlugin

class YourResourcePlugin(ResourcePlugin):
    
    def __init__(self, pricing_service):
        self.pricing_service = pricing_service
    
    @property
    def resource_type(self) -> str:
        return 'aws_your_resource'  # Terraform resource type
    
    @property
    def display_name(self) -> str:
        return 'Your Resource Name'
    
    @property
    def required_attributes(self) -> list:
        return ['required_field1', 'required_field2']
    
    def calculate_cost(self, attributes: Dict[str, Any], region: str = 'us-east-1') -> float:
        """Calculate monthly cost"""
        self.validate_attributes(attributes)
        
        # Your cost calculation logic here
        # Use self.pricing_service.get_*_price() for AWS API
        # Or use static pricing
        
        return monthly_cost
```

### 2. Register Plugin

Add to `plugins/__init__.py`:

```python
from plugins.your_resource import YourResourcePlugin

def initialize_plugins(pricing_service):
    registry = get_registry()
    
    # ... existing plugins ...
    
    # Register your plugin
    registry.register(YourResourcePlugin(pricing_service))
    
    return registry
```

### 3. Test Plugin

```bash
# Rebuild
docker-compose up -d --build cost-service

# List plugins
curl http://localhost:8002/api/v1/plugins

# Test with Terraform file
./cli/kostructure estimate --path examples/your-test.tf
```

## Plugin Interface

### Required Methods

#### `resource_type` (property)
- Returns: Terraform resource type (e.g., `'aws_instance'`)
- Must match exactly what Terraform uses

#### `display_name` (property)
- Returns: Human-readable name (e.g., `'EC2 Instance'`)
- Used in UI and error messages

#### `required_attributes` (property)
- Returns: List of required Terraform attributes
- Example: `['instance_type', 'ami']`
- Automatically validated before cost calculation

#### `calculate_cost(attributes, region)`
- Args:
  - `attributes`: Dict of Terraform resource attributes
  - `region`: AWS region (default: 'us-east-1')
- Returns: Monthly cost in USD (float)
- Raises: `ValueError` if validation fails

### Optional Methods

#### `get_cost_breakdown(attributes, region)`
- Returns detailed cost breakdown
- Example:
```python
{
    'total': 100.50,
    'components': [
        {'name': 'Compute', 'description': 't3.medium', 'cost': 30.37},
        {'name': 'Storage', 'description': '100GB', 'cost': 11.50}
    ]
}
```

## Examples

### Example 1: Static Pricing

```python
class S3Plugin(ResourcePlugin):
    @property
    def resource_type(self) -> str:
        return 'aws_s3_bucket'
    
    @property
    def display_name(self) -> str:
        return 'S3 Bucket'
    
    @property
    def required_attributes(self) -> list:
        return []  # No required attributes
    
    def calculate_cost(self, attributes: Dict[str, Any], region: str = 'us-east-1') -> float:
        storage_gb = 100  # Estimate
        return storage_gb * 0.023  # $0.023 per GB
```

### Example 2: AWS Pricing API

```python
class LambdaPlugin(ResourcePlugin):
    def __init__(self, pricing_service):
        self.pricing_service = pricing_service
    
    @property
    def resource_type(self) -> str:
        return 'aws_lambda_function'
    
    @property
    def display_name(self) -> str:
        return 'Lambda Function'
    
    @property
    def required_attributes(self) -> list:
        return ['memory_size']
    
    def calculate_cost(self, attributes: Dict[str, Any], region: str = 'us-east-1') -> float:
        self.validate_attributes(attributes)
        
        memory_mb = int(attributes['memory_size'])
        invocations = 1000000  # Estimate 1M invocations
        
        # Calculate based on memory and invocations
        gb_seconds = (memory_mb / 1024) * (invocations * 0.1)  # Assume 100ms per invocation
        cost = gb_seconds * 0.0000166667  # Lambda pricing
        
        return cost
```

## Testing Your Plugin

### Unit Test Template

```python
def test_your_plugin():
    from plugins.your_resource import YourResourcePlugin
    
    plugin = YourResourcePlugin(None)
    
    # Test valid attributes
    cost = plugin.calculate_cost({
        'required_field1': 'value1',
        'required_field2': 'value2'
    })
    assert cost > 0
    
    # Test missing attributes
    try:
        plugin.calculate_cost({})
        assert False, "Should raise ValueError"
    except ValueError:
        pass
```

## Contributing

1. Fork the repository
2. Create your plugin in `plugins/`
3. Add tests
4. Submit pull request

## Current Plugins

- ✅ EC2 Instance (`aws_instance`)
- ✅ RDS Database (`aws_db_instance`)

## Roadmap

- [ ] S3 Bucket
- [ ] Lambda Function
- [ ] EBS Volume
- [ ] Load Balancer
- [ ] NAT Gateway
- [ ] VPC
- [ ] CloudFront
- [ ] DynamoDB
- [ ] ElastiCache
- [ ] ECS/EKS
