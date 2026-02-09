"""Mobile app channel for secure enterprise communication."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from loguru import logger

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel

if TYPE_CHECKING:
    from nanobot.gateway.websocket import SecureWebSocketServer


class MobileChannel(BaseChannel):
    """
    Mobile app channel that integrates with SecureWebSocketServer.

    This channel:
    - Receives messages from mobile app via WebSocket server
    - Forwards messages to the message bus for agent processing
    - Sends agent responses back to mobile devices
    - Manages multiple concurrent mobile connections
    """

    name = "mobile"

    def __init__(self, config, bus: MessageBus, websocket_server: SecureWebSocketServer):
        """
        Initialize mobile channel.

        Args:
            config: Mobile app configuration
            bus: Message bus for agent communication
            websocket_server: Secure WebSocket server instance
        """
        super().__init__(config, bus)
        self.websocket_server = websocket_server
        self._outbound_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the mobile channel."""
        if self._running:
            logger.warning("Mobile channel already running")
            return

        self._running = True

        # Subscribe to outbound messages for this channel
        self.bus.subscribe_outbound(self.name, self._handle_outbound)

        # Start outbound message handler
        self._outbound_task = asyncio.create_task(self._process_outbound())

        logger.info("Mobile channel started")

    async def stop(self) -> None:
        """Stop the mobile channel."""
        if not self._running:
            return

        self._running = False

        # Cancel outbound task
        if self._outbound_task:
            self._outbound_task.cancel()
            try:
                await self._outbound_task
            except asyncio.CancelledError:
                pass
            self._outbound_task = None

        logger.info("Mobile channel stopped")

    async def send(self, msg: OutboundMessage) -> None:
        """
        Send message to mobile device.

        Args:
            msg: Outbound message to send
        """
        # Extract device_id from chat_id
        device_id = msg.chat_id

        # Send via WebSocket server
        success = await self.websocket_server.send_to_device(device_id, msg.content)

        if success:
            logger.info(f"Sent message to device {device_id}: {msg.content[:50]}...")
        else:
            logger.warning(f"Failed to send message to device {device_id}")

    async def _handle_outbound(self, msg: OutboundMessage) -> None:
        """
        Handle outbound message from message bus.

        Args:
            msg: Outbound message from agent
        """
        await self.send(msg)

    async def _process_outbound(self) -> None:
        """
        Process outbound messages from the bus.

        This runs as a background task to handle messages.
        """
        logger.debug("Mobile channel outbound processor started")

        while self._running:
            try:
                # Wait for outbound messages
                await asyncio.sleep(0.1)  # Small sleep to prevent busy loop
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in mobile channel outbound processor: {e}")

        logger.debug("Mobile channel outbound processor stopped")

    def get_connected_devices(self) -> list[dict]:
        """
        Get list of connected mobile devices.

        Returns:
            List of device info dictionaries
        """
        return self.websocket_server.get_connected_devices()

    @property
    def connection_count(self) -> int:
        """Get number of connected mobile devices."""
        return self.websocket_server.connection_count
