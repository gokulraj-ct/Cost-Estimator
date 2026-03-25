"""
Simple API Key Authentication
"""
import os
import hashlib
from functools import wraps
from flask import request, jsonify

# Simple API keys (in production, use database)
API_KEYS = {
    'demo-key-12345': {'name': 'Demo User', 'tier': 'free'},
    'prod-key-67890': {'name': 'Production User', 'tier': 'premium'}
}

def generate_api_key(name):
    """Generate a new API key"""
    import secrets
    key = f"kos_{secrets.token_urlsafe(32)}"
    return key

def require_api_key(f):
    """Decorator to require API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if auth is disabled
        if os.getenv('DISABLE_AUTH', 'false').lower() == 'true':
            return f(*args, **kwargs)
        
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key required', 'message': 'Include X-API-Key header'}), 401
        
        # Validate API key
        if api_key not in API_KEYS:
            return jsonify({'error': 'Invalid API key'}), 403
        
        # Add user info to request
        request.api_user = API_KEYS[api_key]
        
        return f(*args, **kwargs)
    
    return decorated_function
