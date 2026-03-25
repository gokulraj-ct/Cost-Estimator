"""
Cost Optimization Suggestions
Analyze infrastructure and provide cost-saving recommendations
"""

from typing import Dict, List


class CostOptimizer:
    """Provide cost optimization suggestions"""
    
    def __init__(self, plugin_registry):
        self.registry = plugin_registry
    
    def analyze(self, resources: List[Dict], region: str = 'us-east-1') -> Dict:
        """
        Analyze resources and provide optimization suggestions
        
        Args:
            resources: List of resources
            region: AWS region
            
        Returns:
            Dict with suggestions and potential savings
        """
        suggestions = []
        total_savings = 0
        
        for resource in resources:
            resource_type = resource['type']
            attrs = resource.get('attributes', {})
            name = resource['name']
            
            if resource_type == 'aws_instance':
                ec2_suggestions = self._analyze_ec2(name, attrs, region)
                suggestions.extend(ec2_suggestions['suggestions'])
                total_savings += ec2_suggestions['savings']
            
            elif resource_type == 'aws_db_instance':
                rds_suggestions = self._analyze_rds(name, attrs, region)
                suggestions.extend(rds_suggestions['suggestions'])
                total_savings += rds_suggestions['savings']
        
        return {
            'suggestions': suggestions,
            'total_potential_savings': round(total_savings, 2),
            'count': len(suggestions)
        }
    
    def _analyze_ec2(self, name: str, attrs: Dict, region: str) -> Dict:
        """Analyze EC2 instance for optimization"""
        suggestions = []
        savings = 0
        
        instance_type = attrs.get('instance_type', '')
        
        # Suggestion 1: Consider Reserved Instances
        if instance_type:
            current_cost = self.registry.calculate_cost('aws_instance', attrs, region)
            reserved_savings = current_cost * 0.40  # ~40% savings with 1-year RI
            
            suggestions.append({
                'resource': f'aws_instance.{name}',
                'type': 'Reserved Instance',
                'description': f'Switch to 1-year Reserved Instance for {instance_type}',
                'current_cost': round(current_cost, 2),
                'optimized_cost': round(current_cost - reserved_savings, 2),
                'savings': round(reserved_savings, 2),
                'impact': 'high'
            })
            savings += reserved_savings
        
        # Suggestion 2: Consider Spot Instances
        if instance_type and not instance_type.startswith('t'):  # Not burstable
            current_cost = self.registry.calculate_cost('aws_instance', attrs, region)
            spot_savings = current_cost * 0.70  # ~70% savings with Spot
            
            suggestions.append({
                'resource': f'aws_instance.{name}',
                'type': 'Spot Instance',
                'description': f'Use Spot Instances for non-critical workloads ({instance_type})',
                'current_cost': round(current_cost, 2),
                'optimized_cost': round(current_cost - spot_savings, 2),
                'savings': round(spot_savings, 2),
                'impact': 'high',
                'risk': 'Spot instances can be interrupted'
            })
        
        # Suggestion 3: Right-sizing
        if instance_type in ['t3.large', 't3.xlarge', 'm5.large', 'm5.xlarge']:
            smaller_type = self._get_smaller_instance(instance_type)
            if smaller_type:
                current_cost = self.registry.calculate_cost('aws_instance', attrs, region)
                smaller_attrs = attrs.copy()
                smaller_attrs['instance_type'] = smaller_type
                smaller_cost = self.registry.calculate_cost('aws_instance', smaller_attrs, region)
                rightsizing_savings = current_cost - smaller_cost
                
                suggestions.append({
                    'resource': f'aws_instance.{name}',
                    'type': 'Right-sizing',
                    'description': f'Consider downsizing from {instance_type} to {smaller_type}',
                    'current_cost': round(current_cost, 2),
                    'optimized_cost': round(smaller_cost, 2),
                    'savings': round(rightsizing_savings, 2),
                    'impact': 'medium',
                    'note': 'Monitor performance after downsizing'
                })
        
        return {'suggestions': suggestions, 'savings': savings}
    
    def _analyze_rds(self, name: str, attrs: Dict, region: str) -> Dict:
        """Analyze RDS instance for optimization"""
        suggestions = []
        savings = 0
        
        instance_class = attrs.get('instance_class', '')
        
        # Suggestion: Reserved Instances
        if instance_class:
            current_cost = self.registry.calculate_cost('aws_db_instance', attrs, region)
            reserved_savings = current_cost * 0.35  # ~35% savings with 1-year RI
            
            suggestions.append({
                'resource': f'aws_db_instance.{name}',
                'type': 'Reserved Instance',
                'description': f'Switch to 1-year Reserved Instance for {instance_class}',
                'current_cost': round(current_cost, 2),
                'optimized_cost': round(current_cost - reserved_savings, 2),
                'savings': round(reserved_savings, 2),
                'impact': 'high'
            })
            savings += reserved_savings
        
        return {'suggestions': suggestions, 'savings': savings}
    
    def _get_smaller_instance(self, instance_type: str) -> str:
        """Get next smaller instance type"""
        downsizing_map = {
            't3.xlarge': 't3.large',
            't3.large': 't3.medium',
            'm5.xlarge': 'm5.large',
            'm5.large': 'm5.medium',
        }
        return downsizing_map.get(instance_type)
