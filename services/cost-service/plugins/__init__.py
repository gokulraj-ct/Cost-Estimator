"""
Plugin System Initialization
Auto-discovers and registers all plugins
"""

from plugins.registry import get_registry
from plugins.ec2 import EC2Plugin
from plugins.rds import RDSPlugin
from plugins.s3 import S3Plugin
from plugins.lb import LoadBalancerPlugin
from plugins.elasticache import ElastiCachePlugin
from plugins.ebs import EBSPlugin


def initialize_plugins(pricing_service):
    """Initialize and register all plugins"""
    registry = get_registry()
    
    print("🔌 Initializing plugin system...")
    
    # Register EC2 plugin
    registry.register(EC2Plugin(pricing_service))
    
    # Register RDS plugin
    registry.register(RDSPlugin(pricing_service))
    
    # Register S3 plugin
    registry.register(S3Plugin(pricing_service))
    
    # Register Load Balancer plugin
    registry.register(LoadBalancerPlugin(pricing_service))
    
    # Register ElastiCache plugin
    registry.register(ElastiCachePlugin(pricing_service))
    
    # Register EBS plugin
    registry.register(EBSPlugin(pricing_service))
    
    print(f"✅ Loaded {len(registry.list_plugins())} plugins")
    
    return registry
