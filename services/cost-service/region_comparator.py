"""
Multi-Region Cost Comparison
Compare costs across AWS regions to find the cheapest option
"""

from typing import Dict, List
from plugins.registry import get_registry


class RegionComparator:
    """Compare costs across AWS regions"""
    
    # Major AWS regions
    REGIONS = [
        'us-east-1',      # N. Virginia
        'us-west-2',      # Oregon
        'eu-west-1',      # Ireland
        'ap-southeast-1', # Singapore
        'ap-northeast-1', # Tokyo
    ]
    
    def __init__(self, plugin_registry):
        self.registry = plugin_registry
    
    def compare_regions(self, resources: List[Dict]) -> Dict:
        """
        Compare costs across all regions
        
        Args:
            resources: List of resources to price
            
        Returns:
            Dict with regional costs and recommendations
        """
        regional_costs = {}
        
        for region in self.REGIONS:
            try:
                total = 0
                breakdown = []
                
                for resource in resources:
                    cost = self.registry.calculate_cost(
                        resource['type'],
                        resource.get('attributes', {}),
                        region
                    )
                    total += cost
                    breakdown.append({
                        'resource': f"{resource['type']}.{resource['name']}",
                        'cost': round(cost, 2)
                    })
                
                regional_costs[region] = {
                    'total': round(total, 2),
                    'breakdown': breakdown
                }
            except Exception as e:
                regional_costs[region] = {
                    'error': str(e)
                }
        
        # Find cheapest region
        valid_regions = {k: v for k, v in regional_costs.items() if 'error' not in v}
        if valid_regions:
            cheapest = min(valid_regions.items(), key=lambda x: x[1]['total'])
            most_expensive = max(valid_regions.items(), key=lambda x: x[1]['total'])
            
            savings = most_expensive[1]['total'] - cheapest[1]['total']
            savings_percent = (savings / most_expensive[1]['total']) * 100 if most_expensive[1]['total'] > 0 else 0
            
            return {
                'regions': regional_costs,
                'recommendation': {
                    'cheapest_region': cheapest[0],
                    'cheapest_cost': cheapest[1]['total'],
                    'most_expensive_region': most_expensive[0],
                    'most_expensive_cost': most_expensive[1]['total'],
                    'potential_savings': round(savings, 2),
                    'savings_percent': round(savings_percent, 1)
                }
            }
        
        return {'regions': regional_costs}
    
    def get_region_name(self, region_code: str) -> str:
        """Get human-readable region name"""
        region_names = {
            'us-east-1': 'US East (N. Virginia)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'Europe (Ireland)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
        }
        return region_names.get(region_code, region_code)
