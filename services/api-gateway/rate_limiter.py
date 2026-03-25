"""
Simple Rate Limiting
"""
import time
from functools import wraps
from flask import request, jsonify
import redis
import os

# Redis connection
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)

# Rate limits by tier
RATE_LIMITS = {
    'free': {'requests': 10, 'window': 60},      # 10 requests per minute
    'premium': {'requests': 100, 'window': 60},  # 100 requests per minute
    'unlimited': {'requests': 10000, 'window': 60}
}

def rate_limit(f):
    """Decorator for rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if rate limiting is disabled
        if os.getenv('DISABLE_RATE_LIMIT', 'false').lower() == 'true':
            return f(*args, **kwargs)
        
        # Get user tier
        tier = getattr(request, 'api_user', {}).get('tier', 'free')
        limit_config = RATE_LIMITS.get(tier, RATE_LIMITS['free'])
        
        # Get client identifier (API key or IP)
        api_key = request.headers.get('X-API-Key', request.remote_addr)
        key = f"rate_limit:{api_key}"
        
        try:
            # Get current count
            current = redis_client.get(key)
            
            if current is None:
                # First request in window
                redis_client.setex(key, limit_config['window'], 1)
                remaining = limit_config['requests'] - 1
            else:
                current = int(current)
                
                if current >= limit_config['requests']:
                    # Rate limit exceeded
                    ttl = redis_client.ttl(key)
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f"Try again in {ttl} seconds",
                        'limit': limit_config['requests'],
                        'window': limit_config['window']
                    }), 429
                
                # Increment counter
                redis_client.incr(key)
                remaining = limit_config['requests'] - current - 1
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            
            # If response is already a Response object, just add headers and return
            from flask import Response as FlaskResponse
            if isinstance(response, FlaskResponse):
                response.headers['X-RateLimit-Limit'] = str(limit_config['requests'])
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Reset'] = str(int(time.time()) + limit_config['window'])
                return response
            
            # Handle tuple responses (response, status_code)
            if isinstance(response, tuple) and len(response) >= 2:
                return response
            
            # Return as-is for other types
            return response
            
        except redis.RedisError:
            # If Redis fails, allow request (fail open)
            return f(*args, **kwargs)
    
    return decorated_function
