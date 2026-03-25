"""
Report Exporter
Export cost estimates to CSV format
"""

import csv
import io
from typing import List, Dict
from datetime import datetime


class ReportExporter:
    """Export cost reports to various formats"""
    
    def export_csv(self, estimate_data: Dict) -> str:
        """
        Export estimate to CSV format
        
        Args:
            estimate_data: Estimate data with breakdown
            
        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Kostructure Cost Estimate Report'])
        writer.writerow([f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
        writer.writerow([])
        
        # Summary
        writer.writerow(['Summary'])
        writer.writerow(['Total Monthly Cost', f"${estimate_data.get('total_monthly_cost', 0):.2f}"])
        writer.writerow(['Region', estimate_data.get('region', 'N/A')])
        writer.writerow(['Resource Count', estimate_data.get('resource_count', 0)])
        writer.writerow([])
        
        # Breakdown
        writer.writerow(['Resource Breakdown'])
        writer.writerow(['Resource', 'Type', 'Monthly Cost'])
        
        for item in estimate_data.get('breakdown', []):
            writer.writerow([
                item.get('resource', ''),
                item.get('type', ''),
                f"${item.get('monthly_cost', 0):.2f}"
            ])
        
        return output.getvalue()
    
    def export_optimization_csv(self, optimization_data: Dict) -> str:
        """
        Export optimization suggestions to CSV
        
        Args:
            optimization_data: Optimization suggestions
            
        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Kostructure Cost Optimization Report'])
        writer.writerow([f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
        writer.writerow([])
        
        # Summary
        writer.writerow(['Summary'])
        writer.writerow(['Total Potential Savings', f"${optimization_data.get('total_potential_savings', 0):.2f}"])
        writer.writerow(['Number of Suggestions', optimization_data.get('count', 0)])
        writer.writerow([])
        
        # Suggestions
        writer.writerow(['Optimization Suggestions'])
        writer.writerow(['Resource', 'Type', 'Description', 'Current Cost', 'Optimized Cost', 'Savings', 'Impact'])
        
        for suggestion in optimization_data.get('suggestions', []):
            writer.writerow([
                suggestion.get('resource', ''),
                suggestion.get('type', ''),
                suggestion.get('description', ''),
                f"${suggestion.get('current_cost', 0):.2f}",
                f"${suggestion.get('optimized_cost', 0):.2f}",
                f"${suggestion.get('savings', 0):.2f}",
                suggestion.get('impact', '')
            ])
        
        return output.getvalue()
    
    def export_region_comparison_csv(self, comparison_data: Dict) -> str:
        """
        Export region comparison to CSV
        
        Args:
            comparison_data: Region comparison data
            
        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Kostructure Region Comparison Report'])
        writer.writerow([f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
        writer.writerow([])
        
        # Recommendation
        if 'recommendation' in comparison_data:
            rec = comparison_data['recommendation']
            writer.writerow(['Recommendation'])
            writer.writerow(['Cheapest Region', rec.get('cheapest_region', '')])
            writer.writerow(['Cheapest Cost', f"${rec.get('cheapest_cost', 0):.2f}"])
            writer.writerow(['Most Expensive Region', rec.get('most_expensive_region', '')])
            writer.writerow(['Most Expensive Cost', f"${rec.get('most_expensive_cost', 0):.2f}"])
            writer.writerow(['Potential Savings', f"${rec.get('potential_savings', 0):.2f}"])
            writer.writerow(['Savings Percent', f"{rec.get('savings_percent', 0):.1f}%"])
            writer.writerow([])
        
        # Regional costs
        writer.writerow(['Regional Costs'])
        writer.writerow(['Region', 'Total Monthly Cost'])
        
        for region, data in comparison_data.get('regions', {}).items():
            if 'error' not in data:
                writer.writerow([region, f"${data.get('total', 0):.2f}"])
        
        return output.getvalue()
