#!/usr/bin/env python3
"""
Integration test script for enterprise mobile backend.

Tests:
1. QR code generation
2. WebSocket server initialization
3. JWT token generation and validation
4. REST API endpoint availability
"""

import asyncio
import sys
from pathlib import Path

# Add nanobot to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all new modules can be imported."""
    print("\n=== Testing Imports ===")
    try:
        from nanobot.pairing.manager import PairingManager, PairingSession
        print("✓ Pairing manager imported")

        from nanobot.auth.jwt_manager import JWTManager
        print("✓ JWT manager imported")

        from nanobot.gateway.websocket import SecureWebSocketServer
        print("✓ WebSocket server imported")

        from nanobot.security.hardening import RateLimiter, AuditLogger, SecurityValidator
        print("✓ Security components imported")

        from nanobot.api.app import create_app
        print("✓ REST API app imported")

        from nanobot.config.schema import (
            MobileAppConfig,
            AuthConfig,
            EnterpriseConfig,
            NetworkConfig,
        )
        print("✓ Enterprise config schemas imported")

        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_qr_generation():
    """Test QR code generation."""
    print("\n=== Testing QR Code Generation ===")
    try:
        from nanobot.pairing.manager import PairingManager

        manager = PairingManager(websocket_url="ws://localhost:18791")
        session_id, qr_bytes = manager.create_pairing_session()

        print(f"✓ Session ID: {session_id}")
        print(f"✓ QR code size: {len(qr_bytes)} bytes")
        print(f"✓ Active sessions: {manager.get_active_session_count()}")

        # Test ASCII QR
        session = manager.get_session(session_id)
        ascii_qr = manager.generate_qr_ascii(session_id, session.temp_token)
        print(f"✓ ASCII QR generated: {len(ascii_qr)} chars")

        return True
    except Exception as e:
        print(f"✗ QR generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_jwt_tokens():
    """Test JWT token generation and validation."""
    print("\n=== Testing JWT Tokens ===")
    try:
        from nanobot.auth.jwt_manager import JWTManager

        jwt_mgr = JWTManager(secret="test_secret_key_1234567890", expiry_hours=24)

        # Generate token
        token = jwt_mgr.generate_token("device_001", "Test Device")
        print(f"✓ Token generated: {token[:50]}...")

        # Validate token
        device_id = jwt_mgr.validate_token(token)
        print(f"✓ Token validated: device_id={device_id}")

        # Extract credentials
        creds = jwt_mgr.extract_device_credentials(token)
        print(f"✓ Credentials extracted: {creds.device_name}")

        # Refresh token
        new_token = jwt_mgr.refresh_token(token)
        print(f"✓ Token refreshed: {new_token[:50]}...")

        return True
    except Exception as e:
        print(f"✗ JWT test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_websocket_server():
    """Test WebSocket server initialization."""
    print("\n=== Testing WebSocket Server ===")
    try:
        from nanobot.auth.jwt_manager import JWTManager
        from nanobot.bus.queue import MessageBus
        from nanobot.gateway.websocket import SecureWebSocketServer
        from nanobot.pairing.manager import PairingManager

        # Create dependencies
        pairing_mgr = PairingManager(websocket_url="ws://localhost:18791")
        jwt_mgr = JWTManager(secret="test_secret_key", expiry_hours=24)
        message_bus = MessageBus()

        # Create server
        server = SecureWebSocketServer(
            host="localhost",
            port=18791,
            pairing_manager=pairing_mgr,
            jwt_manager=jwt_mgr,
            message_bus=message_bus,
            tls_enabled=False,
        )

        print("✓ WebSocket server created")
        print(f"✓ Server running: {server.is_running}")
        print(f"✓ Connection count: {server.connection_count}")

        # Note: Not actually starting server to avoid port conflicts
        # Just testing initialization

        return True
    except Exception as e:
        print(f"✗ WebSocket test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_security_components():
    """Test security hardening components."""
    print("\n=== Testing Security Components ===")
    try:
        from nanobot.security.hardening import RateLimiter, AuditLogger, SecurityValidator
        import tempfile

        # Test rate limiter
        rate_limiter = RateLimiter(requests_per_minute=60)
        allowed, error = rate_limiter.check_rate_limit("device_001")
        print(f"✓ Rate limiter: allowed={allowed}, error={error}")

        # Test audit logger
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            audit_log_path = Path(f.name)

        audit_logger = AuditLogger(log_path=audit_log_path)
        audit_logger.log_authentication("device_001", "127.0.0.1", True)
        print(f"✓ Audit logger: {audit_log_path}")

        # Test security validator
        validator = SecurityValidator(ip_whitelist=["127.0.0.1"], enable_whitelist=False)
        valid, error = validator.validate_ip_address("127.0.0.1")
        print(f"✓ Security validator: valid={valid}")

        # Cleanup
        audit_log_path.unlink(missing_ok=True)

        return True
    except Exception as e:
        print(f"✗ Security test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rest_api():
    """Test REST API creation."""
    print("\n=== Testing REST API ===")
    try:
        from nanobot.api.app import create_app
        from nanobot.auth.jwt_manager import JWTManager
        from nanobot.config.loader import load_config
        from nanobot.pairing.manager import PairingManager

        config = load_config()
        pairing_mgr = PairingManager(websocket_url="ws://localhost:18791")
        jwt_mgr = JWTManager(secret="test_secret", expiry_hours=24)

        app = create_app(config, pairing_mgr, jwt_mgr)
        print(f"✓ FastAPI app created: {app.title}")
        print(f"✓ Routes: {len(app.routes)}")

        # List some routes
        route_paths = [route.path for route in app.routes if hasattr(route, "path")]
        print(f"✓ Sample routes: {route_paths[:5]}")

        return True
    except Exception as e:
        print(f"✗ REST API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_schema():
    """Test enterprise configuration schema."""
    print("\n=== Testing Configuration Schema ===")
    try:
        from nanobot.config.schema import Config

        config = Config()
        print(f"✓ Mobile app enabled: {config.channels.mobile.enabled}")
        print(f"✓ WebSocket port: {config.channels.mobile.websocket_port}")
        print(f"✓ JWT algorithm: {config.auth.jwt_algorithm}")
        print(f"✓ Rate limit enabled: {config.enterprise.rate_limit_enabled}")
        print(f"✓ Audit log enabled: {config.enterprise.audit_log_enabled}")

        return True
    except Exception as e:
        print(f"✗ Config schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("ENTERPRISE MOBILE BACKEND INTEGRATION TESTS")
    print("=" * 60)

    results = {
        "Imports": test_imports(),
        "Configuration Schema": test_config_schema(),
        "QR Code Generation": test_qr_generation(),
        "JWT Tokens": test_jwt_tokens(),
        "WebSocket Server": asyncio.run(test_websocket_server()),
        "Security Components": test_security_components(),
        "REST API": test_rest_api(),
    }

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ All tests passed! Enterprise backend is ready.")
        return 0
    else:
        print("\n✗ Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
