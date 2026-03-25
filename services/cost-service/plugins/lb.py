"""
Load Balancer Plugin
"""

from typing import Dict, Any
from plugins.base import ResourcePlugin


class LoadBalancerPlugin(ResourcePlugin):
    
    def __init__(self, pricing_service):
        self.pricing_service = pricing_service
    
    @property
    def resource_type(self) -> str:
        return 'aws_lb'
    
    @property
    def display_name(self) -> str:
        return 'Load Balancer'
    
    @property
    def required_attributes(self) -> list:
        return []
    
    def calculate_cost(self, attributes: Dict[str, Any], region: str = 'us-east-1') -> float:
        # Get ALB hourly price
        if self.pricing_service:
            hourly = self.pricing_service.get_alb_price(region)
        else:
            hourly = 0.0225  # Fallback
        monthly = hourly * 730
        lcu_cost = 16.43  # Estimated LCU charges (varies by traffic)
        return monthly + lcu_cost
