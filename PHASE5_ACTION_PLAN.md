# Phase 5: Action Plan & Implementation Guide

**Date:** February 9, 2026
**Purpose:** Step-by-step guide to fix critical issues and reach production readiness

---

## Sprint 1: Critical Security Fixes (Week 1) 🚨

**Goal:** Fix all P0 issues to unblock production deployment
**Duration:** 18 hours (~3 days)
**Priority:** CRITICAL

### Task 1.1: Enable TLS by Default (4 hours)

**Issue:** P0-002 - TLS disabled by default

**Implementation:**

```python
# File: nanobot/config/schema.py
class MobileAppConfig(BaseModel):
    """Mobile app configuration for secure enterprise communication."""
    enabled: bool = True
    websocket_port: int = 18791
    tls_enabled: bool = True  # CHANGE: Was False
    tls_cert_path: str | None = None
    tls_key_path: str | None = None
```

**Additional Changes:**

1. Add startup validation:
```python
# File: start_server.py (add check)
if config.channels.mobile.tls_enabled:
    if not config.channels.mobile.tls_cert_path:
        logger.error("TLS enabled but no cert path configured!")
        if not is_demo_mode:
            raise ValueError("TLS cert required in production")
```

2. Create TLS setup guide:
```bash
# File: docs/TLS_SETUP.md
# Quick TLS Setup with Let's Encrypt
# 1. Install certbot
# 2. Generate cert
# 3. Configure paths
```

3. Add dashboard warning:
```javascript
// File: dashboard/static/js/dashboard.js
// Add TLS status indicator if not enabled
if (!config.tls_enabled) {
    showWarning("⚠️ TLS disabled - not secure for production");
}
```

**Testing:**
- Generate self-signed cert for testing
- Test WSS connection from mobile
- Verify cert validation works
- Test cert renewal process

---

### Task 1.2: Fix CORS Configuration (2 hours)

**Issue:** P0-003 - CORS accepts all origins

**Implementation:**

```python
# File: nanobot/config/schema.py
class NetworkConfig(BaseModel):
    """Network configuration for enterprise deployments."""
    proxy_enabled: bool = False
    proxy_url: str | None = None
    vpn_required: bool = False
    allowed_origins: list[str] = Field(default_factory=lambda: [])  # CHANGE: Was ["*"]
```

```python
# File: nanobot/api/app.py
def create_app(...) -> FastAPI:
    # ...

    # CORS middleware with validation
    origins = config.network.allowed_origins
    if "*" in origins:
        logger.warning("⚠️ CORS allows all origins - insecure for production!")
        if not is_demo_mode:
            logger.error("Wildcard CORS not allowed in production")
            # Could raise error here or continue with warning

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins else ["http://localhost:8080"],  # Safe default
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],  # Explicit methods
        allow_headers=["*"],
    )
```

**Testing:**
- Test with allowed origin (should work)
- Test with disallowed origin (should fail)
- Test pre-flight requests
- Test credentials with CORS

---

### Task 1.3: Implement CSRF Protection (6 hours)

**Issue:** P0-004 - No CSRF protection on state-changing operations

**Implementation:**

```python
# File: nanobot/api/csrf.py (NEW FILE)
"""CSRF protection middleware for FastAPI."""

import secrets
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

CSRF_TOKEN_LENGTH = 32
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_COOKIE_NAME = "csrf_token"

class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware."""

    async def dispatch(self, request: Request, call_next):
        # Generate token for GET requests
        if request.method == "GET":
            if CSRF_COOKIE_NAME not in request.cookies:
                token = secrets.token_urlsafe(CSRF_TOKEN_LENGTH)
                response = await call_next(request)
                response.set_cookie(
                    CSRF_COOKIE_NAME,
                    token,
                    httponly=True,
                    samesite="strict",
                    secure=True,  # Only over HTTPS
                )
                return response

        # Validate token for state-changing methods
        elif request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # Skip WebSocket and health endpoints
            if request.url.path.startswith("/ws/") or request.url.path == "/api/health":
                return await call_next(request)

            cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
            header_token = request.headers.get(CSRF_HEADER_NAME)

            if not cookie_token or not header_token:
                raise HTTPException(status_code=403, detail="CSRF token missing")

            if cookie_token != header_token:
                raise HTTPException(status_code=403, detail="CSRF token invalid")

        return await call_next(request)
```

```python
# File: nanobot/api/app.py
from nanobot.api.csrf import CSRFMiddleware

def create_app(...) -> FastAPI:
    app = FastAPI(...)

    # Add CSRF middleware (after CORS, before routes)
    app.add_middleware(CSRFMiddleware)

    # ... rest of setup
```

**Dashboard Changes:**

```javascript
// File: dashboard/static/js/dashboard.js
class EntobotDashboard {
    constructor() {
        this.csrfToken = this.getCsrfToken();
    }

    getCsrfToken() {
        // Extract from cookie
        const name = "csrf_token=";
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name)) {
                return cookie.substring(name.length);
            }
        }
        return null;
    }

    async generateQRCode() {
        const response = await fetch('/api/dashboard/generate-qr', {
            method: 'POST',
            headers: {
                'X-CSRF-Token': this.csrfToken  // Add CSRF header
            }
        });
        // ... rest
    }
}
```

**Testing:**
- Test POST without CSRF token (should fail)
- Test POST with wrong token (should fail)
- Test POST with correct token (should succeed)
- Test GET requests work without token

---

### Task 1.4: Fix JWT Secret Handling (6 hours)

**Issues:** P0-001, P0-005 - Weak secret handling and plaintext storage

**Implementation:**

```python
# File: nanobot/config/schema.py
import os

class AuthConfig(BaseModel):
    """Authentication configuration."""
    jwt_secret: str = Field(default="")  # Will validate on load
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24 * 7  # CHANGE: 7 days instead of 30

    @validator('jwt_secret')
    def validate_jwt_secret(cls, v):
        """Validate JWT secret strength."""
        # Check environment variable first
        env_secret = os.environ.get('NANOBOT_JWT_SECRET')
        if env_secret:
            v = env_secret

        if not v:
            raise ValueError("JWT secret is required. Set NANOBOT_JWT_SECRET environment variable.")

        if len(v) < 32:
            raise ValueError(f"JWT secret must be at least 32 characters (got {len(v)})")

        # Check for common weak patterns
        weak_patterns = [
            "change", "replace", "secret", "password", "example",
            "12345", "qwerty", "abc123"
        ]
        v_lower = v.lower()
        if any(pattern in v_lower for pattern in weak_patterns):
            raise ValueError("JWT secret appears to be a placeholder or weak pattern")

        return v
```

```python
# File: nanobot/auth/jwt_manager.py
def __init__(self, secret: str, algorithm: str = "HS256", expiry_hours: int = 24 * 7):
    """
    Initialize JWT manager.

    Args:
        secret: Secret key for signing tokens (must be strong in production)
        algorithm: JWT signing algorithm (default: HS256)
        expiry_hours: Token expiry time in hours (default: 7 days)
    """
    # Remove the weak secret generation - should fail instead
    if not secret or len(secret) < 32:
        raise ValueError(
            "JWT secret must be at least 32 characters. "
            "Set NANOBOT_JWT_SECRET environment variable or configure in config file."
        )

    self.secret = secret
    self.algorithm = algorithm
    self.expiry_hours = expiry_hours
```

**Config File Security:**

```python
# File: nanobot/config/loader.py (NEW or modify existing)
import os
import stat
from pathlib import Path

def load_config(config_path: Path) -> Config:
    """Load and validate config file with security checks."""

    # Check file permissions
    if config_path.exists():
        file_stat = config_path.stat()
        file_mode = stat.filemode(file_stat.st_mode)

        # Check if world-readable or group-readable
        if file_stat.st_mode & (stat.S_IROTH | stat.S_IRGRP):
            logger.warning(
                f"⚠️ Config file {config_path} has insecure permissions: {file_mode}\n"
                f"   Recommended: chmod 600 {config_path}"
            )
            # Could auto-fix: config_path.chmod(0o600)

    # Load config
    config = Config.parse_file(config_path)

    # Additional runtime validation
    if not config.auth.jwt_secret:
        raise ValueError("JWT secret must be configured")

    return config
```

**Documentation Update:**

```markdown
# File: QUICKSTART.md (add section)

## Security Configuration

### JWT Secret (CRITICAL)

The JWT secret is used to sign authentication tokens. It MUST be strong and kept secret.

**Option 1: Environment Variable (Recommended)**
```bash
export NANOBOT_JWT_SECRET="your-very-strong-random-secret-at-least-32-chars"
python -m nanobot gateway
```

**Option 2: Config File**
```bash
# Generate strong secret
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Add to config.json
{
  "auth": {
    "jwt_secret": "paste-generated-secret-here"
  }
}

# Secure the file
chmod 600 ~/.nanobot/config.json
```

**Never commit secrets to version control!**
```

**Testing:**
- Test with no secret (should fail to start)
- Test with weak secret (should fail)
- Test with env var override (should work)
- Test with strong secret in file (should work)
- Verify file permission check works

---

## Sprint 2: High Priority Fixes (Week 2-3) ⚠️

**Goal:** Address high-priority security and functionality gaps
**Duration:** 67 hours (~8-10 days)
**Priority:** HIGH

### Task 2.1: Add Authentication Middleware (6 hours)

**Issue:** P1-005 - Missing auth on protected endpoints

```python
# File: nanobot/api/middleware/auth.py (NEW FILE)
"""JWT authentication middleware for FastAPI."""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> str:
    """
    Verify JWT token from Authorization header.

    Returns device_id if valid, raises HTTPException if invalid.
    """
    token = credentials.credentials
    jwt_manager = request.app.state.jwt_manager

    device_id = jwt_manager.validate_token(token)

    if not device_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return device_id
```

```python
# File: nanobot/api/auth.py (update endpoints)
@router.get("/devices", response_model=DevicesResponse)
async def list_devices(
    device_id: str = Depends(verify_jwt_token),  # ADD authentication
    request: Request = None
):
    """List all currently connected devices. Requires authentication."""

    # Get WebSocket server from app state
    ws_server = request.app.state.websocket_server

    if ws_server:
        devices = ws_server.get_connected_devices()
        return DevicesResponse(devices=devices)

    return DevicesResponse(devices=[])
```

---

### Task 2.2: Implement Token Revocation (8 hours)

**Issue:** P1-002 - No way to invalidate tokens

**Option A: In-Memory Blacklist (Simple)**

```python
# File: nanobot/auth/token_blacklist.py (NEW FILE)
"""Token blacklist for revocation."""

import time
from typing import Set

class TokenBlacklist:
    """Simple in-memory token blacklist."""

    def __init__(self):
        self._blacklist: Set[str] = set()
        self._expiry_times: dict[str, float] = {}

    def revoke(self, token: str, expiry: float):
        """Add token to blacklist until it expires."""
        self._blacklist.add(token)
        self._expiry_times[token] = expiry

    def is_revoked(self, token: str) -> bool:
        """Check if token is revoked."""
        if token in self._blacklist:
            # Check if still needs to be blacklisted
            if time.time() < self._expiry_times.get(token, 0):
                return True
            else:
                # Token expired naturally, remove from blacklist
                self._blacklist.discard(token)
                self._expiry_times.pop(token, None)
        return False

    def cleanup_expired(self):
        """Remove expired tokens from blacklist."""
        now = time.time()
        expired = [
            token for token, expiry in self._expiry_times.items()
            if now >= expiry
        ]
        for token in expired:
            self._blacklist.discard(token)
            self._expiry_times.pop(token, None)
```

**Option B: Redis (Production-Ready)**

```python
# File: nanobot/auth/token_blacklist_redis.py (NEW FILE)
"""Redis-based token blacklist for production."""

import redis
from typing import Optional

class RedisTokenBlacklist:
    """Production token blacklist using Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(redis_url)

    def revoke(self, token: str, expiry_seconds: int):
        """Revoke token with TTL."""
        self.redis.setex(f"revoked:{token}", expiry_seconds, "1")

    def is_revoked(self, token: str) -> bool:
        """Check if token is revoked."""
        return self.redis.exists(f"revoked:{token}") > 0
```

**Update JWT Validation:**

```python
# File: nanobot/auth/jwt_manager.py
def validate_token(self, token: str, blacklist: Optional[TokenBlacklist] = None) -> str | None:
    """
    Validate a JWT token and extract device_id.

    Args:
        token: JWT token to validate
        blacklist: Optional token blacklist for revocation checks

    Returns:
        device_id if valid, None if invalid or expired
    """
    # Check blacklist first (fast path)
    if blacklist and blacklist.is_revoked(token):
        logger.warning("JWT token has been revoked")
        return None

    # ... rest of validation
```

---

### Task 2.3: Reduce Token Expiry (2 hours)

**Issue:** P1-003 - 30 days too long

Already addressed in Task 1.4 (changed default to 7 days).

Additional: Implement refresh token flow for longer sessions.

---

### Task 2.4: Add WebSocket Rate Limiting (4 hours)

**Issue:** P1-004 - No rate limiting on WebSocket messages

```python
# File: nanobot/gateway/websocket.py
async def _handle_client_message(
    self, websocket: WebSocketServerProtocol, data: dict[str, Any]
) -> None:
    """Handle message from authenticated client."""
    # Check if client is authenticated
    device_id = self._find_device_id_by_websocket(websocket)
    if not device_id:
        await self._send_error(websocket, "Not authenticated")
        return

    # ADD: Rate limit check
    if hasattr(self, 'rate_limiter'):
        allowed, error_msg = self.rate_limiter.check_rate_limit(device_id)
        if not allowed:
            await self._send_error(websocket, error_msg)
            return

    # ... rest of message handling
```

---

### Task 2.5: Add Unit & Integration Tests (32 hours)

**Critical test coverage:**

1. JWT tests (4 hours)
2. Pairing tests (4 hours)
3. WebSocket auth tests (6 hours)
4. Rate limiter tests (4 hours)
5. CSRF protection tests (4 hours)
6. Integration tests (10 hours)

---

### Task 2.6: Performance & Load Testing (8 hours)

1. Load test with 100 concurrent WebSockets (4 hours)
2. Message throughput testing (2 hours)
3. Memory leak detection (2 hours)

---

### Task 2.7: Accessibility Audit (16 hours)

1. Screen reader testing (6 hours)
2. Keyboard navigation (4 hours)
3. Color contrast verification (2 hours)
4. ARIA labels (4 hours)

---

## Sprint 3: Polish & Documentation (Week 4+) ✨

**Goal:** Production-ready documentation and enhancements
**Duration:** 40+ hours
**Priority:** MEDIUM

- Complete all P2 issues
- Enhance documentation
- Add deployment guides
- Implement monitoring
- Performance optimization

---

## Quick Win: Pre-Demo Improvements (Today) ⚡

If you have 2 hours before the demo:

### 1. Add TLS Status Warning (30 min)

```python
# File: dashboard/app.py
@app.get("/api/dashboard/status")
async def get_status():
    # ... existing code ...

    return {
        "status": "online",
        "devices": devices,
        "sessions": sessions,
        "messages": state.message_count,
        "uptime": state.get_uptime(),
        "tls_enabled": state.websocket_server.tls_enabled if state.websocket_server else False,  # ADD
        "demo_mode": state.demo_mode
    }
```

```javascript
// File: dashboard/static/js/dashboard.js
async updateStatus() {
    const data = await response.json();

    // ADD TLS warning
    if (!data.tls_enabled && !data.demo_mode) {
        this.showNotification('⚠️ TLS disabled - communications not encrypted', 'warning');
    }
}
```

### 2. Test Full Flow (30 min)

```bash
# Start backend
python3 start_server.py

# Open dashboard
# Generate QR code
# Scan with mobile app (if available)
# Send test message
# Verify it appears in dashboard
```

### 3. Prepare Demo Script (30 min)

Create talking points for demo:
- "This is v1.0 with focus on core functionality"
- "Security hardening is next sprint (we have a 32-item QA report)"
- "P0 issues identified and prioritized"
- "3-week timeline to production-ready"

### 4. Review QA Report (30 min)

Familiarize yourself with issues so you can answer questions confidently.

---

## Success Criteria

### ✅ Demo Success
- Dashboard loads and looks professional
- QR code generates
- Real-time updates work
- No crashes during demo
- Can articulate security roadmap

### ✅ Production Ready (After Sprint 1)
- All P0 issues fixed
- TLS enabled by default
- CORS configured properly
- CSRF protection active
- JWT secrets secure
- Basic tests passing

### ✅ Enterprise Ready (After Sprint 2-3)
- All P1 issues fixed
- Comprehensive test suite
- Load tested to 100+ users
- Accessibility compliant
- Full documentation
- Security audit complete

---

## Resources Needed

- **Development time:** 3-4 weeks full-time
- **Testing devices:** iOS and Android phones
- **Infrastructure:** SSL certificates, Redis (optional)
- **Tools:** pytest, Lighthouse, screen reader
- **Review:** Security audit (optional but recommended)

---

## Next Steps

1. ✅ Review this action plan
2. ✅ Present to team/stakeholders
3. ✅ Prioritize based on timeline
4. 🔧 Start Sprint 1 (Critical Fixes)
5. 🧪 Implement test suite
6. 📊 Track progress
7. 🚀 Deploy to production

---

**Good luck with the demo tonight! You've built something impressive.** 🎉
