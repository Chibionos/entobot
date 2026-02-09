# 🔧 Enterprise Entobot Troubleshooting Guide

Common issues and solutions for the Enterprise Entobot mobile backend.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Server Startup Issues](#server-startup-issues)
- [WebSocket Connection Issues](#websocket-connection-issues)
- [Pairing Issues](#pairing-issues)
- [Authentication Issues](#authentication-issues)
- [Message Delivery Issues](#message-delivery-issues)
- [API Issues](#api-issues)
- [Mobile App Issues](#mobile-app-issues)
- [Performance Issues](#performance-issues)
- [Security Issues](#security-issues)

---

## Installation Issues

### Problem: `ModuleNotFoundError: No module named 'websockets'`

**Cause:** Dependencies not installed.

**Solution:**
```bash
cd /home/chibionos/r/entobot
pip install -e .

# Or with uv
uv venv
source .venv/bin/activate
uv pip install -e .
```

### Problem: `pip: command not found`

**Cause:** pip not installed in system.

**Solution:**
```bash
# On Arch Linux
sudo pacman -S python-pip

# Or use system Python
python -m ensurepip --upgrade

# Or use uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Problem: `externally managed environment`

**Cause:** System Python protection (PEP 668).

**Solutions:**
```bash
# Option 1: Use virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Option 2: Use --user flag
pip install --user -e .

# Option 3: Use uv
uv venv && source .venv/bin/activate
uv pip install -e .
```

---

## Server Startup Issues

### Problem: `Address already in use` (port 18791 or 18790)

**Cause:** Another process using the port.

**Solution:**
```bash
# Find process using port
lsof -i :18791
# or
netstat -tulpn | grep 18791

# Kill the process
kill -9 <PID>

# Or use different port
python start_server.py --ws-port 18792 --api-port 18793
```

### Problem: `No API key configured`

**Cause:** Missing API key in config.

**Solution:**
```bash
# Edit config
nano ~/.nanobot/config.json

# Add API key
{
  "providers": {
    "openrouter": {
      "api_key": "sk-or-v1-..."
    }
  }
}
```

### Problem: `JWT secret not set`

**Cause:** Missing JWT secret.

**Solution:**
```bash
# Generate strong secret
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Add to config
{
  "auth": {
    "jwt_secret": "generated-secret-here"
  }
}
```

### Problem: `Failed to load configuration`

**Cause:** Config file doesn't exist or has errors.

**Solution:**
```bash
# Initialize config
nanobot onboard

# Or copy example
cp config.example.json ~/.nanobot/config.json

# Validate JSON syntax
python -m json.tool ~/.nanobot/config.json
```

---

## WebSocket Connection Issues

### Problem: `Connection refused` (ws://localhost:18791)

**Cause:** Server not running or wrong port.

**Solution:**
```bash
# Check if server running
ps aux | grep start_server

# Check port
netstat -tulpn | grep 18791

# Verify config
grep websocket_port ~/.nanobot/config.json

# Start server
python start_server.py --verbose
```

### Problem: `Connection timeout`

**Cause:** Firewall or network issue.

**Solution:**
```bash
# Check firewall
sudo ufw status
sudo ufw allow 18791/tcp

# Test locally
wscat -c ws://localhost:18791

# Check server logs
tail -f ~/.nanobot/logs/*.log
```

### Problem: `SSL/TLS handshake failed`

**Cause:** TLS misconfiguration.

**Solutions:**
```bash
# For development, disable TLS
{
  "channels": {
    "mobile": {
      "tls_enabled": false
    }
  }
}

# For production, check certificates
openssl s_client -connect localhost:18791

# Verify cert paths exist
ls -la /path/to/cert.pem
ls -la /path/to/key.pem
```

---

## Pairing Issues

### Problem: `QR code won't scan`

**Cause:** QR code expired or invalid format.

**Solutions:**
```bash
# Generate new QR (expires in 5 minutes)
nanobot pairing generate-qr

# Save to file for better quality
nanobot pairing generate-qr --save --output qr.png

# Increase brightness on screen
# Ensure good lighting
# Try different QR scanner app
```

### Problem: `Invalid pairing credentials`

**Cause:** Session expired or wrong token.

**Solution:**
```bash
# Generate fresh QR code
nanobot pairing generate-qr

# Check session expiry time
grep pairing_session_expiry_minutes ~/.nanobot/config.json

# Increase expiry if needed
{
  "auth": {
    "pairing_session_expiry_minutes": 10
  }
}
```

### Problem: `Session not found`

**Cause:** Server restarted or session cleaned up.

**Solution:**
```bash
# Generate new pairing session
nanobot pairing generate-qr

# Scan immediately (don't wait)

# Check server logs
tail -f ~/.nanobot/logs/*.log
```

---

## Authentication Issues

### Problem: `Invalid or expired JWT token`

**Cause:** Token expired or JWT secret changed.

**Solutions:**
```bash
# Re-pair device (generates new token)
nanobot pairing generate-qr

# Check token expiry
{
  "auth": {
    "jwt_expiry_hours": 720  // 30 days
  }
}

# Verify JWT secret hasn't changed
grep jwt_secret ~/.nanobot/config.json
```

### Problem: `Not authenticated` when sending messages

**Cause:** WebSocket not authenticated.

**Solution:**
```javascript
// Mobile app must authenticate first
{
  "type": "auth",
  "jwt_token": "saved-token-here"
}

// Then send messages
{
  "type": "message",
  "content": "Hello"
}
```

### Problem: `Failed to extract credentials from token`

**Cause:** Corrupted or invalid JWT.

**Solution:**
```bash
# Clear app storage and re-pair
# On mobile: Settings -> Storage -> Clear Data

# Generate new QR
nanobot pairing generate-qr

# Scan and pair again
```

---

## Message Delivery Issues

### Problem: Messages sent but no response

**Cause:** Agent loop not running or LLM error.

**Solutions:**
```bash
# Check server logs
tail -f ~/.nanobot/logs/*.log

# Verify agent loop running
ps aux | grep python | grep start_server

# Test agent directly
nanobot agent -m "test message"

# Check API key valid
curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"anthropic/claude-opus-4-5","messages":[{"role":"user","content":"hi"}]}'
```

### Problem: `Message received` but stuck in queue

**Cause:** Message bus issue.

**Solution:**
```bash
# Check bus stats
# In server logs, look for "In: X, Out: Y"

# Restart server
pkill -f start_server
python start_server.py

# Check for exceptions
grep -i error ~/.nanobot/logs/*.log
```

### Problem: Messages arrive out of order

**Cause:** Network latency or race condition.

**Solution:**
```bash
# Add sequence numbers in mobile app
# Use server-side message queue
# Check network stability

# Reduce concurrent connections
{
  "channels": {
    "mobile": {
      "max_connections": 50
    }
  }
}
```

---

## API Issues

### Problem: `404 Not Found` on API endpoints

**Cause:** Wrong URL or API server not running.

**Solution:**
```bash
# Check API server running
curl http://localhost:18790/api/health

# Verify port
grep "port" ~/.nanobot/config.json

# Check available endpoints
curl http://localhost:18790/api/docs

# Use correct paths
# ✓ /api/v1/settings/bot
# ✗ /settings/bot (missing /api/v1)
```

### Problem: `500 Internal Server Error`

**Cause:** Server-side exception.

**Solution:**
```bash
# Check server logs
tail -f ~/.nanobot/logs/*.log

# Enable verbose mode
python start_server.py --verbose

# Test API directly
curl -v http://localhost:18790/api/v1/settings/bot

# Check for Python exceptions
grep -i traceback ~/.nanobot/logs/*.log
```

### Problem: CORS errors in browser

**Cause:** CORS policy blocking requests.

**Solution:**
```json
// Update config
{
  "network": {
    "allowed_origins": ["http://localhost:3000", "http://192.168.1.100"]
  }
}

// Or allow all (development only!)
{
  "network": {
    "allowed_origins": ["*"]
  }
}
```

---

## Mobile App Issues

### Problem: App crashes on startup

**Cause:** Dependencies or configuration issue.

**Solution:**
```bash
cd mobile/entobot_flutter

# Clear cache
flutter clean

# Get dependencies
flutter pub get

# Rebuild
flutter run --debug

# Check logs
flutter logs
```

### Problem: `Unable to connect to server`

**Cause:** Wrong WebSocket URL or server not accessible.

**Solutions:**
```dart
// Check WebSocket URL in app
// Development: ws://localhost:18791
// Network: ws://192.168.1.100:18791
// Production: wss://your-domain.com:18791

// Verify server reachable
// From mobile device:
ping 192.168.1.100
telnet 192.168.1.100 18791
```

### Problem: QR scanner not working

**Cause:** Camera permissions or QR parsing issue.

**Solution:**
```bash
# Grant camera permission on device
# Settings -> Apps -> Entobot -> Permissions -> Camera

# Test QR code with other scanner app

# Verify QR contains valid JSON
# Should have: session_id, websocket_url, temp_token
```

### Problem: Messages don't appear in chat

**Cause:** UI state not updating or WebSocket disconnected.

**Solution:**
```dart
// Check WebSocket connection state
print(websocket.readyState);

// Verify message listener registered
websocket.onMessage.listen((msg) {
  print('Received: $msg');
});

// Force UI rebuild
setState(() {});

// Check Flutter console for errors
flutter logs | grep -i error
```

---

## Performance Issues

### Problem: Slow response times

**Cause:** LLM latency, network, or overloaded server.

**Solutions:**
```bash
# Use faster model
{
  "agents": {
    "defaults": {
      "model": "openai/gpt-4o-mini"  // faster than opus
    }
  }
}

# Reduce token limit
{
  "agents": {
    "defaults": {
      "max_tokens": 2048  // faster generation
    }
  }
}

# Check network latency
ping openrouter.ai
curl -w "@-" -o /dev/null -s https://openrouter.ai/api/v1/models <<'EOF'
    time_namelookup:  %{time_namelookup}\n
       time_connect:  %{time_connect}\n
    time_appconnect:  %{time_appconnect}\n
      time_redirect:  %{time_redirect}\n
   time_pretransfer:  %{time_pretransfer}\n
 time_starttransfer:  %{time_starttransfer}\n
                    ----------\n
         time_total:  %{time_total}\n
EOF
```

### Problem: High memory usage

**Cause:** Message queue buildup or memory leak.

**Solution:**
```bash
# Monitor memory
top -p $(pgrep -f start_server)

# Restart server periodically
# Set up systemd service with restart policy

# Reduce max connections
{
  "channels": {
    "mobile": {
      "max_connections": 50  // default: 100
    }
  }
}

# Clear old sessions
# Implement session cleanup in code
```

### Problem: Too many concurrent connections

**Cause:** Rate limiting not working or DDoS.

**Solution:**
```bash
# Enable rate limiting
{
  "enterprise": {
    "rate_limit_enabled": true,
    "rate_limit_requests_per_minute": 30
  }
}

# Check connected devices
# In server logs: "X devices connected"

# Implement IP whitelist
{
  "enterprise": {
    "ip_whitelist_enabled": true,
    "ip_whitelist": ["192.168.1.0/24"]
  }
}
```

---

## Security Issues

### Problem: Unauthorized access attempts

**Cause:** No authentication or weak JWT secret.

**Solutions:**
```bash
# Use strong JWT secret (64+ chars)
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Enable audit logging
{
  "enterprise": {
    "audit_log_enabled": true,
    "audit_log_path": "~/.nanobot/logs/audit.log"
  }
}

# Monitor audit logs
tail -f ~/.nanobot/logs/audit.log | grep -i "failed\|unauthorized"

# Implement IP whitelist
{
  "enterprise": {
    "ip_whitelist_enabled": true,
    "ip_whitelist": ["10.0.0.0/8"]
  }
}
```

### Problem: JWT tokens leaked

**Cause:** Insecure storage or transmission.

**Solutions:**
```bash
# Immediately rotate JWT secret
# Generate new secret
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Update config and restart server

# Force re-pairing of all devices
# Old tokens become invalid

# Enable TLS
{
  "channels": {
    "mobile": {
      "tls_enabled": true,
      "tls_cert_path": "/path/to/cert.pem",
      "tls_key_path": "/path/to/key.pem"
    }
  }
}
```

### Problem: Man-in-the-middle attacks

**Cause:** No TLS encryption.

**Solution:**
```bash
# Enable TLS for production
{
  "channels": {
    "mobile": {
      "tls_enabled": true
    }
  }
}

# Use proper SSL certificates (not self-signed)
# From Let's Encrypt or trusted CA

# Verify certificate in mobile app
# Implement certificate pinning
```

---

## Diagnostic Commands

### Check System Status
```bash
# Server running?
ps aux | grep start_server

# Ports listening?
netstat -tulpn | grep -E "18790|18791"

# Disk space?
df -h ~/.nanobot

# Memory usage?
free -h
```

### View Logs
```bash
# All logs
tail -f ~/.nanobot/logs/*.log

# Only errors
grep -i error ~/.nanobot/logs/*.log

# Only warnings
grep -i warning ~/.nanobot/logs/*.log

# Audit log
tail -f ~/.nanobot/logs/audit.log
```

### Test Components
```bash
# Test WebSocket
wscat -c ws://localhost:18791

# Test API
curl http://localhost:18790/api/health

# Test agent
nanobot agent -m "test"

# Test QR generation
nanobot pairing generate-qr

# Run integration tests
python test_integration.py
```

### Debug Mode
```bash
# Start with verbose logging
python start_server.py --verbose

# Enable Python debugging
PYTHONDEVMODE=1 python start_server.py

# Trace WebSocket messages
# Add logging in websocket.py
```

---

## Getting More Help

### Log Issues
```bash
# Collect diagnostic info
cat ~/.nanobot/config.json | jq .
python --version
uname -a
free -h
df -h
ps aux | grep start_server
netstat -tulpn | grep -E "18790|18791"
tail -100 ~/.nanobot/logs/*.log
```

### Report Bugs
When reporting issues, include:
1. Error message (full traceback)
2. Server logs (last 100 lines)
3. Configuration (sanitized - remove API keys!)
4. Steps to reproduce
5. System info (OS, Python version)
6. Network setup (local, remote, VPN?)

### Community Resources
- GitHub Issues: Report bugs and feature requests
- Documentation: Check latest docs
- Integration Tests: Run `python test_integration.py`
- API Docs: Visit `http://localhost:18790/api/docs`

---

## Quick Fixes

**90% of issues are:**
1. ❌ Dependencies not installed → `pip install -e .`
2. ❌ Server not running → `python start_server.py`
3. ❌ Wrong port → Check config
4. ❌ API key missing → Add to config
5. ❌ QR expired → Generate new one
6. ❌ JWT secret weak → Generate strong one
7. ❌ TLS misconfigured → Disable for dev
8. ❌ Firewall blocking → Allow ports
9. ❌ Config syntax error → Validate JSON
10. ❌ Wrong WebSocket URL → Use `ws://` not `wss://` for local

**Always check logs first!**
```bash
tail -f ~/.nanobot/logs/*.log
```
