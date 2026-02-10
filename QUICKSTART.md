# 🚀 Enterprise Entobot Quick Start Guide

This guide will get you up and running with the Enterprise Entobot mobile app backend in 5 minutes.

## Prerequisites

- Python 3.11 or higher
- Node.js 18+ (optional, for Flutter app development)
- Flutter SDK (for mobile app)

## Step 1: Install Dependencies

### Option A: Using pip (recommended)
```bash
cd /home/chibionos/r/entobot
pip install -e .
```

### Option B: Using uv (faster)
```bash
cd /home/chibionos/r/entobot
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
uv pip install -e .
```

### Option C: Using system Python
```bash
python -m pip install --user -e .
```

## Step 2: Configure Settings

### Quick Setup
```bash
# Initialize configuration
nanobot onboard

# Edit config file
nano ~/.nanobot/config.json
```

### Minimal Configuration

Create or edit `~/.nanobot/config.json`:

```json
{
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5",
      "workspace": "~/.nanobot/workspace"
    }
  },
  "channels": {
    "mobile": {
      "enabled": true,
      "websocket_port": 18791,
      "tls_enabled": false
    }
  },
  "providers": {
    "openrouter": {
      "api_key": "YOUR_API_KEY_HERE"
    }
  },
  "auth": {
    "jwt_secret": "YOUR_STRONG_SECRET_MIN_32_CHARS_HERE"
  },
  "enterprise": {
    "organization_name": "My Organization",
    "rate_limit_enabled": true,
    "audit_log_enabled": true
  }
}
```

**Important Settings:**
- `providers.openrouter.api_key` or any other provider - **REQUIRED**
- `auth.jwt_secret` - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- `channels.mobile.tls_enabled` - Set to `false` for local development, `true` for production

### Get API Key

1. Visit [OpenRouter](https://openrouter.ai/keys) or your preferred provider
2. Create a new API key
3. Add to config file

## Step 3: Start the Server

### Using the Startup Script (Recommended)
```bash
python start_server.py
```

### Using Existing Gateway Command
```bash
nanobot gateway
```

You should see:
```
═══════════════════════════════════════════════════════════
  🤖 Enterprise Entobot Server
  Version: 1.0.0

  Starting secure mobile communication platform...
═══════════════════════════════════════════════════════════

✓ WebSocket server started on ws://localhost:18791
✓ REST API server starting on port 18790
✓ Mobile channel active
✓ Agent loop running
```

## Step 4: Generate QR Code

Open a new terminal:

```bash
# Display QR in terminal
nanobot pairing generate-qr

# Or save to file
nanobot pairing generate-qr --save --output ~/qr_code.png
```

The QR code contains:
- Session ID
- WebSocket URL
- Temporary pairing token
- Timestamp

**⏱️ QR codes expire in 5 minutes** - generate a new one if needed.

## Step 5: Run the Mobile App

### Flutter App Setup

```bash
cd mobile/entobot_flutter

# Install dependencies
flutter pub get

# Run on connected device or emulator
flutter run
```

### Using the App

1. **Pair Device:**
   - Open Entobot app
   - Tap "Pair New Device"
   - Scan QR code from terminal
   - Wait for "Pairing successful" message
   - JWT token saved automatically

2. **Start Chatting:**
   - Type your message in chat input
   - Send message
   - Wait for AI response
   - Continue conversation

3. **Manage Settings:**
   - Tap settings icon
   - View/edit bot configuration
   - Change model, temperature, etc.
   - Settings sync with server

## Step 6: Verify Everything Works

### Test WebSocket Connection
```bash
# Install wscat if needed
npm install -g wscat

# Connect to WebSocket server
wscat -c ws://localhost:18791

# Send ping (after authentication)
{"type":"ping"}

# Should receive
{"type":"pong"}
```

### Test REST API
```bash
# Health check
curl http://localhost:18790/api/health

# Get bot settings (should return JSON)
curl http://localhost:18790/api/v1/settings/bot

# Get providers
curl http://localhost:18790/api/v1/settings/providers
```

### Run Integration Tests
```bash
# Start server first in another terminal
python start_server.py

# In new terminal, run tests
python test_integration.py
```

## Architecture Overview

```
┌─────────────────┐
│  Mobile App     │
│  (Flutter)      │
└────────┬────────┘
         │
         │ WebSocket (ws://localhost:18791)
         │ REST API (http://localhost:18790)
         │
┌────────▼────────────────────────────────────┐
│  Enterprise Entobot Backend                 │
│                                              │
│  ┌──────────────────┐   ┌────────────────┐ │
│  │ Secure WebSocket │   │   REST API     │ │
│  │     Server       │   │   (FastAPI)    │ │
│  └────────┬─────────┘   └────────┬───────┘ │
│           │                      │          │
│  ┌────────▼──────────────────────▼───────┐ │
│  │        Message Bus                     │ │
│  └────────┬───────────────────────────────┘ │
│           │                                  │
│  ┌────────▼───────┐   ┌──────────────────┐ │
│  │  Agent Loop    │───│  LLM Provider    │ │
│  │  (AI Logic)    │   │  (Anthropic/etc) │ │
│  └────────────────┘   └──────────────────┘ │
└─────────────────────────────────────────────┘
```

## Common Tasks

### Change AI Model
```bash
# Edit config
nano ~/.nanobot/config.json

# Update model
"agents": {
  "defaults": {
    "model": "openai/gpt-4"  # or any supported model
  }
}

# Restart server
```

### Enable TLS/SSL
```bash
# Generate self-signed certificate (development only)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Update config
"channels": {
  "mobile": {
    "tls_enabled": true,
    "tls_cert_path": "/path/to/cert.pem",
    "tls_key_path": "/path/to/key.pem"
  }
}
```

### Enable Audit Logging
```bash
# Config
"enterprise": {
  "audit_log_enabled": true,
  "audit_log_path": "~/.nanobot/logs/audit.log"
}

# View logs
tail -f ~/.nanobot/logs/audit.log
```

### Multiple Mobile Devices
- Each device gets unique JWT token
- Support for 100 concurrent connections (configurable)
- All devices share same conversation history via session manager

## Next Steps

- ✅ Server running
- ✅ Mobile app connected
- ✅ Chatting with AI
- 🎯 Explore advanced features:
  - Settings management via API
  - Token refresh
  - Multi-device sync
  - Rate limiting
  - Enterprise features

## Getting Help

- **Troubleshooting:** See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **API Documentation:** Visit `http://localhost:18790/api/docs`
- **Integration Tests:** Run `python test_integration.py`
- **Logs:** Check `~/.nanobot/logs/`

## Security Notes

### Development vs Production

**Development (Local):**
- TLS disabled
- `ws://localhost`
- Self-signed certificates OK
- Debug logging enabled

**Production (Deployed):**
- ✅ Enable TLS (`tls_enabled: true`)
- ✅ Use proper SSL certificates
- ✅ Strong JWT secret (64+ chars)
- ✅ Enable rate limiting
- ✅ Enable audit logging
- ✅ Configure IP whitelist
- ✅ Disable debug logs
- ✅ Use environment variables for secrets

### JWT Secret Generation

```bash
# Generate strong secret
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Or use openssl
openssl rand -base64 64
```

### Environment Variables

Instead of config file, use environment variables:

```bash
export NANOBOT_AUTH__JWT_SECRET="your-secret-here"
export NANOBOT_PROVIDERS__OPENROUTER__API_KEY="your-key-here"
export NANOBOT_CHANNELS__MOBILE__WEBSOCKET_PORT=18791
```

## Performance Tuning

### Increase Connection Limit
```json
"channels": {
  "mobile": {
    "max_connections": 500  // default: 100
  }
}
```

### Adjust Rate Limiting
```json
"enterprise": {
  "rate_limit_requests_per_minute": 120  // default: 60
}
```

### Optimize Agent Performance
```json
"agents": {
  "defaults": {
    "max_tool_iterations": 10,  // reduce for faster responses
    "max_tokens": 4096  // reduce for lower costs
  }
}
```

## Demo Ready Checklist

- [ ] Dependencies installed
- [ ] Configuration file created
- [ ] API key configured
- [ ] JWT secret generated
- [ ] Server starts without errors
- [ ] QR code generates successfully
- [ ] Mobile app can scan QR
- [ ] Pairing completes
- [ ] Chat messages work
- [ ] AI responses received
- [ ] Settings API accessible
- [ ] Integration tests pass

---

**Ready to demo!** 🎉

Now you can:
1. Generate QR code: `nanobot pairing generate-qr`
2. Open mobile app and scan
3. Start chatting with your AI assistant
4. Show off the enterprise features!
