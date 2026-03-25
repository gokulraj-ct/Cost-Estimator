# Authentication & Rate Limiting

## ✅ Features Implemented

### 1. API Key Authentication
- Header-based authentication (`X-API-Key`)
- Simple key validation
- User tier support (free, premium)
- Can be disabled for development

### 2. Rate Limiting
- Redis-based rate limiting
- Per-user/per-IP limits
- Tier-based limits:
  - **Free**: 10 requests/minute
  - **Premium**: 100 requests/minute
- Rate limit headers in response
- Graceful degradation (fails open if Redis down)

---

## Configuration

### Environment Variables
```bash
DISABLE_AUTH=true          # Disable auth (for web UI)
DISABLE_RATE_LIMIT=false   # Enable rate limiting
```

### Demo API Keys
```
demo-key-12345  # Free tier (10 req/min)
prod-key-67890  # Premium tier (100 req/min)
```

---

## Usage Examples

### With API Key (Auth Enabled)
```bash
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-12345" \
  -d '{
    "files": [{
      "name": "main.tf",
      "content": "resource \"aws_instance\" \"web\" { instance_type = \"t3.medium\" }"
    }]
  }'
```

### Without API Key (Auth Disabled - Default)
```bash
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "files": [{
      "name": "main.tf",
      "content": "resource \"aws_instance\" \"web\" { instance_type = \"t3.medium\" }"
    }]
  }'
```

---

## Rate Limit Response Headers

```
X-RateLimit-Limit: 10           # Max requests per window
X-RateLimit-Remaining: 7        # Remaining requests
X-RateLimit-Reset: 1710752400   # Unix timestamp when limit resets
```

---

## Error Responses

### 401 Unauthorized (Missing API Key)
```json
{
  "error": "API key required",
  "message": "Include X-API-Key header"
}
```

### 403 Forbidden (Invalid API Key)
```json
{
  "error": "Invalid API key"
}
```

### 429 Too Many Requests (Rate Limit Exceeded)
```json
{
  "error": "Rate limit exceeded",
  "message": "Try again in 45 seconds",
  "limit": 10,
  "window": 60
}
```

---

## How It Works

### Authentication Flow
1. Request arrives with `X-API-Key` header
2. If `DISABLE_AUTH=true`, skip validation
3. Validate API key against known keys
4. Attach user info to request
5. Proceed to rate limiting

### Rate Limiting Flow
1. Get user tier (free/premium) or use IP
2. Check Redis for current request count
3. If under limit, increment and proceed
4. If over limit, return 429 error
5. Add rate limit headers to response

---

## Production Setup

### 1. Enable Authentication
```bash
# In docker-compose.yml or .env
DISABLE_AUTH=false
```

### 2. Generate API Keys
```python
import secrets
key = f"kos_{secrets.token_urlsafe(32)}"
print(key)
```

### 3. Store Keys in Database
Replace the in-memory `API_KEYS` dict with database storage:
```python
# In auth.py
def get_api_key_from_db(key):
    # Query PostgreSQL
    pass
```

### 4. Add User Management
- User registration
- API key generation
- Key rotation
- Usage analytics

---

## Testing

### Test Rate Limiting
```bash
# Make 12 requests (limit is 10)
for i in {1..12}; do
  echo "Request $i"
  curl -X POST http://localhost:8000/api/v1/estimate \
    -H "Content-Type: application/json" \
    -d '{"files":[{"name":"test.tf","content":"resource \"aws_instance\" \"web\" { instance_type = \"t3.micro\" }"}]}'
  sleep 0.5
done
```

Expected: First 10 succeed, last 2 fail with 429

### Test Authentication
```bash
# Without API key (should fail if auth enabled)
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{"files":[]}'

# With valid API key
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-12345" \
  -d '{"files":[]}'
```

---

## Current Status

✅ **Authentication**: Implemented, DISABLED by default (for web UI)
✅ **Rate Limiting**: Implemented, ENABLED by default
✅ **Redis Integration**: Working
✅ **Tier Support**: Free (10/min), Premium (100/min)

---

## Next Steps (Optional)

1. **Database-backed API keys** - Store in PostgreSQL
2. **JWT tokens** - For session-based auth
3. **OAuth2** - For third-party integrations
4. **Usage analytics** - Track API usage per user
5. **Billing integration** - Charge based on usage
6. **API key rotation** - Automatic key expiry
7. **Webhook authentication** - HMAC signatures

---

## Why Auth is Disabled by Default

The web UI (http://localhost:3000) makes direct API calls from the browser. 
If auth is enabled, the web UI would need to:
1. Store API keys (insecure in browser)
2. Implement login flow
3. Use backend proxy

For development, auth is disabled. For production:
- Enable auth
- Add backend proxy for web UI
- Or use API keys only for programmatic access
