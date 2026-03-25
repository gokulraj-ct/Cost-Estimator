"""
Plugin Registry
Manages all resource pricing plugins
"""

from typing import Dict, Optional
from plugins.base import ResourcePlugin


class PluginRegistry:
    """Registry for all resource pricing plugins"""
    
    def __init__(self):
        self._plugins: Dict[str, ResourcePlugin] = {}
    
    def register(self, plugin: ResourcePlugin) -> None:
        """Register a new plugin"""
        self._plugins[plugin.resource_type] = plugin
        print(f"✅ Registered plugin: {plugin.display_name} ({plugin.resource_type})")
    
    def get_plugin(self, resource_type: str) -> Optional[ResourcePlugin]:
        """Get plugin for a resource type"""
        return self._plugins.get(resource_type)
    
    def list_plugins(self) -> list:
        """List all registered plugins"""
        return [
            {
                'resource_type': plugin.resource_type,
                'display_name': plugin.display_name,
                'required_attributes': plugin.required_attributes
            }
            for plugin in self._plugins.values()
        ]
    
    def calculate_cost(self, resource_type: str, attributes: dict, region: str = 'us-east-1') -> float:
        """Calculate cost using appropriate plugin"""
        plugin = self.get_plugin(resource_type)
        if not plugin:
            raise ValueError(f"No plugin found for resource type: {resource_type}")
        
        return plugin.calculate_cost(attributes, region)
    
    def get_cost_breakdown(self, resource_type: str, attributes: dict, region: str = 'us-east-1') -> dict:
        """Get detailed cost breakdown"""
        plugin = self.get_plugin(resource_type)
        if not plugin:
            raise ValueError(f"No plugin found for resource type: {resource_type}")
        
        return plugin.get_cost_breakdown(attributes, region)


# Global registry instance
_registry = None

def get_registry() -> PluginRegistry:
    """Get or create plugin registry singleton"""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry
