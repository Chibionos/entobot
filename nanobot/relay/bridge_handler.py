"""Bridge connection handler — manages the WebSocket link to the local agent bridge."""

from __future__ import annotations

import asyncio
import json
import secrets
from typing import Any, TYPE_CHECKING

from loguru import logger
from websockets.server import WebSocketServerProtocol

if TYPE_CHECKING:
    from nanobot.gateway.websocket import SecureWebSocketServer


class BridgeConnectionHandler:
    """
    Manages the single bridge WebSocket connection on the relay side.

    The bridge client (running on the user's local machine) connects here
    and authenticates with a shared bridge_token. Once authenticated,
    mobile messages are forwarded to the bridge, and bridge responses
    are forwarded back to the correct mobile device.
    """

    def __init__(self, bridge_token: str, websocket_server: SecureWebSocketServer):
        self.bridge_token = bridge_token
        self.websocket_server = websocket_server
        self.bridge_ws: WebSocketServerProtocol | None = None
        self._authenticated = False
        self._ping_task: asyncio.Task | None = None

    async def handle_connection(self, websocket: WebSocketServerProtocol) -> None:
        """Handle incoming bridge WebSocket connection."""
        if self.bridge_ws is not None:
            logger.warning("Bridge connection rejected — another bridge is already connected")
            await self._send_json(websocket, {
                "type": "error",
                "message": "Another bridge is already connected",
            })
            await websocket.close(4000, "Bridge already connected")
            return

        logger.info("Bridge client connecting...")

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    await self._send_json(websocket, {"type": "error", "message": "Invalid JSON"})
                    continue

                msg_type = data.get("type")

                if msg_type == "bridge_auth":
                    await self._handle_auth(websocket, data)
                elif msg_type == "bridge_response":
                    await self._handle_response(data)
                elif msg_type == "bridge_pong":
                    pass  # keepalive ack
                else:
                    await self._send_json(websocket, {
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}",
                    })

        except Exception as e:
            logger.error(f"Bridge connection error: {e}")
        finally:
            was_authenticated = self._authenticated
            self.bridge_ws = None
            self._authenticated = False
            if self._ping_task:
                self._ping_task.cancel()
                self._ping_task = None
            if was_authenticated:
                logger.warning("Bridge client disconnected")

    async def _handle_auth(self, websocket: WebSocketServerProtocol, data: dict[str, Any]) -> None:
        """Validate bridge token using constant-time comparison."""
        token = data.get("bridge_token", "")
        if secrets.compare_digest(token, self.bridge_token):
            self.bridge_ws = websocket
            self._authenticated = True
            await self._send_json(websocket, {"type": "bridge_auth_success"})
            self._ping_task = asyncio.create_task(self._ping_loop())
            logger.info("Bridge client authenticated successfully")
        else:
            logger.warning("Bridge authentication failed — invalid token")
            await self._send_json(websocket, {"type": "error", "message": "Invalid bridge token"})
            await websocket.close(4001, "Auth failed")

    async def forward_to_bridge(
        self, device_id: str, sender: str, content: str, chat_id: str
    ) -> None:
        """Forward a mobile message to the bridge client."""
        if not self.is_connected:
            logger.warning("No bridge connected — sending offline message to device")
            await self.websocket_server.send_to_device(
                device_id,
                "Agent is currently offline. The local bridge is not connected. Please try again later.",
            )
            return

        msg = {
            "type": "bridge_message",
            "device_id": device_id,
            "sender": sender,
            "content": content,
            "chat_id": chat_id,
        }
        try:
            await self.bridge_ws.send(json.dumps(msg))
        except Exception as e:
            logger.error(f"Failed to forward message to bridge: {e}")

    async def _handle_response(self, data: dict[str, Any]) -> None:
        """Forward bridge response back to the mobile device."""
        device_id = data.get("device_id")
        content = data.get("content")
        if device_id and content:
            success = await self.websocket_server.send_to_device(device_id, content)
            if not success:
                logger.warning(f"Failed to deliver response to device {device_id} — not connected")

    async def _ping_loop(self) -> None:
        """Send periodic pings to keep the bridge connection alive."""
        try:
            while self._authenticated and self.bridge_ws:
                await asyncio.sleep(25)
                if self.bridge_ws:
                    await self._send_json(self.bridge_ws, {"type": "bridge_ping"})
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Bridge ping error: {e}")

    async def _send_json(self, websocket: WebSocketServerProtocol, data: dict[str, Any]) -> None:
        """Send JSON message to a WebSocket."""
        try:
            await websocket.send(json.dumps(data))
        except Exception as e:
            logger.error(f"Failed to send to bridge: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if a bridge client is connected and authenticated."""
        return self.bridge_ws is not None and self._authenticated
