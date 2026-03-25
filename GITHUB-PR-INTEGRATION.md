# GitHub PR Integration - The Core Feature! 🎯

## What This Does

**Automatically posts cost estimates on GitHub Pull Requests** when Terraform files are changed.

When a developer opens a PR with Terraform changes:
1. 🤖 Bot detects the PR
2. 📄 Extracts Terraform files
3. 💰 Calculates costs
4. 💬 Posts comment with estimate

---

## Two Implementation Options

### Option 1: GitHub Action (Recommended for Public Repos)

**Pros:**
- ✅ No server needed
- ✅ Runs on GitHub's infrastructure
- ✅ Easy to set up
- ✅ Free for public repos

**Cons:**
- ❌ Requires public API endpoint
- ❌ Limited to GitHub Actions minutes

**Setup:**
1. Copy `.github/workflows/cost-estimate.yml` to your repo
2. Deploy Kostructure API publicly
3. Update API URL in workflow
4. Done!

---

### Option 2: Webhook Bot (Recommended for Private/Enterprise)

**Pros:**
- ✅ Works with private repos
- ✅ Self-hosted (no external dependencies)
- ✅ Full control
- ✅ Can access private APIs

**Cons:**
- ❌ Requires server
- ❌ Need to expose webhook endpoint

**Setup:**
1. Deploy GitHub bot service
2. Create GitHub webhook
3. Configure GitHub token
4. Done!

---

## Setup Guide

### GitHub Action Setup

#### Step 1: Deploy Kostructure API
```bash
# Deploy to your cloud provider
# Make sure it's publicly accessible
# Example: https://kostructure-api.yourcompany.com
```

#### Step 2: Add Workflow File
```bash
# Copy the workflow file
cp .github/workflows/cost-estimate.yml your-repo/.github/workflows/

# Update API URL in the file
# Line 42: Replace with your API URL
```

#### Step 3: Test
```bash
# Create a PR with Terraform changes
# Bot will automatically comment!
```

---

### Webhook Bot Setup

#### Step 1: Start GitHub Bot Service
```bash
# Add to .env
GITHUB_TOKEN=ghp_your_token_here
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Start services
docker-compose up -d github-bot
```

#### Step 2: Expose Webhook Endpoint
```bash
# Option A: Use ngrok for testing
ngrok http 8003

# Option B: Deploy to cloud with public IP
# Make sure port 8003 is accessible
```

#### Step 3: Create GitHub Webhook
1. Go to your repo → Settings → Webhooks
2. Click "Add webhook"
3. **Payload URL**: `https://your-domain.com/webhook`
4. **Content type**: `application/json`
5. **Secret**: Same as `GITHUB_WEBHOOK_SECRET`
6. **Events**: Select "Pull requests"
7. Click "Add webhook"

#### Step 4: Test
```bash
# Create a PR with Terraform changes
# Check webhook deliveries in GitHub settings
# Bot should post a comment!
```

---

## Example PR Comment

```markdown
## 💰 Kostructure Cost Estimate

### Monthly Cost: **$299.83**

📍 **Region**: us-east-1
📦 **Resources**: 5

### Resource Breakdown

| Resource | Type | Monthly Cost |
|----------|------|-------------|
| aws_instance.web | aws_instance | $30.37 |
| aws_db_instance.database | aws_db_instance | $64.06 |
| aws_s3_bucket.assets | aws_s3_bucket | $2.30 |
| aws_lb.app | aws_lb | $32.86 |
| aws_instance.worker | aws_instance | $170.24 |

---
*Estimated by [Kostructure](https://github.com/your-org/kostructure)*
```

---

## Configuration

### Environment Variables

```bash
# GitHub Bot Service
GITHUB_TOKEN=ghp_xxxxx              # GitHub personal access token
GITHUB_WEBHOOK_SECRET=secret123     # Webhook secret for verification
API_GATEWAY_URL=http://api-gateway:8000  # Internal API URL
PORT=8003                           # Bot service port
```

### GitHub Token Permissions

Create a GitHub Personal Access Token with:
- ✅ `repo` - Full control of private repositories
- ✅ `write:discussion` - Write access to discussions

Or use a GitHub App with:
- ✅ Pull requests: Read & write
- ✅ Contents: Read

---

## How It Works

### GitHub Action Flow
```
1. PR opened/updated with .tf files
   ↓
2. GitHub Action triggered
   ↓
3. Action extracts Terraform files
   ↓
4. Calls Kostructure API
   ↓
5. Formats response as comment
   ↓
6. Posts comment on PR
```

### Webhook Bot Flow
```
1. PR opened/updated
   ↓
2. GitHub sends webhook to bot
   ↓
3. Bot verifies signature
   ↓
4. Bot fetches .tf files via GitHub API
   ↓
5. Bot calls Kostructure API
   ↓
6. Bot posts comment via GitHub API
```

---

## Advanced Features

### Cost Comparison (Before/After)

To show cost delta, you need to:
1. Store previous estimate in PR metadata
2. Compare with new estimate
3. Show difference in comment

**Example:**
```markdown
### Cost Change: **+$50.00** (+20%)

**Before**: $250.00/month
**After**: $300.00/month
```

### Optimization Suggestions

Add optimization suggestions to PR comments:
```markdown
### 💡 Optimization Suggestions

1. **Switch to t3.medium** - Save $15/month
2. **Use Reserved Instances** - Save $100/month (1-year commitment)
```

### Cost Alerts

Fail the PR if cost exceeds threshold:
```yaml
- name: Check cost threshold
  run: |
    if [ "$TOTAL_COST" -gt "1000" ]; then
      echo "::error::Cost exceeds $1000 threshold!"
      exit 1
    fi
```

---

## Troubleshooting

### Bot Not Posting Comments

**Check:**
1. ✅ GitHub token has correct permissions
2. ✅ Webhook is configured correctly
3. ✅ Webhook secret matches
4. ✅ Bot service is running
5. ✅ API gateway is accessible

**Debug:**
```bash
# Check bot logs
docker logs kostructure-github-bot

# Check webhook deliveries in GitHub
# Repo → Settings → Webhooks → Recent Deliveries
```

### Action Failing

**Check:**
1. ✅ API URL is correct and accessible
2. ✅ Terraform files are valid
3. ✅ Action has `pull-requests: write` permission

**Debug:**
```bash
# Check Action logs in GitHub
# PR → Checks → Terraform Cost Estimate → View logs
```

---

## Security Considerations

### GitHub Token
- ✅ Use fine-grained tokens (not classic)
- ✅ Limit to specific repositories
- ✅ Rotate regularly
- ✅ Store in secrets (never commit)

### Webhook Secret
- ✅ Use strong random secret
- ✅ Verify signature on every request
- ✅ Store in environment variables

### API Access
- ✅ Use API keys for authentication
- ✅ Rate limit requests
- ✅ Validate input files

---

## Production Checklist

- [ ] Deploy Kostructure API with HTTPS
- [ ] Set up GitHub webhook with secret
- [ ] Configure GitHub token with minimal permissions
- [ ] Enable rate limiting
- [ ] Set up monitoring/alerts
- [ ] Test with sample PRs
- [ ] Document for team
- [ ] Add cost thresholds
- [ ] Enable optimization suggestions

---

## Example Workflow

### Developer Experience

1. **Developer creates PR**
   ```bash
   git checkout -b add-rds-database
   # Edit main.tf to add RDS instance
   git commit -am "Add RDS database"
   git push origin add-rds-database
   # Create PR on GitHub
   ```

2. **Bot comments within seconds**
   ```
   💰 Kostructure Cost Estimate
   Monthly Cost: $64.06
   
   New resource: aws_db_instance.database
   ```

3. **Team reviews cost impact**
   - "That's reasonable for production DB"
   - "Let's use db.t3.small instead to save $30/month"

4. **Developer updates PR**
   ```bash
   # Change instance class
   git commit -am "Use smaller instance"
   git push
   ```

5. **Bot updates comment**
   ```
   💰 Kostructure Cost Estimate
   Monthly Cost: $34.06 (-$30.00)
   
   ✅ Cost reduced!
   ```

6. **PR approved and merged**

---

## Why This Is The Core Feature

### Problem It Solves
- ❌ Developers don't know cost impact of changes
- ❌ Surprise bills at end of month
- ❌ No visibility into infrastructure costs
- ❌ Manual cost estimation is tedious

### Value It Provides
- ✅ **Visibility** - See costs before deploying
- ✅ **Prevention** - Catch expensive mistakes early
- ✅ **Education** - Learn AWS pricing
- ✅ **Collaboration** - Discuss costs in PR
- ✅ **Automation** - No manual work needed

### Competitive Advantage
- 🚀 **Infracost** does this, but we can do it better
- 🚀 **Integrated** with your existing workflow
- 🚀 **Real-time** feedback on every PR
- 🚀 **Actionable** optimization suggestions

---

## Next Steps

1. **Test the GitHub Action**
   - Create a test repo
   - Add workflow file
   - Open PR with Terraform changes
   - Verify comment appears

2. **Deploy Webhook Bot**
   - Start bot service
   - Expose webhook endpoint
   - Configure GitHub webhook
   - Test with real PR

3. **Enhance Comments**
   - Add cost comparison (before/after)
   - Add optimization suggestions
   - Add cost breakdown charts
   - Add links to detailed reports

4. **Scale It**
   - Support multiple repos
   - Add team notifications
   - Integrate with Slack
   - Build analytics dashboard

---

**This is the killer feature that makes Kostructure valuable!** 🎯

Without PR integration, it's just another cost calculator.
With PR integration, it's a **must-have tool** for every team using Terraform.
