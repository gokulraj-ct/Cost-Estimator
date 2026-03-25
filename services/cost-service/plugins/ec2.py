"""
EC2 Instance Plugin
Calculates cost for AWS EC2 instances using AWS Pricing API
"""

from typing import Dict, Any
from plugins.base import ResourcePlugin


class EC2Plugin(ResourcePlugin):
    """Plugin for AWS EC2 instance pricing"""
    
    def __init__(self, pricing_service):
        self.pricing_service = pricing_service
    
    @property
    def resource_type(self) -> str:
        return 'aws_instance'
    
    @property
    def display_name(self) -> str:
        return 'EC2 Instance'
    
    @property
    def required_attributes(self) -> list:
        return ['instance_type']
    
    def calculate_cost(self, attributes: Dict[str, Any], region: str = 'us-east-1') -> float:
        """Calculate EC2 monthly cost using AWS Pricing API or fallback"""
        self.validate_attributes(attributes)
        
        instance_type = attributes['instance_type']
        
        # Try AWS Pricing API first
        if self.pricing_service:
            try:
                hourly = self.pricing_service.get_ec2_price(instance_type, region)
                if hourly > 0:
                    monthly = hourly * 730
                    
                    # Add EBS volume cost if specified
                    if 'root_block_device' in attributes:
                        volume_size = attributes['root_block_device'].get('volume_size', 8)
                        monthly += volume_size * 0.08  # GP3 pricing
                    
                    return monthly
            except:
                pass  # Fall through to static pricing
        
        # Fallback: Static pricing
        pricing = {
            't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416,
            't3.large': 0.0832, 't3.xlarge': 0.1664, 't3.2xlarge': 0.3328,
            't2.micro': 0.0116, 't2.small': 0.023, 't2.medium': 0.0464,
            'm5.large': 0.096, 'm5.xlarge': 0.192, 'm5.2xlarge': 0.384,
            'c5.large': 0.085, 'c5.xlarge': 0.17, 'c5.2xlarge': 0.34,
        }
        
        hourly = pricing.get(instance_type, 0.05)  # Default $0.05/hr
        monthly = hourly * 730
        
        # Add EBS volume cost if specified
        if 'root_block_device' in attributes:
            volume_size = attributes['root_block_device'].get('volume_size', 8)
            monthly += volume_size * 0.08
        
        return monthly
    
    def get_cost_breakdown(self, attributes: Dict[str, Any], region: str = 'us-east-1') -> Dict[str, Any]:
        """Get detailed cost breakdown"""
        self.validate_attributes(attributes)
        
        instance_type = attributes['instance_type']
        hourly = self.pricing_service.get_ec2_price(instance_type, region)
        compute_cost = hourly * 730
        
        components = [{
            'name': 'Compute',
            'description': f'{instance_type} instance',
            'cost': compute_cost
        }]
        
        # Add EBS if present
        if 'root_block_device' in attributes:
            volume_size = attributes['root_block_device'].get('volume_size', 8)
            ebs_cost = volume_size * 0.08
            components.append({
                'name': 'EBS Storage',
                'description': f'{volume_size}GB GP3',
                'cost': ebs_cost
            })
        
        return {
            'total': sum(c['cost'] for c in components),
            'components': components
        }
