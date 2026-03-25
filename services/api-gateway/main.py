"""
API Gateway
Routes requests to microservices and handles database operations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import psycopg2
import json
import uuid
import os
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# Service URLs
PARSER_SERVICE = os.getenv('PARSER_SERVICE_URL', 'http://localhost:8001')
COST_SERVICE = os.getenv('COST_SERVICE_URL', 'http://localhost:8002')
POLICY_SERVICE = os.getenv('POLICY_SERVICE_URL', 'http://localhost:8004')

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'kostructure'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres')
    )


def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS estimates (
            id VARCHAR(50) PRIMARY KEY,
            total_monthly_cost DECIMAL(10,2) NOT NULL,
            currency VARCHAR(3) DEFAULT 'USD',
            region VARCHAR(50) NOT NULL,
            resources JSONB NOT NULL,
            breakdown JSONB NOT NULL,
            resource_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS policies (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            severity VARCHAR(20) NOT NULL,
            category VARCHAR(50) NOT NULL,
            resource_type VARCHAR(100) NOT NULL,
            enabled BOOLEAN DEFAULT true,
            config JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pr_estimates (
            id SERIAL PRIMARY KEY,
            estimate_id VARCHAR(50) REFERENCES estimates(id),
            repo_full_name VARCHAR(255) NOT NULL,
            pr_number INTEGER NOT NULL,
            pr_title TEXT,
            pr_url TEXT,
            policy_violations JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(repo_full_name, pr_number)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS integrations (
            id SERIAL PRIMARY KEY,
            repo_full_name VARCHAR(255) NOT NULL UNIQUE,
            github_token TEXT,
            default_region VARCHAR(50) DEFAULT 'us-east-1',
            description TEXT,
            settings JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cur.execute('''
        CREATE INDEX IF NOT EXISTS idx_created_at 
        ON estimates(created_at DESC)
    ''')
    
    # Seed default policies
    cur.execute("SELECT COUNT(*) FROM policies")
    if cur.fetchone()[0] == 0:
        default_policies = [
            ('SEC-001', 'No Public S3 Buckets', 'S3 buckets should not be publicly accessible', 'high', 'security', 'aws_s3_bucket', True, '{"check": "acl != public-read"}'),
            ('SEC-002', 'S3 Encryption Required', 'S3 buckets must have encryption enabled', 'high', 'security', 'aws_s3_bucket', True, '{"check": "server_side_encryption_configuration exists"}'),
            ('SEC-003', 'No Public EC2 Instances', 'EC2 instances should not have public IPs', 'medium', 'security', 'aws_instance', True, '{"check": "associate_public_ip_address != true"}'),
            ('SEC-004', 'RDS Encryption Required', 'RDS instances must be encrypted', 'high', 'security', 'aws_db_instance', True, '{"check": "storage_encrypted == true"}'),
            ('SEC-005', 'RDS Public Access Disabled', 'RDS instances must not be publicly accessible', 'critical', 'security', 'aws_db_instance', True, '{"check": "publicly_accessible != true"}'),
            ('COST-001', 'EC2 Instance Size Limit', 'EC2 instances should use approved sizes', 'medium', 'cost', 'aws_instance', True, '{"allowed": ["t3.micro", "t3.small", "t3.medium", "m5.large"]}'),
            ('COST-002', 'RDS Instance Size Limit', 'RDS instances should use approved sizes', 'medium', 'cost', 'aws_db_instance', True, '{"allowed": ["db.t3.micro", "db.t3.small", "db.t3.medium"]}'),
            ('BUDGET-001', 'Monthly Cost Limit - Development', 'Development environments should not exceed $100/month', 'high', 'budget', 'all', True, '{"monthly_limit": 100}'),
            ('BUDGET-002', 'Monthly Cost Limit - Production', 'Production environments should not exceed $500/month', 'critical', 'budget', 'all', False, '{"monthly_limit": 500}'),
            ('COMP-001', 'Required Tags Present', 'Resources must have required tags', 'low', 'compliance', 'all', True, '{"required_tags": ["Environment", "Owner", "Project"]}')
        ]
        
        for policy in default_policies:
            cur.execute('''
                INSERT INTO policies (id, name, description, severity, category, resource_type, enabled, config)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            ''', policy)
    
    conn.commit()
    cur.close()
    conn.close()


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'api-gateway',
        'version': '0.1.0'
    })


@app.route('/api/v1/estimate', methods=['POST'])
def estimate():
    """
    Main endpoint: Parse Terraform and calculate costs
    
    Request:
    {
        "files": [{"name": "main.tf", "content": "..."}],
        "region": "us-east-1"
    }
    """
    try:
        data = request.json
        files = data.get('files', [])
        default_region = data.get('region', 'us-east-1')
        
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        # Step 1: Parse Terraform files
        parse_response = requests.post(
            f'{PARSER_SERVICE}/api/v1/parse',
            json={'files': files, 'region': default_region}
        )
        
        if parse_response.status_code != 200:
            return jsonify({'error': 'Parser service error'}), 500
        
        parse_data = parse_response.json()
        resources = parse_data.get('resources', [])
        
        # Use region from first resource (from provider block), fallback to default
        region = default_region if default_region else 'us-east-1'
        if resources and resources[0].get('region'):
            region = resources[0]['region']
        
        if not resources:
            return jsonify({
                'estimate_id': f"est_{uuid.uuid4().hex[:8]}",
                'total_monthly_cost': 0,
                'currency': 'USD',
                'region': region,
                'resource_count': 0,
                'resources': [],
                'breakdown': [],
                'policy_validation': {'status': 'passed', 'violations': []},
                'message': 'No AWS resources found'
            })
        
        # Step 2: Calculate costs FIRST
        cost_response = requests.post(
            f'{COST_SERVICE}/api/v1/calculate',
            json={'resources': resources, 'region': region}
        )
        
        if cost_response.status_code != 200:
            return jsonify({'error': 'Cost service error'}), 500
        
        cost_data = cost_response.json()
        
        # Step 3: Validate policies (now we have cost_data)
        policy_data = {}
        try:
            policy_response = requests.post(
                f'{POLICY_SERVICE}/api/v1/validate',
                json={
                    'resources': resources,
                    'total_cost': cost_data.get('total_monthly_cost', 0),
                    'repo': data.get('repo')
                },
                timeout=5
            )
            
            if policy_response.status_code == 200:
                policy_data = policy_response.json()
                print(f"✅ Policy validation: {policy_data.get('status')} - {policy_data.get('violation_count', 0)} violations")
            else:
                print(f"⚠️ Policy service returned {policy_response.status_code}")
        except Exception as e:
            print(f"⚠️ Policy validation failed: {e}")
            policy_data = {'status': 'error', 'violations': [], 'violation_count': 0}
        
        # Step 4: Save to database
        estimate_id = f"est_{uuid.uuid4().hex[:8]}"
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            INSERT INTO estimates 
            (id, total_monthly_cost, currency, region, resources, breakdown, resource_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            estimate_id,
            cost_data['total_monthly_cost'],
            cost_data['currency'],
            region,
            json.dumps(resources),
            json.dumps(cost_data['breakdown']),
            cost_data['resource_count']
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Return response
        return jsonify({
            'estimate_id': estimate_id,
            'total_monthly_cost': cost_data['total_monthly_cost'],
            'currency': cost_data['currency'],
            'region': region,
            'resource_count': cost_data['resource_count'],
            'resources': resources,
            'breakdown': cost_data['breakdown'],
            'policy_validation': policy_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/estimates/<estimate_id>', methods=['GET'])
def get_estimate(estimate_id):
    """Get estimate by ID"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT * FROM estimates WHERE id = %s', (estimate_id,))
        row = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Estimate not found'}), 404
        
        return jsonify({
            'estimate_id': row[0],
            'total_monthly_cost': float(row[1]),
            'currency': row[2],
            'region': row[3],
            'resources': row[4],
            'breakdown': row[5],
            'resource_count': row[6],
            'created_at': row[7].isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/estimates', methods=['GET'])
def list_estimates():
    """List recent estimates"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT id, total_monthly_cost, currency, region, resource_count, created_at
            FROM estimates
            ORDER BY created_at DESC
            LIMIT %s
        ''', (limit,))
        
        rows = cur.fetchall()
        
        estimates = [{
            'estimate_id': row[0],
            'total_monthly_cost': float(row[1]),
            'currency': row[2],
            'region': row[3],
            'resource_count': row[4],
            'created_at': row[5].isoformat()
        } for row in rows]
        
        cur.execute('SELECT COUNT(*) FROM estimates')
        total = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return jsonify({'estimates': estimates, 'total': total})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/v1/policies', methods=['GET'])
def list_policies():
    """List all policies"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT id, name, description, severity, category, resource_type, enabled, config
            FROM policies
            ORDER BY category, severity DESC
        ''')
        
        policies = []
        for row in cur.fetchall():
            policies.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'severity': row[3],
                'category': row[4],
                'resource_type': row[5],
                'enabled': row[6],
                'config': row[7]
            })
        
        cur.close()
        conn.close()
        
        return jsonify({'policies': policies, 'count': len(policies)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/policies/<policy_id>', methods=['PUT'])
def update_policy(policy_id):
    """Update policy (enable/disable or modify)"""
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor()
        
        updates = []
        values = []
        
        if 'enabled' in data:
            updates.append('enabled = %s')
            values.append(data['enabled'])
        
        if 'severity' in data:
            updates.append('severity = %s')
            values.append(data['severity'])
        
        if 'config' in data:
            updates.append('config = %s::jsonb')
            values.append(json.dumps(data['config']))
        
        updates.append('updated_at = CURRENT_TIMESTAMP')
        values.append(policy_id)
        
        cur.execute(f'''
            UPDATE policies
            SET {', '.join(updates)}
            WHERE id = %s
        ''', values)
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'policy_id': policy_id})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/pr-estimates', methods=['GET'])
def list_pr_estimates():
    """List all PR estimates"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT 
                pr.id, pr.repo_full_name, pr.pr_number, pr.pr_title, pr.pr_url,
                e.total_monthly_cost, e.currency, e.region, e.resource_count,
                pr.policy_violations, pr.created_at
            FROM pr_estimates pr
            JOIN estimates e ON pr.estimate_id = e.id
            ORDER BY pr.created_at DESC
            LIMIT 50
        ''')
        
        estimates = []
        for row in cur.fetchall():
            estimates.append({
                'id': row[0],
                'repo': row[1],
                'pr_number': row[2],
                'pr_title': row[3],
                'pr_url': row[4],
                'total_cost': float(row[5]),
                'currency': row[6],
                'region': row[7],
                'resource_count': row[8],
                'policy_violations': row[9],
                'created_at': row[10].isoformat()
            })
        
        cur.close()
        conn.close()
        
        return jsonify({'estimates': estimates, 'count': len(estimates)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/pr-estimates', methods=['POST'])
def save_pr_estimate():
    """Save PR estimate"""
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            INSERT INTO pr_estimates 
            (estimate_id, repo_full_name, pr_number, pr_title, pr_url, policy_violations)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (repo_full_name, pr_number) 
            DO UPDATE SET 
                estimate_id = EXCLUDED.estimate_id,
                pr_title = EXCLUDED.pr_title,
                pr_url = EXCLUDED.pr_url,
                policy_violations = EXCLUDED.policy_violations,
                created_at = CURRENT_TIMESTAMP
        ''', (
            data['estimate_id'],
            data['repo_full_name'],
            data['pr_number'],
            data.get('pr_title', ''),
            data.get('pr_url', ''),
            json.dumps(data.get('policy_violations', {}))
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/policies')
def policies_page():
    """Serve policy management page"""
    return app.send_static_file('policies.html')

@app.route('/pr-estimates')
def pr_estimates_page():
    """Serve PR estimates page"""
    return app.send_static_file('pr-estimates.html')



# ============================================
# INTEGRATIONS ENDPOINTS
# ============================================

@app.route('/api/v1/integrations', methods=['GET'])
def get_integrations():
    """Get all integrations"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT id, repo_full_name, default_region, description, 
               settings, created_at, updated_at
        FROM integrations
        ORDER BY created_at DESC
    ''')
    
    integrations = []
    for row in cur.fetchall():
        integrations.append({
            'id': row[0],
            'repo': row[1],
            'default_region': row[2],
            'description': row[3],
            'settings': row[4],
            'created_at': row[5].isoformat(),
            'updated_at': row[6].isoformat()
        })
    
    cur.close()
    conn.close()
    
    return jsonify({'integrations': integrations})


@app.route('/api/v1/integrations', methods=['POST'])
def create_integration():
    """Create new integration"""
    data = request.json
    repo = data.get('repo')
    token = data.get('token')
    region = data.get('region', 'us-east-1')
    description = data.get('description', '')
    
    if not repo:
        return jsonify({'error': 'repo is required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            INSERT INTO integrations (repo_full_name, github_token, default_region, description)
            VALUES (%s, %s, %s, %s)
            RETURNING id, repo_full_name, default_region, description, created_at
        ''', (repo, token, region, description))
        
        row = cur.fetchone()
        integration = {
            'id': row[0],
            'repo': row[1],
            'default_region': row[2],
            'description': row[3],
            'created_at': row[4].isoformat()
        }
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify(integration), 201
    except psycopg2.IntegrityError:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': 'Integration already exists'}), 409


@app.route('/api/v1/integrations/<repo_full_name>', methods=['GET'])
def get_integration(repo_full_name):
    """Get integration by repo name"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT id, repo_full_name, github_token, default_region, 
               description, settings, created_at, updated_at
        FROM integrations
        WHERE repo_full_name = %s
    ''', (repo_full_name,))
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        return jsonify({'error': 'Integration not found'}), 404
    
    return jsonify({
        'id': row[0],
        'repo': row[1],
        'has_token': bool(row[2]),
        'default_region': row[3],
        'description': row[4],
        'settings': row[5],
        'created_at': row[6].isoformat(),
        'updated_at': row[7].isoformat()
    })


@app.route('/api/v1/integrations/<repo_full_name>', methods=['PUT'])
def update_integration(repo_full_name):
    """Update integration"""
    data = request.json
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    updates = []
    params = []
    
    if 'token' in data:
        updates.append('github_token = %s')
        params.append(data['token'])
    
    if 'region' in data:
        updates.append('default_region = %s')
        params.append(data['region'])
    
    if 'description' in data:
        updates.append('description = %s')
        params.append(data['description'])
    
    if not updates:
        return jsonify({'error': 'No fields to update'}), 400
    
    updates.append('updated_at = CURRENT_TIMESTAMP')
    params.append(repo_full_name)
    
    cur.execute(f'''
        UPDATE integrations
        SET {', '.join(updates)}
        WHERE repo_full_name = %s
        RETURNING id
    ''', params)
    
    if cur.rowcount == 0:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': 'Integration not found'}), 404
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'message': 'Integration updated'})


@app.route('/api/v1/integrations/<repo_full_name>', methods=['DELETE'])
def delete_integration(repo_full_name):
    """Delete integration"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('DELETE FROM integrations WHERE repo_full_name = %s', (repo_full_name,))
    
    if cur.rowcount == 0:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': 'Integration not found'}), 404
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'message': 'Integration deleted'})


if __name__ == '__main__':
    print("🔧 Initializing database...")
    init_db()
    
    port = int(os.getenv('PORT', 8000))
    print(f"🚀 API Gateway starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
