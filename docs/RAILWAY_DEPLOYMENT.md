# Railway Deployment Guide

## Why Railway for Entobot Enterprise?

Railway is the **recommended platform** for deploying Entobot Enterprise because it supports:

- ✅ **Long-running processes** (WebSocket server, agent loop)
- ✅ **Persistent connections** (WebSocket on port 18791)
- ✅ **Full Python applications** (not just serverless functions)
- ✅ **Environment variables** (API keys, secrets)
- ✅ **Custom ports** (18790 for API, 18791 for WebSocket)
- ✅ **Automatic HTTPS** (with custom domains)
- ✅ **Built-in PostgreSQL** (optional, for scaling)
- ✅ **Zero-downtime deployments**

**Vercel is NOT suitable** for Entobot Enterprise because it's designed for serverless functions, not persistent services.

---

## Prerequisites

- Railway account (free tier available)
- GitHub repository (already set up: https://github.com/Chibionos/entobot)
- API keys for LLM providers (OpenRouter, OpenAI, etc.)

---

## Deployment Steps

### 1. Install Railway CLI

```bash
npm install -g @railway/cli
```

Verify installation:
```bash
railway --version
```

### 2. Login to Railway

```bash
railway login
```

This will open your browser for authentication.

### 3. Initialize Railway Project

Navigate to your project:
```bash
cd /home/chibionos/r/entobot
```

Create a new Railway project:
```bash
railway init
```

Follow the prompts:
- **Project name**: entobot-enterprise
- **Environment**: production

### 4. Configure Environment Variables

Set required environment variables:

```bash
# LLM Provider API Keys
railway variables set OPENROUTER_API_KEY="your-key-here"
railway variables set OPENAI_API_KEY="your-key-here"

# Optional: Other providers
railway variables set ANTHROPIC_API_KEY="your-key-here"
railway variables set DEEPSEEK_API_KEY="your-key-here"

# JWT Secret (generate a strong secret)
railway variables set JWT_SECRET="$(openssl rand -hex 32)"

# Application Config
railway variables set NANOBOT_CONFIG_PATH="/app/config.json"
railway variables set HOST="0.0.0.0"
railway variables set PORT="8080"
```

### 5. Create Railway Configuration

Create a `railway.json` file:

```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -e ."
  },
  "deploy": {
    "startCommand": "python start_server.py",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 6. Deploy to Railway

```bash
railway up
```

This will:
1. Build your application
2. Install dependencies from `pyproject.toml`
3. Start the server with `python start_server.py`
4. Assign a public URL

### 7. Get Your Railway URL

```bash
railway status
```

Or check the Railway dashboard: https://railway.app/dashboard

Your deployment URL will be something like:
```
https://entobot-enterprise-production.up.railway.app
```

### 8. Update Mobile App Configuration

Update the mobile app to point to your Railway deployment:

```bash
cd mobile/entobot_flutter
```

Edit `lib/core/utils/constants.dart`:

```dart
class ApiConstants {
  // Replace with your Railway URL
  static const String websocketUrl = 'wss://entobot-enterprise-production.up.railway.app';
  static const String apiBaseUrl = 'https://entobot-enterprise-production.up.railway.app/api/v1';

  // Pairing
  static const Duration pairingTimeout = Duration(minutes: 5);
}
```

### 9. Rebuild Mobile App

```bash
flutter pub get
flutter build apk --release  # For Android
flutter build ios --release  # For iOS (requires macOS)
```

---

## Verification Steps

### 1. Check Server Health

```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 123
}
```

### 2. Check WebSocket Connection

```bash
wscat -c wss://your-app.railway.app
```

Expected: Connection established

### 3. Generate QR Code

Using the Railway deployment:
```bash
railway run nanobot pairing generate-qr
```

Or via CLI pointing to Railway:
```bash
export NANOBOT_API_URL=https://your-app.railway.app/api/v1
nanobot pairing generate-qr
```

### 4. Test Mobile App

1. Install mobile app on device
2. Scan QR code
3. Send test message
4. Verify AI response

---

## Monitoring and Logs

### View Live Logs

```bash
railway logs
```

Or use the Railway dashboard for a better experience.

### Monitor Metrics

Railway dashboard provides:
- CPU usage
- Memory usage
- Network traffic
- Request count
- Error rates

---

## Scaling

### Vertical Scaling (Increase Resources)

Railway dashboard → Settings → Resources
- Adjust CPU cores
- Adjust memory limit

### Horizontal Scaling (Multiple Instances)

Railway supports multiple replicas:
```bash
railway scale replicas 3
```

**Note**: For horizontal scaling, you'll need:
- Shared session storage (PostgreSQL or Redis)
- Load balancer configuration

---

## Custom Domain

### 1. Add Domain in Railway

Railway dashboard → Settings → Domains → Add Domain
- Enter your domain (e.g., `entobot.yourcompany.com`)

### 2. Update DNS Records

Add CNAME record:
```
entobot.yourcompany.com → your-railway-app.railway.app
```

### 3. Update Mobile App

Update `constants.dart` with your custom domain:
```dart
static const String websocketUrl = 'wss://entobot.yourcompany.com';
static const String apiBaseUrl = 'https://entobot.yourcompany.com/api/v1';
```

---

## Database (Optional)

For production deployments with > 100 users, add PostgreSQL:

### 1. Add PostgreSQL Plugin

```bash
railway add postgresql
```

### 2. Update Configuration

Railway automatically sets `DATABASE_URL` environment variable.

Update `config.json`:
```json
{
  "database": {
    "type": "postgresql",
    "url": "${DATABASE_URL}"
  }
}
```

### 3. Initialize Database

```bash
railway run python -c "from nanobot.database import init_db; init_db()"
```

---

## CI/CD (Continuous Deployment)

Railway automatically deploys on `git push` to main branch.

To enable:

### 1. Link GitHub Repository

Railway dashboard → Settings → GitHub
- Connect repository
- Select branch (e.g., `main` or `enterprise-mobile-backend`)

### 2. Push to Deploy

```bash
git push origin main
```

Railway will automatically:
1. Detect changes
2. Build new version
3. Run tests (if configured)
4. Deploy with zero downtime

---

## Troubleshooting

### Error: "Build failed"

Check build logs:
```bash
railway logs --build
```

Common issues:
- Missing dependencies in `pyproject.toml`
- Python version mismatch
- Build timeout (increase in settings)

### Error: "Application crashed"

Check runtime logs:
```bash
railway logs
```

Common issues:
- Missing environment variables
- Port binding issues (ensure `HOST=0.0.0.0`)
- Missing config file

### Error: "WebSocket connection failed"

1. Verify WebSocket endpoint:
   ```bash
   wscat -c wss://your-app.railway.app
   ```

2. Check firewall settings
3. Verify Railway exposes WebSocket port

### Error: "Cannot generate QR code"

Ensure pairing manager is initialized:
```bash
railway run nanobot pairing generate-qr --debug
```

---

## Cost Estimation

### Free Tier (Hobby Plan)
- ✅ $5/month credit
- ✅ 500 hours execution time
- ✅ 512 MB memory
- ✅ Shared CPU
- ⚠️ Suitable for testing and small teams (< 10 users)

### Pro Plan ($20/month)
- ✅ Unlimited execution time
- ✅ 8 GB memory
- ✅ 8 vCPU
- ✅ Suitable for medium deployments (10-100 users)

### Enterprise
- Custom pricing
- Dedicated resources
- SLA guarantees
- Contact Railway for pricing

**Estimated costs for Entobot Enterprise:**
- Small team (10 users): **$5-10/month**
- Medium team (50 users): **$20-40/month**
- Large team (200+ users): **$100-200/month**

---

## Production Checklist

Before going live:

- [ ] Set strong JWT secret
- [ ] Configure all API keys
- [ ] Enable HTTPS (automatic on Railway)
- [ ] Set up custom domain
- [ ] Configure monitoring alerts
- [ ] Test QR code pairing
- [ ] Test mobile app end-to-end
- [ ] Review security settings
- [ ] Set up backup strategy
- [ ] Document rollback procedure

---

## Alternative: Docker Deployment

If you prefer Docker:

### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --no-dev

COPY . .

EXPOSE 18790 18791

CMD ["python", "start_server.py"]
```

### 2. Deploy to Railway

```bash
railway up --dockerfile
```

---

## Support

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Entobot Docs**: See `docs/` folder

---

## Next Steps

1. **Deploy to Railway**: `railway up`
2. **Generate QR code**: `railway run nanobot pairing generate-qr`
3. **Update mobile app**: Edit `constants.dart` with Railway URL
4. **Test end-to-end**: Scan QR, send message, verify response
5. **Roll out to company**: Follow `docs/ROLLOUT_SUMMARY.md`

---

**Railway is the recommended platform** for Entobot Enterprise because it provides the right infrastructure for long-running WebSocket services and AI agent loops.

For questions or issues, see `docs/TROUBLESHOOTING.md` or open a GitHub issue.
