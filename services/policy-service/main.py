"""
Policy Governance Service
Validates Terraform against security and compliance policies from database
"""

from flask import Flask, request, jsonify
import requests
import re
import os
from typing import Dict, List, Any

app = Flask(__name__)

API_GATEWAY = os.getenv('API_GATEWAY_URL', 'http://api-gateway:8000')

class PolicyEngine:
    """Policy validation engine"""
    
    def __init__(self):
        self.policies_cache = []
        self.cache_time = 0
    
    def _load_policies(self) -> List[Dict]:
        """Load policies from API gateway"""
        import time
        
        # Cache for 60 seconds
        if time.time() - self.cache_time < 60 and self.policies_cache:
            return self.policies_cache
        
        try:
            response = requests.get(f'{API_GATEWAY}/api/v1/policies', timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.policies_cache = [p for p in data.get('policies', []) if p.get('enabled')]
                self.cache_time = time.time()
                return self.policies_cache
        except Exception as e:
            print(f"⚠️ Failed to load policies from API: {e}")
        
        return []
    
    def _check_policy(self, policy: Dict, resource: Dict) -> bool:
        """Check if resource passes policy"""
        policy_id = policy['id']
        attrs = resource.get('attributes', {})
        
        # SEC-001: No Public S3 Buckets
        if policy_id == 'SEC-001':
            return attrs.get('acl') != 'public-read'
        
        # SEC-002: S3 Encryption Required
        if policy_id == 'SEC-002':
            return 'server_side_encryption_configuration' in attrs
        
        # SEC-003: No Public EC2 Instances
        if policy_id == 'SEC-003':
            return not attrs.get('associate_public_ip_address', False)
        
        # SEC-004: RDS Encryption Required
        if policy_id == 'SEC-004':
            return attrs.get('storage_encrypted', False)
        
        # SEC-005: RDS Public Access Disabled
        if policy_id == 'SEC-005':
            return not attrs.get('publicly_accessible', False)
        
        # COST-001: EC2 Instance Size Limit
        if policy_id == 'COST-001':
            instance_type = attrs.get('instance_type', '')
            allowed = policy.get('config', {}).get('allowed', [])
            return instance_type in allowed if allowed else True
        
        # COST-002: RDS Instance Size Limit
        if policy_id == 'COST-002':
            instance_class = attrs.get('instance_class', '')
            allowed = policy.get('config', {}).get('allowed', [])
            return instance_class in allowed if allowed else True
        
        # COMP-001: Required Tags Present
        if policy_id == 'COMP-001':
            tags = attrs.get('tags', {})
            required = policy.get('config', {}).get('required_tags', [])
            return all(tag in tags for tag in required)
        
        return True
    
    def validate(self, resources: List[Dict], total_cost: float = 0, repo: str = None) -> Dict[str, Any]:
        """Validate resources against all policies"""
        policies = self._load_policies()
        violations = []
        passed = []
        
        # Check cost limit policies first
        for policy in policies:
            if policy['category'] == 'budget' and policy['id'].startswith('BUDGET-'):
                try:
                    cost_limit = float(policy.get('config', {}).get('monthly_limit', 0))
                    if cost_limit > 0 and total_cost > cost_limit:
                        violations.append({
                            'policy_id': policy['id'],
                            'policy_name': policy['name'],
                            'severity': policy['severity'],
                            'resource': 'total_infrastructure',
                            'category': 'budget',
                            'message': f"Total cost ${total_cost:.2f} exceeds limit ${cost_limit:.2f}"
                        })
                except Exception as e:
                    print(f"Error checking budget policy {policy['id']}: {e}")
        
        # Check resource-level policies
        for resource in resources:
            resource_type = resource.get('type')
            resource_name = resource.get('name')
            
            for policy in policies:
                # Skip budget policies (already checked)
                if policy['category'] == 'budget':
                    continue
                    
                # Skip if policy doesn't apply to this resource type
                if policy['resource_type'] != 'all' and policy['resource_type'] != resource_type:
                    continue
                
                try:
                    if not self._check_policy(policy, resource):
                        violations.append({
                            'policy_id': policy['id'],
                            'policy_name': policy['name'],
                            'severity': policy['severity'],
                            'resource': f"{resource_type}.{resource_name}",
                            'category': policy['category']
                        })
                    else:
                        passed.append({
                            'policy_id': policy['id'],
                            'resource': f"{resource_type}.{resource_name}"
                        })
                except Exception as e:
                    print(f"Error checking policy {policy['id']}: {e}")
        
        return {
            'violations': violations,
            'passed_count': len(passed),
            'violation_count': len(violations),
            'status': 'failed' if violations else 'passed'
        }

# Initialize policy engine
policy_engine = PolicyEngine()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'service': 'policy-service', 'status': 'healthy'})

@app.route('/api/v1/validate', methods=['POST'])
def validate():
    """Validate resources against policies"""
    try:
        data = request.get_json()
        resources = data.get('resources', [])
        total_cost = data.get('total_cost', 0)
        repo = data.get('repo')
        
        if not resources:
            return jsonify({'error': 'No resources provided'}), 400
        
        result = policy_engine.validate(resources, total_cost, repo)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/policies', methods=['GET'])
def list_policies():
    """List all available policies"""
    policies = policy_engine._load_policies()
    return jsonify({'policies': policies, 'count': len(policies)})

if __name__ == '__main__':
    print("🔒 Policy Governance Service Starting...")
    print(f"📡 API Gateway: {API_GATEWAY}")
    
    app.run(host='0.0.0.0', port=8004, debug=True)
