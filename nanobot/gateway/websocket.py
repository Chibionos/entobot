"""Secure WebSocket server for mobile app communication."""

from __future__ import annotations

import asyncio
import json
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TYPE_CHECKING

import websockets
from loguru import logger
from websockets.server import WebSocketServerProtocol

if TYPE_CHECKING:
    from nanobot.auth.jwt_manager import JWTManager
    from nanobot.bus.queue import MessageBus
    from nanobot.pairing.manager import PairingManager


@dataclass
class AuthenticatedClient:
    """Represents an authenticated mobile app client."""

    device_id: str
    device_name: str
    websocket: WebSocketServerProtocol
    authenticated_at: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "authenticated_at": self.authenticated_at,
        }


class SecureWebSocketServer:
    """
    Secure WebSocket server for mobile app communication.

    Supports two authentication methods:
    1. Pairing: New devices scan QR code and pair with temp token
    2. JWT: Previously paired devices authenticate with JWT token

    Message Format:
    - Client -> Server (auth):
        {"type": "pair", "session_id": "...", "temp_token": "...", "device_info": {...}}
        {"type": "auth", "jwt_token": "..."}
    - Client -> Server (message):
        {"type": "message", "content": "..."}
    - Server -> Client:
        {"type": "auth_success", "jwt_token": "...", "device_id": "..."}
        {"type": "error", "message": "..."}
        {"type": "message", "content": "..."}
    """

    def __init__(
        self,
        host: str,
        port: int,
        pairing_manager: PairingManager,
        jwt_manager: JWTManager,
        message_bus: MessageBus,
        tls_enabled: bool = False,
        tls_cert_path: Path | None = None,
        tls_key_path: Path | None = None,
        max_connections: int = 100,
        heartbeat_interval: int = 30,
    ):
        """
        Initialize WebSocket server.

        Args:
            host: Server host
            port: Server port
            pairing_manager: QR code pairing manager
            jwt_manager: JWT token manager
            message_bus: Message bus for agent communication
            tls_enabled: Enable TLS/SSL
            tls_cert_path: Path to TLS certificate
            tls_key_path: Path to TLS private key
            max_connections: Maximum concurrent connections
            heartbeat_interval: Heartbeat interval in seconds
        """
        self.host = host
        self.port = port
        self.pairing_manager = pairing_manager
        self.jwt_manager = jwt_manager
        self.message_bus = message_bus
        self.tls_enabled = tls_enabled
        self.tls_cert_path = tls_cert_path
        self.tls_key_path = tls_key_path
        self.max_connections = max_connections
        self.heartbeat_interval = heartbeat_interval

        self.authenticated_clients: dict[str, AuthenticatedClient] = {}
        self._server: Any = None
        self._running = False

    async def start(self) -> None:
        """Start the WebSocket server."""
        if self._running:
            logger.warning("WebSocket server already running")
            return

        # Setup SSL context if TLS enabled
        ssl_context = None
        if self.tls_enabled:
            if not self.tls_cert_path or not self.tls_key_path:
                logger.error("TLS enabled but cert/key paths not provided")
                return

            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(str(self.tls_cert_path), str(self.tls_key_path))
            logger.info("TLS/SSL enabled for WebSocket server")

        # Start server
        self._server = await websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
            ssl=ssl_context,
            max_size=10_000_000,  # 10MB max message size
            ping_interval=self.heartbeat_interval,
            ping_timeout=self.heartbeat_interval * 2,
        )

        self._running = True
        protocol = "wss" if self.tls_enabled else "ws"
        logger.info(f"Secure WebSocket server started on {protocol}://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        if not self._running:
            return

        self._running = False

        # Close all client connections
        for client in list(self.authenticated_clients.values()):
            try:
                await client.websocket.close()
            except Exception as e:
                logger.error(f"Error closing client connection: {e}")

        self.authenticated_clients.clear()

        # Stop server
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        logger.info("Secure WebSocket server stopped")

    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle incoming WebSocket connection."""
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        logger.info(f"New WebSocket connection from {client_ip}")

        try:
            async for message in websocket:
                try:
                    await self._handle_message(websocket, message, client_ip)
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await self._send_error(websocket, str(e))

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed from {client_ip}")
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            # Remove from authenticated clients if present
            device_id = self._find_device_id_by_websocket(websocket)
            if device_id:
                del self.authenticated_clients[device_id]
                logger.info(f"Device disconnected: {device_id}")

    def _find_device_id_by_websocket(self, websocket: WebSocketServerProtocol) -> str | None:
        """Find device_id by websocket connection."""
        for device_id, client in self.authenticated_clients.items():
            if client.websocket == websocket:
                return device_id
        return None

    async def _handle_message(
        self, websocket: WebSocketServerProtocol, message: str | bytes, client_ip: str
    ) -> None:
        """Handle incoming message from client."""
        if isinstance(message, bytes):
            message = message.decode("utf-8")

        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            await self._send_error(websocket, "Invalid JSON")
            return

        msg_type = data.get("type")

        if msg_type == "pair":
            await self._handle_pairing(websocket, data, client_ip)
        elif msg_type == "auth":
            await self._handle_jwt_auth(websocket, data, client_ip)
        elif msg_type == "message":
            await self._handle_client_message(websocket, data)
        elif msg_type == "ping":
            await self._send_json(websocket, {"type": "pong"})
        else:
            await self._send_error(websocket, f"Unknown message type: {msg_type}")

    async def _handle_pairing(
        self, websocket: WebSocketServerProtocol, data: dict[str, Any], client_ip: str
    ) -> None:
        """Handle device pairing request."""
        session_id = data.get("session_id")
        temp_token = data.get("temp_token")
        device_info = data.get("device_info", {})

        if not session_id or not temp_token:
            await self._send_error(websocket, "Missing session_id or temp_token")
            return

        # Validate pairing
        if not self.pairing_manager.validate_pairing(session_id, temp_token, device_info):
            await self._send_error(websocket, "Invalid pairing credentials")
            return

        # Generate device_id and JWT token
        device_name = device_info.get("device_name", "Unknown Device")
        device_id = f"device_{session_id[:8]}"

        jwt_token = self.jwt_manager.generate_token(device_id, device_name)

        # Add to authenticated clients
        import time
        client = AuthenticatedClient(
            device_id=device_id,
            device_name=device_name,
            websocket=websocket,
            authenticated_at=time.time(),
        )
        self.authenticated_clients[device_id] = client

        # Send success response
        await self._send_json(
            websocket,
            {
                "type": "auth_success",
                "jwt_token": jwt_token,
                "device_id": device_id,
                "device_name": device_name,
                "message": "Pairing successful",
            },
        )

        logger.info(f"Device paired successfully: {device_name} ({device_id}) from {client_ip}")

    async def _handle_jwt_auth(
        self, websocket: WebSocketServerProtocol, data: dict[str, Any], client_ip: str
    ) -> None:
        """Handle JWT authentication request."""
        jwt_token = data.get("jwt_token")

        if not jwt_token:
            await self._send_error(websocket, "Missing jwt_token")
            return

        # Validate JWT
        device_id = self.jwt_manager.validate_token(jwt_token)
        if not device_id:
            await self._send_error(websocket, "Invalid or expired JWT token")
            return

        # Get device credentials
        credentials = self.jwt_manager.extract_device_credentials(jwt_token)
        if not credentials:
            await self._send_error(websocket, "Failed to extract credentials from token")
            return

        # Add to authenticated clients
        client = AuthenticatedClient(
            device_id=device_id,
            device_name=credentials.device_name,
            websocket=websocket,
            authenticated_at=credentials.issued_at,
        )
        self.authenticated_clients[device_id] = client

        # Send success response
        await self._send_json(
            websocket,
            {
                "type": "auth_success",
                "device_id": device_id,
                "device_name": credentials.device_name,
                "message": "Authentication successful",
            },
        )

        logger.info(f"Device authenticated: {credentials.device_name} ({device_id}) from {client_ip}")

    async def _handle_client_message(
        self, websocket: WebSocketServerProtocol, data: dict[str, Any]
    ) -> None:
        """Handle message from authenticated client."""
        # Check if client is authenticated
        device_id = self._find_device_id_by_websocket(websocket)
        if not device_id:
            await self._send_error(websocket, "Not authenticated")
            return

        client = self.authenticated_clients.get(device_id)
        if not client:
            await self._send_error(websocket, "Authentication expired")
            return

        content = data.get("content")
        if not content:
            await self._send_error(websocket, "Missing message content")
            return

        logger.info(f"Message from {client.device_name} ({device_id}): {content[:50]}...")

        # Publish to message bus for agent processing
        from nanobot.bus.events import InboundMessage

        inbound_msg = InboundMessage(
            channel="mobile",
            chat_id=device_id,
            sender=client.device_name,
            content=content,
        )
        await self.message_bus.publish_inbound(inbound_msg)

        # Send acknowledgment
        await self._send_json(websocket, {"type": "ack", "message": "Message received"})

    async def _send_error(self, websocket: WebSocketServerProtocol, error_message: str) -> None:
        """Send error message to client."""
        await self._send_json(websocket, {"type": "error", "message": error_message})

    async def _send_json(self, websocket: WebSocketServerProtocol, data: dict[str, Any]) -> None:
        """Send JSON message to client."""
        try:
            await websocket.send(json.dumps(data))
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def broadcast_message(self, message: str, exclude_device_id: str | None = None) -> None:
        """
        Broadcast message to all connected clients.

        Args:
            message: Message content
            exclude_device_id: Optional device_id to exclude from broadcast
        """
        for device_id, client in list(self.authenticated_clients.items()):
            if device_id == exclude_device_id:
                continue

            try:
                await self._send_json(client.websocket, {"type": "message", "content": message})
            except Exception as e:
                logger.error(f"Failed to broadcast to {device_id}: {e}")

    async def send_to_device(self, device_id: str, message: str) -> bool:
        """
        Send message to specific device.

        Args:
            device_id: Target device ID
            message: Message content

        Returns:
            True if sent successfully
        """
        client = self.authenticated_clients.get(device_id)
        if not client:
            logger.warning(f"Device not connected: {device_id}")
            return False

        try:
            await self._send_json(client.websocket, {"type": "message", "content": message})
            return True
        except Exception as e:
            logger.error(f"Failed to send to {device_id}: {e}")
            return False

    def get_connected_devices(self) -> list[dict[str, Any]]:
        """Get list of connected devices."""
        return [client.to_dict() for client in self.authenticated_clients.values()]

    def is_device_connected(self, device_id: str) -> bool:
        """Check if device is connected."""
        return device_id in self.authenticated_clients

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running

    @property
    def connection_count(self) -> int:
        """Get number of connected clients."""
        return len(self.authenticated_clients)
