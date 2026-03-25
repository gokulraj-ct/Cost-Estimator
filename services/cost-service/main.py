"""
Cost Calculation Service
Calculates AWS infrastructure costs using Plugin System
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from decimal import Decimal
import os
import redis
import json

# Import AWS Pricing Service
from aws_pricing import get_pricing_service

# Import Plugin System
from plugins import initialize_plugins
from plugins.registry import get_registry

# Import optimization features
from region_comparator import RegionComparator
from cost_optimizer import CostOptimizer
from report_exporter import ReportExporter
from flask import make_response

app = Flask(__name__)
CORS(app)

# Redis connection
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)

# Check if AWS Pricing API should be used
USE_AWS_PRICING = os.getenv('USE_AWS_PRICING', 'true').lower() == 'true'

# Initialize pricing service
pricing_service = get_pricing_service() if USE_AWS_PRICING else None

# Initialize plugin system
plugin_registry = initialize_plugins(pricing_service)

# Initialize optimization features
region_comparator = RegionComparator(plugin_registry)
cost_optimizer = CostOptimizer(plugin_registry)
report_exporter = ReportExporter()

# Fallback pricing (used if AWS API fails)
PRICING = {
    'ec2': {
        't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416,
        't3.large': 0.0832, 't3.xlarge': 0.1664,
    },
    'rds': {
        'db.t3.micro': 0.017, 'db.t3.small': 0.034,
        'db.t3.medium': 0.068, 'db.t3.large': 0.136,
    },
    's3_storage': 0.023,
    'ebs_gp3': 0.08,
    'lb': 0.0225,
    'nat_gateway': 0.045,
}


def calculate_resource_cost(resource):
    """Calculate cost for a single resource using plugin system"""
    resource_type = resource['type']
    attrs = resource.get('attributes', {})
    region = resource.get('region', 'us-east-1')
    
    try:
        return plugin_registry.calculate_cost(resource_type, attrs, region)
    except ValueError as e:
        raise ValueError(f"{resource_type}.{resource['name']}: {str(e)}")
    except Exception as e:
        raise Exception(f"{resource_type}.{resource['name']}: {str(e)}")
    
    return 0


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'cost-service'})


@app.route('/api/v1/plugins', methods=['GET'])
def list_plugins():
    """List all available resource plugins"""
    plugins = plugin_registry.list_plugins()
    return jsonify({
        'plugins': plugins,
        'count': len(plugins)
    })


@app.route('/api/v1/compare-regions', methods=['POST'])
def compare_regions():
    """Compare costs across AWS regions"""
    data = request.json
    resources = data.get('resources', [])
    
    if not resources:
        return jsonify({'error': 'No resources provided'}), 400
    
    try:
        comparison = region_comparator.compare_regions(resources)
        return jsonify(comparison)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/optimize', methods=['POST'])
def optimize_costs():
    """Get cost optimization suggestions"""
    data = request.json
    resources = data.get('resources', [])
    region = data.get('region', 'us-east-1')
    
    if not resources:
        return jsonify({'error': 'No resources provided'}), 400
    
    try:
        suggestions = cost_optimizer.analyze(resources, region)
        return jsonify(suggestions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/export/csv', methods=['POST'])
def export_csv():
    """Export estimate to CSV"""
    data = request.json
    csv_data = report_exporter.export_csv(data)
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=cost-estimate.csv'
    return response


@app.route('/api/v1/export/optimization-csv', methods=['POST'])
def export_optimization_csv():
    """Export optimization suggestions to CSV"""
    data = request.json
    csv_data = report_exporter.export_optimization_csv(data)
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=optimization-report.csv'
    return response


@app.route('/api/v1/export/region-comparison-csv', methods=['POST'])
def export_region_comparison_csv():
    """Export region comparison to CSV"""
    data = request.json
    csv_data = report_exporter.export_region_comparison_csv(data)
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=region-comparison.csv'
    return response


@app.route('/api/v1/calculate', methods=['POST'])
def calculate():
    """
    Calculate costs for resources
    
    Request:
    {
        "resources": [...],
        "region": "us-east-1"
    }
    
    Response:
    {
        "total_monthly_cost": 245.50,
        "breakdown": [...]
    }
    """
    data = request.json
    resources = data.get('resources', [])
    region = data.get('region', 'us-east-1')
    
    total = 0
    breakdown = []
    
    for resource in resources:
        try:
            cost = calculate_resource_cost(resource)
            total += cost
            
            breakdown.append({
                'resource': f"{resource['type']}.{resource['name']}",
                'type': resource['type'],
                'monthly_cost': round(cost, 2),
                'details': {
                    'instance_type': resource.get('attributes', {}).get('instance_type', 'N/A')
                }
            })
        except ValueError as e:
            return jsonify({'error': str(e), 'resource': resource['name']}), 400
        except Exception as e:
            return jsonify({'error': f"Failed to calculate cost: {str(e)}", 'resource': resource['name']}), 500
    
    result = {
        'total_monthly_cost': round(total, 2),
        'currency': 'USD',
        'region': region,
        'breakdown': breakdown,
        'resource_count': len(resources)
    }
    
    return jsonify(result)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8002))
    print(f"🚀 Cost Service starting on port {port}")
    
    if USE_AWS_PRICING:
        print("💰 AWS Pricing API: ENABLED")
        if pricing_service and pricing_service.enabled:
            print("   ✅ Connected to AWS Pricing API")
        else:
            print("   ⚠️  Fallback to static pricing")
    else:
        print("💰 AWS Pricing API: DISABLED (using static pricing)")
    
    app.run(host='0.0.0.0', port=port, debug=True)
