"""
S3 Bucket Plugin
"""

from typing import Dict, Any
from plugins.base import ResourcePlugin


class S3Plugin(ResourcePlugin):
    
    def __init__(self, pricing_service):
        self.pricing_service = pricing_service
    
    @property
    def resource_type(self) -> str:
        return 'aws_s3_bucket'
    
    @property
    def display_name(self) -> str:
        return 'S3 Bucket'
    
    @property
    def required_attributes(self) -> list:
        return []
    
    def calculate_cost(self, attributes: Dict[str, Any], region: str = 'us-east-1') -> float:
        # Estimate: 100GB storage + minimal requests
        storage_gb = 100
        if self.pricing_service:
            price_per_gb = self.pricing_service.get_s3_price(region)
        else:
            price_per_gb = 0.023  # Fallback
        storage_cost = storage_gb * price_per_gb
        request_cost = 0.004  # Minimal requests estimate
        return storage_cost + request_cost
