# Entobot Enterprise - Deployment Guide

## Deployment Architecture

The Entobot Enterprise platform consists of 3 components with different deployment requirements:

### 1. Dashboard (✅ Vercel-Compatible)
- **What**: Web-based monitoring dashboard
- **Tech**: FastAPI + HTML/CSS/JS
- **Deployment**: Vercel (serverless functions)
- **URL**: Will be at `https://entobot-enterprise-darthwares.vercel.app`

### 2. REST API (✅ Vercel-Compatible)
- **What**: Settings management API
- **Tech**: FastAPI endpoints
- **Deployment**: Vercel (serverless functions)
- **Endpoints**: `/api/v1/*`

### 3. WebSocket Server + Backend (⚠️ Needs Different Host)
- **What**: Real-time messaging, agent loop, WebSocket connections
- **Tech**: Python asyncio WebSocket server
- **Deployment**: **NOT compatible with Vercel** (requires persistent connections)
- **Alternative Hosts**:
  - Railway (recommended - has WebSocket support)
  - Render
  - Fly.io
  - DigitalOcean App Platform
  - AWS EC2/ECS
  - Your own VPS

---

## Quick Deployment

### Option A: Deploy Dashboard to Vercel (Demo Mode)

This deploys the dashboard with demo/mock data for presentation purposes:

```bash
# Deploy to Vercel
cd /home/chibionos/r/entobot
vercel --prod

# Follow prompts:
# - Link to Darthwares project
# - Deploy
```

**Result**: Dashboard accessible at Vercel URL with demo mode enabled.

### Option B: Full Production Deployment

#### Step 1: Deploy Backend to Railway (Recommended)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables
railway variables set JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
railway variables set OPENAI_API_KEY=your_key_here
```

#### Step 2: Deploy Dashboard to Vercel

```bash
# Update vercel.json with backend URL
# Then deploy
vercel --prod
```

#### Step 3: Configure Mobile App

Update `mobile/entobot_flutter/lib/core/utils/constants.dart`:

```dart
// Production URLs
static const String websocketUrl = 'wss://your-railway-app.railway.app';
static const String apiBaseUrl = 'https://your-railway-app.railway.app/api/v1';
```

---

## Current Deployment Status

### ✅ What's Ready
- Dashboard code (demo mode works standalone)
- REST API code (can be deployed as serverless)
- Mobile app code (needs backend URL configuration)
- All documentation

### ⚠️ What's Needed for Production
1. **Backend hosting** - Deploy to Railway/Render/etc
2. **TLS certificates** - Configure SSL for production
3. **Environment variables** - Set JWT secret, API keys
4. **Domain names** - Configure custom domains
5. **Mobile app build** - Build APK/IPA with production URLs

---

## Vercel Deployment (Dashboard Only)

### What Will Be Deployed

```
https://entobot-enterprise-darthwares.vercel.app/
├── /              → Dashboard (with demo mode)
├── /api/dashboard → Dashboard API (mock data)
└── /ws/dashboard  → ⚠️ WebSocket won't work (Vercel limitation)
```

### Limitations

- **No WebSocket support**: Real-time updates won't work (Vercel doesn't support persistent connections)
- **Demo mode only**: Will show simulated data
- **No mobile app pairing**: Requires full backend on different host

### Benefits

- **Fast deployment**: < 1 minute
- **Good for demos**: Professional-looking dashboard
- **Free tier**: No cost
- **Global CDN**: Fast everywhere
- **Easy to share**: Just send the URL

---

## Recommended Production Architecture

```
┌─────────────────────────────────────────────────┐
│  Mobile App (iOS/Android)                       │
│  - QR scanning                                  │
│  - Real-time chat                               │
│  - Settings management                          │
└────────────┬────────────────────────────────────┘
             │
             │ HTTPS/WSS
             ↓
┌─────────────────────────────────────────────────┐
│  Backend (Railway/Render/VPS)                   │
│  ├── WebSocket Server (port 18791)             │
│  ├── REST API (port 18790)                     │
│  ├── Agent Loop                                 │
│  └── Message Bus                                │
└────────────┬────────────────────────────────────┘
             │
             │ Monitoring API
             ↓
┌─────────────────────────────────────────────────┐
│  Dashboard (Vercel)                             │
│  - Real-time monitoring                         │
│  - Audit logs                                   │
│  - Device management                            │
└─────────────────────────────────────────────────┘
```

---

## Deployment Commands

### Deploy Dashboard to Vercel Now

```bash
cd /home/chibionos/r/entobot

# Option 1: Deploy to Darthwares project
vercel --prod

# Option 2: Deploy with specific project
vercel --prod --project=darthwares
```

### Deploy Backend to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Create new project
railway init

# Deploy
railway up

# View logs
railway logs

# Get URL
railway status
```

### Deploy to Render

```bash
# Connect GitHub repo to Render
# Go to https://render.com
# New → Web Service → Connect GitHub repo
# Select branch: enterprise-mobile-backend
# Build command: pip install -r requirements.txt
# Start command: python start_server.py
```

---

## Environment Variables Needed

### For Backend (Railway/Render/VPS)

```env
# Required
JWT_SECRET=<64-character-random-string>
OPENAI_API_KEY=<your-openai-key>

# Optional
WEBSOCKET_PORT=18791
API_PORT=18790
DASHBOARD_PORT=8080
TLS_ENABLED=true
TLS_CERT_PATH=/path/to/cert.pem
TLS_KEY_PATH=/path/to/key.pem
```

### For Dashboard (Vercel)

```env
# Optional (for connecting to backend)
BACKEND_URL=https://your-railway-app.railway.app
ENABLE_DEMO_MODE=true
```

---

## Testing Deployment

### Test Dashboard (Vercel)

```bash
# After deployment
curl https://entobot-enterprise-darthwares.vercel.app/
curl https://entobot-enterprise-darthwares.vercel.app/api/dashboard/status
```

### Test Backend (Railway)

```bash
# Replace with your Railway URL
curl https://your-app.railway.app/api/health
wscat -c wss://your-app.railway.app:18791
```

### Test Mobile App

1. Update constants.dart with production URLs
2. Build app: `flutter build apk --release`
3. Install on device
4. Scan QR code
5. Test chat

---

## Rollback Procedures

### Vercel

```bash
# List deployments
vercel ls

# Rollback to previous
vercel rollback <deployment-url>
```

### Railway

```bash
# Redeploy previous version
railway up --service=<service-id>
```

---

## Next Steps

### For Tonight's Demo
1. Deploy dashboard to Vercel: `vercel --prod`
2. Enable demo mode (already configured)
3. Share Vercel URL
4. Show professional dashboard

### For Production Launch
1. Choose backend hosting (Railway recommended)
2. Deploy backend with TLS
3. Generate production JWT secret
4. Configure domain names
5. Build mobile app with production URLs
6. Test end-to-end
7. Monitor with dashboard

---

## Support

- Dashboard issues: Check Vercel logs
- Backend issues: Check Railway/Render logs
- Mobile app issues: Check device logs (adb logcat / Xcode)
- Integration issues: See TROUBLESHOOTING.md

---

## Cost Estimates

### Free Tier (Demo)
- Vercel: Free (dashboard only)
- Total: $0/month

### Basic Production
- Railway: $5/month (Hobby plan)
- Vercel: Free (dashboard)
- Total: $5/month

### Enterprise Production
- Railway: $20/month (Pro plan)
- Vercel: $20/month (Pro for custom domain)
- Total: $40/month

---

**Note**: WebSocket server requires a platform with persistent connection support. Vercel is perfect for the dashboard but cannot host the full backend. Use Railway, Render, or similar for the backend.
