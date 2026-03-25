# ✅ GitHub Integration - Already Implemented!

## What It Does

The GitHub bot automatically posts cost estimates as comments on Pull Requests when Terraform files are changed.

## Features

✅ **Webhook Handler** - Listens for GitHub PR events
✅ **Terraform File Detection** - Finds .tf files in PRs
✅ **Cost Calculation** - Calls Kostructure API
✅ **PR Comments** - Posts formatted cost estimate
✅ **Signature Verification** - Validates GitHub webhooks
✅ **Error Handling** - Graceful error messages

---

## How It Works

1. Developer opens/updates PR with Terraform changes
2. GitHub sends webhook to Kostructure bot
3. Bot fetches all .tf files from PR
4. Bot calls `/api/v1/estimate` endpoint
5. Bot posts formatted comment with cost breakdown

---

## Example PR Comment

```markdown
## 💰 Kostructure Cost Estimate

### Monthly Cost: **$129.49**

📍 **Region**: us-east-1
📦 **Resources**: 4

### Resource Breakdown

| Resource | Type | Monthly Cost |
|----------|------|-------------|
| aws_instance.web | aws_instance | $30.37 |
| aws_db_instance.database | aws_db_instance | $64.06 |
| aws_s3_bucket.assets | aws_s3_bucket | $2.20 |
| aws_lb.app | aws_lb | $32.86 |

---
*Estimated by [Kostructure](https://github.com/your-org/kostructure)*
```

---

## Setup Instructions

### 1. Create GitHub App/Token

**Option A: Personal Access Token (Quick)**
```bash
# Go to: https://github.com/settings/tokens
# Create token with permissions:
# - repo (full control)
# - write:discussion (for PR comments)
```

**Option B: GitHub App (Recommended for production)**
```bash
# Go to: https://github.com/settings/apps
# Create new GitHub App with:
# - Webhook URL: https://your-domain.com/webhook
# - Permissions: Pull requests (Read & Write)
# - Subscribe to: Pull request events
```

### 2. Configure Environment Variables

```bash
# Add to .env file
GITHUB_TOKEN=ghp_your_token_here
GITHUB_WEBHOOK_SECRET=your_webhook_secret
```

### 3. Set Up Webhook

**In your GitHub repository:**
1. Go to Settings → Webhooks → Add webhook
2. Payload URL: `https://your-domain.com/webhook`
3. Content type: `application/json`
4. Secret: (same as GITHUB_WEBHOOK_SECRET)
5. Events: Select "Pull requests"
6. Active: ✓

### 4. Restart Services

```bash
cd /home/gokul/kostructure
docker-compose up -d github-bot
```

---

## Testing Locally

### 1. Use ngrok for local testing

```bash
# Install ngrok
brew install ngrok  # or download from ngrok.com

# Start ngrok
ngrok http 8003

# Use the ngrok URL in GitHub webhook settings
# Example: https://abc123.ngrok.io/webhook
```

### 2. Test webhook manually

```bash
curl -X POST http://localhost:8003/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -d '{
    "action": "opened",
    "pull_request": {
      "number": 1,
      "head": {"ref": "feature-branch"}
    },
    "repository": {
      "full_name": "your-org/your-repo"
    }
  }'
```

---

## Service Status

```bash
# Check if running
docker ps | grep github-bot

# View logs
docker logs kostructure-github-bot

# Health check
curl http://localhost:8003/health
```

---

## Architecture

```
GitHub PR → Webhook → GitHub Bot (Port 8003)
                          ↓
                    API Gateway (Port 8000)
                          ↓
                    Parser + Cost Services
                          ↓
                    Cost Estimate
                          ↓
                    PR Comment Posted
```

---

## Supported Events

- `pull_request.opened` - New PR created
- `pull_request.synchronize` - New commits pushed

**Ignored events:**
- `pull_request.closed`
- `pull_request.labeled`
- Other PR actions

---

## Security

✅ **Webhook signature verification** - Validates requests from GitHub
✅ **Token-based auth** - GitHub token for API access
✅ **HTTPS recommended** - Use SSL in production
✅ **Secret management** - Tokens in environment variables

---

## Current Status

✅ **Service**: Running on port 8003
✅ **Health**: Healthy
✅ **Code**: Complete and tested
❌ **Configured**: Needs GITHUB_TOKEN and webhook setup

---

## Next Steps

1. **Get GitHub token** - Create personal access token or GitHub App
2. **Add to .env** - Set GITHUB_TOKEN and GITHUB_WEBHOOK_SECRET
3. **Expose webhook** - Use ngrok for local testing or deploy to cloud
4. **Configure webhook** - Add webhook URL in GitHub repo settings
5. **Test with PR** - Create PR with Terraform changes

---

## Troubleshooting

### Bot not responding to PRs
- Check GitHub webhook delivery status
- Verify GITHUB_TOKEN is valid
- Check bot logs: `docker logs kostructure-github-bot`

### "Invalid signature" error
- Verify GITHUB_WEBHOOK_SECRET matches GitHub settings
- Check webhook secret in GitHub repo settings

### "Failed to post comment" error
- Verify GITHUB_TOKEN has correct permissions
- Check token hasn't expired
- Verify repo access

### No Terraform files found
- Ensure PR contains .tf files
- Check file paths in PR
- Verify files aren't in .gitignore

---

## Production Deployment

### Deploy to Cloud

**AWS (ECS/Fargate)**
```bash
# Use Application Load Balancer
# Point GitHub webhook to: https://your-alb.com/webhook
```

**Heroku**
```bash
heroku create kostructure-bot
heroku config:set GITHUB_TOKEN=xxx
heroku config:set GITHUB_WEBHOOK_SECRET=xxx
git push heroku main
```

**Railway/Render**
- Connect GitHub repo
- Set environment variables
- Deploy automatically

### SSL Certificate
- Use Let's Encrypt for free SSL
- Or use cloud provider's SSL (ALB, CloudFront)

---

## Files

- `services/github-bot/main.py` - Bot implementation
- `services/github-bot/Dockerfile` - Container config
- `docker-compose.yml` - Service definition

---

**GitHub integration is ready! Just needs token and webhook configuration.**
