"""
GitHub Bot Service
Handles GitHub webhooks and posts cost estimates on PRs
"""

from flask import Flask, request, jsonify
import requests
import hmac
import hashlib
import os
import json

app = Flask(__name__)

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # Fallback global token
GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET')
API_GATEWAY_URL = os.getenv('API_GATEWAY_URL', 'http://api-gateway:8000')

def get_repo_token(repo_full_name):
    """Get GitHub token for specific repo from integrations"""
    try:
        response = requests.get(
            f'{API_GATEWAY_URL}/api/v1/integrations/{repo_full_name}',
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            # Return repo-specific token if exists, otherwise fallback to global
            return data.get('github_token') or GITHUB_TOKEN
    except:
        pass
    
    return GITHUB_TOKEN

def get_repo_region(repo_full_name):
    """Get default region for specific repo from integrations"""
    try:
        response = requests.get(
            f'{API_GATEWAY_URL}/api/v1/integrations/{repo_full_name}',
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('default_region', 'us-east-1')
    except:
        pass
    
    return 'us-east-1'

def verify_signature(payload_body, signature_header):
    """Verify GitHub webhook signature"""
    if not GITHUB_WEBHOOK_SECRET:
        return True  # Skip verification if no secret
    
    hash_object = hmac.new(
        GITHUB_WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(expected_signature, signature_header)

def get_terraform_files(repo_full_name, pr_number, ref):
    """Fetch Terraform files from PR"""
    token = get_repo_token(repo_full_name)
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get PR files
    url = f'https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files'
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return []
    
    files = []
    for file in response.json():
        # Only process .tf files
        if file['filename'].endswith('.tf') and file['status'] != 'removed':
            # Get file content
            content_url = file['raw_url']
            content_response = requests.get(content_url, headers=headers)
            
            if content_response.status_code == 200:
                files.append({
                    'name': file['filename'],
                    'content': content_response.text,
                    'status': file['status']  # added, modified, unchanged
                })
    
    return files

def get_base_terraform_files(repo_full_name, base_ref):
    """Fetch Terraform files from base branch"""
    token = get_repo_token(repo_full_name)
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get repository tree
    url = f'https://api.github.com/repos/{repo_full_name}/git/trees/{base_ref}?recursive=1'
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return []
    
    files = []
    tree = response.json().get('tree', [])
    
    for item in tree:
        if item['path'].endswith('.tf') and item['type'] == 'blob':
            # Get file content
            content_url = f'https://raw.githubusercontent.com/{repo_full_name}/{base_ref}/{item["path"]}'
            content_response = requests.get(content_url, headers=headers)
            
            if content_response.status_code == 200:
                files.append({
                    'name': item['path'],
                    'content': content_response.text
                })
    
    return files

def post_pr_comment(repo_full_name, pr_number, comment):
    """Post comment on GitHub PR"""
    token = get_repo_token(repo_full_name)
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = f'https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments'
    data = {'body': comment}
    
    response = requests.post(url, headers=headers, json=data)
    return response.status_code == 201

def format_cost_comment(pr_estimate, base_estimate=None):
    """Format cost estimate as GitHub comment with comparison and policy violations"""
    if 'error' in pr_estimate:
        return f"""## 💰 Kostructure Cost Estimate

⚠️ **Error**: {pr_estimate['error']}

Please check your Terraform files or contact support.
"""
    
    total_cost = pr_estimate.get('total_monthly_cost', 0)
    region = pr_estimate.get('region', 'us-east-1')
    resource_count = pr_estimate.get('resource_count', 0)
    breakdown = pr_estimate.get('breakdown', [])
    policy_validation = pr_estimate.get('policy_validation', {})
    
    # Calculate difference if base estimate exists
    cost_diff = 0
    if base_estimate and 'total_monthly_cost' in base_estimate:
        base_cost = base_estimate['total_monthly_cost']
        cost_diff = total_cost - base_cost
    
    comment = f"""## 💰 Kostructure Cost Estimate

### Monthly Cost: **${total_cost:.2f}**"""
    
    if base_estimate:
        if cost_diff > 0:
            comment += f" 📈 **+${cost_diff:.2f}** increase"
        elif cost_diff < 0:
            comment += f" 📉 **${abs(cost_diff):.2f}** decrease"
        else:
            comment += f" ➡️ **No change**"
    
    comment += f"""

📍 **Region**: {region}
📦 **Resources**: {resource_count}

"""
    
    # Add policy validation results
    if policy_validation:
        violations = policy_validation.get('violations', [])
        violation_count = policy_validation.get('violation_count', 0)
        status = policy_validation.get('status', 'unknown')
        
        if status == 'passed':
            comment += "### 🔒 Policy Validation: ✅ **PASSED**\n\n"
        else:
            comment += f"### 🔒 Policy Validation: ⚠️ **{violation_count} VIOLATIONS**\n\n"
            
            if violations:
                # Group by severity
                critical = [v for v in violations if v['severity'] == 'critical']
                high = [v for v in violations if v['severity'] == 'high']
                medium = [v for v in violations if v['severity'] == 'medium']
                low = [v for v in violations if v['severity'] == 'low']
                
                if critical:
                    comment += "#### 🚨 Critical\n"
                    for v in critical:
                        comment += f"- **{v['policy_name']}** ({v['policy_id']})\n"
                        comment += f"  - Resource: `{v['resource']}`\n"
                
                if high:
                    comment += "#### ⚠️ High\n"
                    for v in high:
                        comment += f"- **{v['policy_name']}** ({v['policy_id']})\n"
                        comment += f"  - Resource: `{v['resource']}`\n"
                
                if medium:
                    comment += "#### ⚡ Medium\n"
                    for v in medium:
                        comment += f"- **{v['policy_name']}** ({v['policy_id']})\n"
                        comment += f"  - Resource: `{v['resource']}`\n"
                
                if low:
                    comment += "#### ℹ️ Low\n"
                    for v in low:
                        comment += f"- **{v['policy_name']}** ({v['policy_id']})\n"
                        comment += f"  - Resource: `{v['resource']}`\n"
                
                comment += "\n"
    
    if breakdown:
        comment += "### Resource Breakdown\n\n"
        comment += "| Resource | Type | Monthly Cost |\n"
        comment += "|----------|------|-------------|\n"
        
        for item in breakdown:
            resource = item.get('resource', 'Unknown')
            resource_type = item.get('type', 'Unknown')
            cost = item.get('monthly_cost', 0)
            comment += f"| `{resource}` | {resource_type} | ${cost:.2f} |\n"
    
    comment += "\n---\n*Powered by Kostructure*"
    return comment


def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'service': 'github-bot'})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle GitHub webhook events"""
    
    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_signature(request.data, signature):
        return jsonify({'error': 'Invalid signature'}), 403
    
    event = request.headers.get('X-GitHub-Event')
    payload = request.json
    
    # Only handle pull request events
    if event != 'pull_request':
        return jsonify({'message': 'Event ignored'}), 200
    
    action = payload.get('action')
    
    # Only process opened and synchronize (new commits) events
    if action not in ['opened', 'synchronize']:
        return jsonify({'message': 'Action ignored'}), 200
    
    pr = payload['pull_request']
    repo_full_name = payload['repository']['full_name']
    pr_number = pr['number']
    ref = pr['head']['ref']
    base_ref = pr['base']['ref']
    
    print(f"Processing PR #{pr_number} in {repo_full_name}")
    
    # Get Terraform files from PR
    tf_files = get_terraform_files(repo_full_name, pr_number, ref)
    
    if not tf_files:
        print("No Terraform files found in PR")
        return jsonify({'message': 'No Terraform files found'}), 200
    
    print(f"Found {len(tf_files)} Terraform files in PR")
    
    # Get base branch estimate for comparison
    base_estimate = None
    try:
        base_files = get_base_terraform_files(repo_full_name, base_ref)
        if base_files:
            print(f"Found {len(base_files)} Terraform files in base branch")
            base_response = requests.post(
                f'{API_GATEWAY_URL}/api/v1/estimate',
                json={'files': base_files},
                timeout=30
            )
            if base_response.status_code == 200:
                base_estimate = base_response.json()
                print(f"Base branch cost: ${base_estimate.get('total_monthly_cost', 0):.2f}")
    except Exception as e:
        print(f"Could not get base estimate: {e}")
    
    # Call cost estimation API for PR
    try:
        response = requests.post(
            f'{API_GATEWAY_URL}/api/v1/estimate',
            json={'files': tf_files},
            timeout=30
        )
        
        if response.status_code == 200:
            pr_estimate = response.json()
            print(f"PR cost: ${pr_estimate.get('total_monthly_cost', 0):.2f}")
        else:
            pr_estimate = {'error': f'API returned status {response.status_code}'}
    
    except Exception as e:
        pr_estimate = {'error': str(e)}
    
    # Save PR estimate to database
    if 'estimate_id' in pr_estimate:
        try:
            pr_url = f"https://github.com/{repo_full_name}/pull/{pr_number}"
            pr_title = payload.get('pull_request', {}).get('title', '')
            policy_violations = pr_estimate.get('policy_validation', {})
            
            requests.post(
                f'{API_GATEWAY_URL}/api/v1/pr-estimates',
                json={
                    'estimate_id': pr_estimate['estimate_id'],
                    'repo_full_name': repo_full_name,
                    'pr_number': pr_number,
                    'pr_title': pr_title,
                    'pr_url': pr_url,
                    'policy_violations': policy_violations
                },
                timeout=10
            )
        except Exception as e:
            print(f"Failed to save PR estimate: {e}")
    
    # Format and post comment with comparison
    comment = format_cost_comment(pr_estimate, base_estimate)
    success = post_pr_comment(repo_full_name, pr_number, comment)
    
    if success:
        print(f"Posted comment on PR #{pr_number}")
        return jsonify({'message': 'Comment posted successfully'}), 200
    else:
        print(f"Failed to post comment on PR #{pr_number}")
        return jsonify({'error': 'Failed to post comment'}), 500

if __name__ == '__main__':
    if not GITHUB_TOKEN:
        print("WARNING: GITHUB_TOKEN not set")
    
    port = int(os.getenv('PORT', 8003))
    print(f"🤖 GitHub Bot starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
