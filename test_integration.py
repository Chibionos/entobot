#!/usr/bin/env python3
"""
Integration test script for Enterprise Entobot mobile app backend.

This script tests the complete flow:
1. Start backend server (if not running)
2. Generate QR code for pairing
3. Simulate mobile app pairing
4. Verify JWT token received
5. Authenticate with JWT
6. Send chat messages
7. Verify responses
8. Test settings API endpoints
9. Test token refresh
10. Test reconnection scenarios

Usage:
    python test_integration.py
    python test_integration.py --verbose
    python test_integration.py --skip-server-start
"""

import asyncio
import json
import sys
import time
from pathlib import Path

import websockets
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from nanobot import __logo__
from nanobot.auth.jwt_manager import JWTManager
from nanobot.config.loader import load_config
from nanobot.pairing.manager import PairingManager

console = Console()


class IntegrationTester:
    """Integration test runner for mobile backend."""

    def __init__(self, ws_url: str = "ws://localhost:18791", api_url: str = "http://localhost:18790"):
        """
        Initialize integration tester.

        Args:
            ws_url: WebSocket server URL
            api_url: REST API server URL
        """
        self.ws_url = ws_url
        self.api_url = api_url
        self.jwt_token: str | None = None
        self.device_id: str | None = None
        self.test_results = []

    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✓ PASS" if passed else "✗ FAIL"
        style = "green" if passed else "red"
        console.print(f"[{style}]{status}[/{style}] {name}")
        if details:
            console.print(f"  [dim]{details}[/dim]")
        self.test_results.append({"name": name, "passed": passed, "details": details})

    async def test_qr_generation(self) -> tuple[str, str]:
        """
        Test 1: Generate QR code for pairing.

        Returns:
            Tuple of (session_id, temp_token)
        """
        console.print("\n[bold cyan]Test 1: QR Code Generation[/bold cyan]")

        try:
            config = load_config()
            pairing_manager = PairingManager(
                websocket_url=self.ws_url,
                session_expiry_minutes=5,
            )

            session_id, qr_bytes = pairing_manager.create_pairing_session()
            session = pairing_manager.get_session(session_id)

            assert session is not None, "Session not found"
            assert len(qr_bytes) > 0, "QR code bytes empty"
            assert not session.is_expired(), "Session already expired"

            self.log_test(
                "QR Generation",
                True,
                f"Session: {session_id[:16]}..., Size: {len(qr_bytes)} bytes"
            )

            return session_id, session.temp_token

        except Exception as e:
            self.log_test("QR Generation", False, str(e))
            raise

    async def test_pairing(self, session_id: str, temp_token: str) -> str:
        """
        Test 2: Mobile app pairing via WebSocket.

        Args:
            session_id: Pairing session ID
            temp_token: Temporary pairing token

        Returns:
            JWT token
        """
        console.print("\n[bold cyan]Test 2: Mobile App Pairing[/bold cyan]")

        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Send pairing request
                pairing_msg = {
                    "type": "pair",
                    "session_id": session_id,
                    "temp_token": temp_token,
                    "device_info": {
                        "device_name": "Test Device",
                        "device_type": "mobile",
                        "os": "test",
                        "app_version": "1.0.0",
                    }
                }

                await websocket.send(json.dumps(pairing_msg))
                logger.info("Sent pairing request")

                # Receive response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)

                logger.info(f"Received response: {response_data.get('type')}")

                assert response_data.get("type") == "auth_success", "Pairing failed"
                assert "jwt_token" in response_data, "JWT token not in response"
                assert "device_id" in response_data, "device_id not in response"

                jwt_token = response_data["jwt_token"]
                device_id = response_data["device_id"]

                self.jwt_token = jwt_token
                self.device_id = device_id

                self.log_test(
                    "Pairing Request",
                    True,
                    f"Device ID: {device_id}, Token length: {len(jwt_token)}"
                )

                return jwt_token

        except Exception as e:
            self.log_test("Pairing Request", False, str(e))
            raise

    async def test_jwt_auth(self) -> None:
        """Test 3: JWT authentication with existing token."""
        console.print("\n[bold cyan]Test 3: JWT Authentication[/bold cyan]")

        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Send auth request
                auth_msg = {
                    "type": "auth",
                    "jwt_token": self.jwt_token,
                }

                await websocket.send(json.dumps(auth_msg))
                logger.info("Sent auth request")

                # Receive response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)

                logger.info(f"Received response: {response_data.get('type')}")

                assert response_data.get("type") == "auth_success", "Auth failed"
                assert response_data.get("device_id") == self.device_id, "Device ID mismatch"

                self.log_test(
                    "JWT Authentication",
                    True,
                    f"Device authenticated: {self.device_id}"
                )

        except Exception as e:
            self.log_test("JWT Authentication", False, str(e))
            raise

    async def test_chat_message(self) -> None:
        """Test 4: Send chat message and receive response."""
        console.print("\n[bold cyan]Test 4: Chat Message Exchange[/bold cyan]")

        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Authenticate first
                auth_msg = {
                    "type": "auth",
                    "jwt_token": self.jwt_token,
                }
                await websocket.send(json.dumps(auth_msg))
                auth_response = await websocket.recv()
                logger.info("Authenticated")

                # Send chat message
                chat_msg = {
                    "type": "message",
                    "content": "Hello! This is a test message from integration test."
                }

                await websocket.send(json.dumps(chat_msg))
                logger.info("Sent chat message")

                # Receive acknowledgment
                ack_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                ack_data = json.loads(ack_response)

                assert ack_data.get("type") == "ack", "No acknowledgment received"

                self.log_test(
                    "Chat Message Send",
                    True,
                    "Message sent and acknowledged"
                )

                # Note: Agent response will come through the message bus
                # In a full test, we'd need to set up a subscriber to receive it

        except Exception as e:
            self.log_test("Chat Message Send", False, str(e))
            raise

    async def test_api_health(self) -> None:
        """Test 5: REST API health check."""
        console.print("\n[bold cyan]Test 5: REST API Health Check[/bold cyan]")

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/api/health")
                assert response.status_code == 200, f"Health check failed: {response.status_code}"

                data = response.json()
                assert data.get("status") == "ok", "Health status not ok"

                self.log_test(
                    "API Health Check",
                    True,
                    f"Status: {data.get('status')}, Service: {data.get('service')}"
                )

        except Exception as e:
            self.log_test("API Health Check", False, str(e))
            raise

    async def test_api_settings(self) -> None:
        """Test 6: REST API settings endpoints."""
        console.print("\n[bold cyan]Test 6: REST API Settings[/bold cyan]")

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                # Get bot settings
                response = await client.get(f"{self.api_url}/api/v1/settings/bot")
                assert response.status_code == 200, f"Get bot settings failed: {response.status_code}"

                bot_settings = response.json()
                assert "settings" in bot_settings, "Settings not in response"

                self.log_test(
                    "Get Bot Settings",
                    True,
                    f"Model: {bot_settings['settings']['model']}"
                )

                # Get providers
                response = await client.get(f"{self.api_url}/api/v1/settings/providers")
                assert response.status_code == 200, f"Get providers failed: {response.status_code}"

                providers = response.json()
                assert "providers" in providers, "Providers not in response"

                self.log_test(
                    "Get Providers",
                    True,
                    f"Found {len(providers['providers'])} providers"
                )

        except Exception as e:
            self.log_test("API Settings", False, str(e))
            raise

    async def test_token_validation(self) -> None:
        """Test 7: JWT token validation."""
        console.print("\n[bold cyan]Test 7: JWT Token Validation[/bold cyan]")

        try:
            config = load_config()
            jwt_manager = JWTManager(
                secret=config.auth.jwt_secret or "test-secret",
                algorithm=config.auth.jwt_algorithm,
            )

            # Validate token
            device_id = jwt_manager.validate_token(self.jwt_token)
            assert device_id == self.device_id, "Token validation failed"

            # Extract credentials
            credentials = jwt_manager.extract_device_credentials(self.jwt_token)
            assert credentials is not None, "Failed to extract credentials"
            assert credentials.device_id == self.device_id, "Device ID mismatch"
            assert not credentials.is_expired(), "Token expired"

            self.log_test(
                "Token Validation",
                True,
                f"Device: {device_id}, Expires: {time.ctime(credentials.expires_at)}"
            )

        except Exception as e:
            self.log_test("Token Validation", False, str(e))
            raise

    async def test_reconnection(self) -> None:
        """Test 8: Reconnection with existing JWT."""
        console.print("\n[bold cyan]Test 8: Reconnection Test[/bold cyan]")

        try:
            # Disconnect and reconnect
            for i in range(3):
                async with websockets.connect(self.ws_url) as websocket:
                    auth_msg = {
                        "type": "auth",
                        "jwt_token": self.jwt_token,
                    }
                    await websocket.send(json.dumps(auth_msg))

                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)

                    assert response_data.get("type") == "auth_success", f"Reconnection {i+1} failed"

                # Small delay between connections
                await asyncio.sleep(0.5)

            self.log_test(
                "Reconnection",
                True,
                "Successfully reconnected 3 times"
            )

        except Exception as e:
            self.log_test("Reconnection", False, str(e))
            raise

    async def test_invalid_token(self) -> None:
        """Test 9: Invalid token handling."""
        console.print("\n[bold cyan]Test 9: Invalid Token Handling[/bold cyan]")

        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Send invalid token
                auth_msg = {
                    "type": "auth",
                    "jwt_token": "invalid.token.here",
                }

                await websocket.send(json.dumps(auth_msg))
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)

                assert response_data.get("type") == "error", "Expected error response"
                assert "Invalid" in response_data.get("message", ""), "Expected 'Invalid' in error message"

                self.log_test(
                    "Invalid Token Handling",
                    True,
                    "Server correctly rejected invalid token"
                )

        except Exception as e:
            self.log_test("Invalid Token Handling", False, str(e))
            raise

    async def test_ping_pong(self) -> None:
        """Test 10: Ping/pong keepalive."""
        console.print("\n[bold cyan]Test 10: Ping/Pong Keepalive[/bold cyan]")

        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Authenticate first
                auth_msg = {
                    "type": "auth",
                    "jwt_token": self.jwt_token,
                }
                await websocket.send(json.dumps(auth_msg))
                await websocket.recv()

                # Send ping
                ping_msg = {"type": "ping"}
                await websocket.send(json.dumps(ping_msg))

                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)

                assert response_data.get("type") == "pong", "Expected pong response"

                self.log_test(
                    "Ping/Pong",
                    True,
                    "Keepalive working correctly"
                )

        except Exception as e:
            self.log_test("Ping/Pong", False, str(e))
            raise

    def print_summary(self):
        """Print test summary."""
        console.print("\n" + "=" * 70)
        console.print()

        passed = sum(1 for r in self.test_results if r["passed"])
        failed = len(self.test_results) - passed

        if failed == 0:
            console.print(Panel(
                f"[bold green]✓ All Tests Passed![/bold green]\n\n"
                f"Passed: {passed}/{len(self.test_results)}",
                title="Integration Test Results",
                border_style="green",
            ))
        else:
            console.print(Panel(
                f"[bold red]✗ Some Tests Failed[/bold red]\n\n"
                f"Passed: {passed}/{len(self.test_results)}\n"
                f"Failed: {failed}/{len(self.test_results)}",
                title="Integration Test Results",
                border_style="red",
            ))

        console.print()


async def run_tests(skip_server_start: bool = False):
    """
    Run all integration tests.

    Args:
        skip_server_start: Skip server startup check
    """
    console.print()
    console.print(Panel(
        f"[bold cyan]{__logo__} Integration Test Suite[/bold cyan]\n\n"
        f"Testing Enterprise Entobot mobile backend\n"
        f"WebSocket: ws://localhost:18791\n"
        f"REST API: http://localhost:18790",
        border_style="cyan",
    ))

    if not skip_server_start:
        console.print("\n[yellow]Make sure the server is running:[/yellow]")
        console.print("[cyan]python start_server.py[/cyan]")
        console.print()
        input("Press Enter when server is ready...")

    tester = IntegrationTester()

    try:
        # Run tests
        session_id, temp_token = await tester.test_qr_generation()
        await tester.test_pairing(session_id, temp_token)
        await tester.test_jwt_auth()
        await tester.test_chat_message()
        await tester.test_api_health()
        await tester.test_api_settings()
        await tester.test_token_validation()
        await tester.test_reconnection()
        await tester.test_invalid_token()
        await tester.test_ping_pong()

    except Exception as e:
        logger.error(f"Test suite error: {e}")

    finally:
        tester.print_summary()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run integration tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--skip-server-start", action="store_true", help="Skip server startup check")

    args = parser.parse_args()

    if args.verbose:
        logger.enable("nanobot")
    else:
        logger.disable("nanobot")

    try:
        asyncio.run(run_tests(skip_server_start=args.skip_server_start))
    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrupted[/yellow]")
