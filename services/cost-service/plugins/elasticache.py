"""
ElastiCache Plugin
Calculates cost for AWS ElastiCache clusters
"""

from typing import Dict, Any
from plugins.base import ResourcePlugin


class ElastiCachePlugin(ResourcePlugin):
    """Plugin for AWS ElastiCache pricing"""
    
    def __init__(self, pricing_service):
        self.pricing_service = pricing_service
    
    @property
    def resource_type(self) -> str:
        return 'aws_elasticache_cluster'
    
    @property
    def display_name(self) -> str:
        return 'ElastiCache Cluster'
    
    @property
    def required_attributes(self) -> list:
        return ['node_type']
    
    def calculate_cost(self, attributes: Dict[str, Any], region: str = 'us-east-1') -> float:
        """Calculate ElastiCache monthly cost"""
        self.validate_attributes(attributes)
        
        node_type = attributes['node_type']
        num_nodes = attributes.get('num_cache_nodes', 1)
        
        # Pricing per node type (hourly)
        pricing = {
            'cache.t3.micro': 0.017,
            'cache.t3.small': 0.034,
            'cache.t3.medium': 0.068,
            'cache.t4g.micro': 0.016,
            'cache.t4g.small': 0.032,
            'cache.t4g.medium': 0.064,
            'cache.m5.large': 0.136,
            'cache.m5.xlarge': 0.272,
            'cache.r5.large': 0.188,
            'cache.r5.xlarge': 0.376,
        }
        
        hourly = pricing.get(node_type, 0.017)  # Default to t3.micro
        monthly = hourly * 730 * num_nodes
        
        return monthly
