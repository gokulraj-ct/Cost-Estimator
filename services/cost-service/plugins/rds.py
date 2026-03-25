"""
RDS Database Plugin
Calculates cost for AWS RDS instances using AWS Pricing API
"""

from typing import Dict, Any
from plugins.base import ResourcePlugin


class RDSPlugin(ResourcePlugin):
    """Plugin for AWS RDS database pricing"""
    
    def __init__(self, pricing_service):
        self.pricing_service = pricing_service
    
    @property
    def resource_type(self) -> str:
        return 'aws_db_instance'
    
    @property
    def display_name(self) -> str:
        return 'RDS Database'
    
    @property
    def required_attributes(self) -> list:
        return ['instance_class']
    
    def calculate_cost(self, attributes: Dict[str, Any], region: str = 'us-east-1') -> float:
        """Calculate RDS monthly cost using AWS Pricing API or fallback"""
        self.validate_attributes(attributes)
        
        instance_class = attributes['instance_class']
        storage = int(attributes.get('allocated_storage', 20))
        engine = attributes.get('engine', 'postgres')
        
        # Try AWS Pricing API first
        if self.pricing_service:
            try:
                hourly = self.pricing_service.get_rds_price(instance_class, engine, region)
                if hourly > 0:
                    monthly = hourly * 730
                    monthly += storage * 0.115  # GP2 storage
                    return monthly
            except:
                pass  # Fall through to static pricing
        
        # Fallback: Static pricing
        pricing = {
            'db.t3.micro': 0.017, 'db.t3.small': 0.034, 'db.t3.medium': 0.068,
            'db.t3.large': 0.136, 'db.t2.micro': 0.018, 'db.t2.small': 0.036,
            'db.m5.large': 0.192, 'db.m5.xlarge': 0.384,
        }
        
        hourly = pricing.get(instance_class, 0.034)  # Default db.t3.small
        monthly = hourly * 730
        monthly += storage * 0.115  # GP2 storage
        
        return monthly
    
    def get_cost_breakdown(self, attributes: Dict[str, Any], region: str = 'us-east-1') -> Dict[str, Any]:
        """Get detailed cost breakdown"""
        self.validate_attributes(attributes)
        
        instance_class = attributes['instance_class']
        storage = int(attributes.get('allocated_storage', 20))
        engine = attributes.get('engine', 'postgres')
        
        hourly = self.pricing_service.get_rds_price(instance_class, engine, region)
        compute_cost = hourly * 730
        storage_cost = storage * 0.115
        
        components = [
            {
                'name': 'Compute',
                'description': f'{instance_class} ({engine})',
                'cost': compute_cost
            },
            {
                'name': 'Storage',
                'description': f'{storage}GB GP2',
                'cost': storage_cost
            }
        ]
        
        return {
            'total': compute_cost + storage_cost,
            'components': components
        }
