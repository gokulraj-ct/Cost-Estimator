"""
EBS Volume Plugin
Calculates cost for AWS EBS volumes
"""

from typing import Dict, Any
from plugins.base import ResourcePlugin


class EBSPlugin(ResourcePlugin):
    """Plugin for AWS EBS volume pricing"""
    
    def __init__(self, pricing_service):
        self.pricing_service = pricing_service
    
    @property
    def resource_type(self) -> str:
        return 'aws_ebs_volume'
    
    @property
    def display_name(self) -> str:
        return 'EBS Volume'
    
    @property
    def required_attributes(self) -> list:
        return ['size']
    
    def calculate_cost(self, attributes: Dict[str, Any], region: str = 'us-east-1') -> float:
        """Calculate EBS monthly cost"""
        self.validate_attributes(attributes)
        
        size = int(attributes.get('size', 8))
        volume_type = attributes.get('type', 'gp3')
        
        # Pricing per GB per month
        pricing = {
            'gp2': 0.10,
            'gp3': 0.08,
            'io1': 0.125,
            'io2': 0.125,
            'st1': 0.045,
            'sc1': 0.015,
            'standard': 0.05,
        }
        
        price_per_gb = pricing.get(volume_type, 0.08)
        monthly = size * price_per_gb
        
        # Add IOPS cost for io1/io2
        if volume_type in ['io1', 'io2']:
            iops = int(attributes.get('iops', 100))
            monthly += iops * 0.065  # $0.065 per provisioned IOPS
        
        return monthly
