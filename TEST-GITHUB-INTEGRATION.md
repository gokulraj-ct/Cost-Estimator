# Testing GitHub PR Integration

## Quick Test Setup

### Option 1: Test with ngrok (Fastest)

1. **Start ngrok**
```bash
ngrok http 8003
```

2. **Copy the URL** (e.g., `https://abc123.ngrok.io`)

3. **Create GitHub webhook**
- Go to your test repo → Settings → Webhooks → Add webhook
- Payload URL: `https://abc123.ngrok.io/webhook`
- Content type: `application/json`
- Secret: `test-secret-123`
- Events: Pull requests
- Save

4. **Set environment variables**
```bash
export GITHUB_TOKEN=ghp_your_token_here
export GITHUB_WEBHOOK_SECRET=test-secret-123
docker-compose restart github-bot
```

5. **Create test PR**
```bash
# In your test repo
echo 'resource "aws_instance" "test" { instance_type = "t3.micro" }' > test.tf
git add test.tf
git commit -m "Add test instance"
git push origin -u test-branch
# Create PR on GitHub
```

6. **Check the PR** - Bot should comment within seconds!

---

### Option 2: Test GitHub Action (No Server Needed)

1. **Copy workflow to your repo**
```bash
mkdir -p .github/workflows
cp /home/gokul/kostructure/.github/workflows/cost-estimate.yml .github/workflows/
```

2. **Update API URL in workflow** (line 42)
```yaml
# Change this:
RESPONSE=$(curl -s -X POST https://your-kostructure-api.com/api/v1/estimate \

# To your deployed API or use ngrok:
RESPONSE=$(curl -s -X POST https://abc123.ngrok.io/api/v1/estimate \
```

3. **Push and create PR**
```bash
git add .github/workflows/cost-estimate.yml
git commit -m "Add cost estimation"
git push
# Create PR with .tf file changes
```

---

## What You Need

### GitHub Token
```bash
# Create at: https://github.com/settings/tokens
# Permissions needed:
# - repo (full control)
# - write:discussion

# Then set it:
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
```

### Test Repository
- Any GitHub repo you have admin access to
- Or create a new test repo

---

## Quick Test Commands

```bash
# 1. Check bot is running
curl http://localhost:8003/health

# 2. Test webhook endpoint locally
curl -X POST http://localhost:8003/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -d '{
    "action": "opened",
    "pull_request": {
      "number": 1,
      "head": {"ref": "test"}
    },
    "repository": {
      "full_name": "your-username/test-repo"
    }
  }'

# 3. Check bot logs
docker logs kostructure-github-bot -f
```

---

## Expected Result

Bot posts this comment on your PR:

```markdown
## 💰 Kostructure Cost Estimate

### Monthly Cost: **$7.59**

📍 **Region**: us-east-1
📦 **Resources**: 1

### Resource Breakdown

| Resource | Type | Monthly Cost |
|----------|------|-------------|
| aws_instance.test | aws_instance | $7.59 |

---
*Estimated by Kostructure*
```
