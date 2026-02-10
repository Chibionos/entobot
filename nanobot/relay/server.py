"""
Relay server for Railway deployment.

A thin message forwarder — NO agent loop, NO LLM keys, NO tool execution.
Accepts mobile WebSocket connections and forwards messages to the local
bridge client, which runs the agent loop on the user's machine.

Required env vars:
    BRIDGE_TOKEN  — shared secret for bridge authentication
    JWT_SECRET    — secret for mobile JWT tokens

Optional env vars:
    RELAY_PUBLIC_URL — public WebSocket URL (for QR codes)
    PORT             — Railway-assigned port
"""

from __future__ import annotations

import asyncio
import os
import signal
from pathlib import Path

import uvicorn
import websockets
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from nanobot.api.app import create_app
from nanobot.auth.jwt_manager import JWTManager
from nanobot.gateway.websocket import SecureWebSocketServer
from nanobot.pairing.manager import PairingManager
from nanobot.relay.bridge_handler import BridgeConnectionHandler

console = Console()


class RelayServer:
    """
    Relay server — deployed to Railway as a public-facing message forwarder.

    Components:
    - SecureWebSocketServer: handles mobile auth/pairing/messaging
    - BridgeConnectionHandler: manages the bridge connection from local agent
    - PairingManager + JWTManager: mobile authentication
    - REST API: pairing endpoints

    Does NOT contain: AgentLoop, MessageBus, LLM providers, tools.
    """

    def __init__(
        self,
        config,
        bridge_token: str,
        ws_port: int | None = None,
        api_port: int | None = None,
        public_url: str | None = None,
    ):
        self.config = config
        self.bridge_token = bridge_token
        self.ws_port = ws_port or int(os.environ.get("PORT", config.channels.mobile.websocket_port))
        self.api_port = api_port or config.gateway.port
        self.public_url = public_url or config.relay.public_url or ""
        self._running = False

        # Components (initialized in initialize_components)
        self.jwt_manager: JWTManager | None = None
        self.pairing_manager: PairingManager | None = None
        self.websocket_server: SecureWebSocketServer | None = None
        self.bridge_handler: BridgeConnectionHandler | None = None

    def initialize_components(self) -> None:
        """Initialize relay components — no agent loop or LLM providers."""
        logger.info("Initializing relay server components...")

        # 1. JWT Manager
        jwt_secret = self.config.auth.jwt_secret or os.environ.get("JWT_SECRET", "")
        if not jwt_secret:
            import secrets as _secrets
            jwt_secret = _secrets.token_urlsafe(64)
            logger.warning("JWT_SECRET not set — using temporary secret (set JWT_SECRET env var)")

        self.jwt_manager = JWTManager(
            secret=jwt_secret,
            algorithm=self.config.auth.jwt_algorithm,
            expiry_hours=self.config.auth.jwt_expiry_hours,
        )
        logger.info("  JWT manager initialized")

        # 2. Pairing Manager — uses relay's public URL for QR codes
        websocket_url = self.public_url or f"ws://localhost:{self.ws_port}"
        self.pairing_manager = PairingManager(
            websocket_url=websocket_url,
            session_expiry_minutes=self.config.auth.pairing_session_expiry_minutes,
        )
        logger.info(f"  Pairing manager initialized (URL: {websocket_url})")

        # 3. WebSocket Server — with on_client_message callback (relay mode)
        # The callback forwards messages to the bridge instead of a local bus
        self.websocket_server = SecureWebSocketServer(
            host="0.0.0.0",
            port=self.ws_port,
            pairing_manager=self.pairing_manager,
            jwt_manager=self.jwt_manager,
            message_bus=None,  # No local message bus in relay mode
            tls_enabled=self.config.channels.mobile.tls_enabled,
            tls_cert_path=Path(self.config.channels.mobile.tls_cert_path) if self.config.channels.mobile.tls_cert_path else None,
            tls_key_path=Path(self.config.channels.mobile.tls_key_path) if self.config.channels.mobile.tls_key_path else None,
            max_connections=self.config.channels.mobile.max_connections,
            heartbeat_interval=self.config.channels.mobile.heartbeat_interval,
        )
        logger.info(f"  WebSocket server initialized (port: {self.ws_port})")

        # 4. Bridge Handler — manages the connection from the local agent
        self.bridge_handler = BridgeConnectionHandler(
            bridge_token=self.bridge_token,
            websocket_server=self.websocket_server,
        )
        logger.info("  Bridge handler initialized")

        # Wire up: when a mobile message arrives, forward to bridge
        self.websocket_server.on_client_message = self.bridge_handler.forward_to_bridge

        logger.info("All relay components initialized")

    async def run(self) -> None:
        """Start the relay server."""
        self._print_banner()
        self.initialize_components()
        self._running = True

        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))

        # Start a single WebSocket server with path-based routing
        server = await websockets.serve(
            self._route_connection,
            "0.0.0.0",
            self.ws_port,
            max_size=10_000_000,
            ping_interval=30,
            ping_timeout=60,
        )
        self.websocket_server._server = server
        self.websocket_server._running = True

        protocol = "wss" if self.config.channels.mobile.tls_enabled else "ws"
        logger.info(f"Relay WebSocket server started on {protocol}://0.0.0.0:{self.ws_port}")

        # Start pairing manager cleanup
        await self.pairing_manager.start()

        self._print_status()

        # Run REST API and keepalive
        try:
            await asyncio.gather(
                self._run_api_server(),
                self._keep_alive(),
            )
        except asyncio.CancelledError:
            pass
        finally:
            server.close()
            await server.wait_closed()

    async def _route_connection(self, websocket) -> None:
        """Route WebSocket connections by path."""
        # websockets v12+: path is on request object
        path = getattr(getattr(websocket, "request", None), "path", "/")
        # websockets <12 fallback
        if not path:
            path = getattr(websocket, "path", "/")

        if path == "/bridge":
            await self.bridge_handler.handle_connection(websocket)
        else:
            # Mobile app connections (/, /ws, or any other path)
            await self.websocket_server._handle_connection(websocket, path)

    async def _run_api_server(self) -> None:
        """Run FastAPI REST API for pairing and settings."""
        app = create_app(
            config=self.config,
            pairing_manager=self.pairing_manager,
            jwt_manager=self.jwt_manager,
        )

        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=self.api_port,
            log_level="info",
        )
        server = uvicorn.Server(config)

        logger.info(f"REST API server starting on port {self.api_port}")

        try:
            await server.serve()
        except asyncio.CancelledError:
            pass

    async def _keep_alive(self) -> None:
        """Keep server alive."""
        while self._running:
            await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop relay server gracefully."""
        if not self._running:
            return
        self._running = False
        logger.info("Relay server stopping...")

        if self.pairing_manager:
            await self.pairing_manager.stop()
        if self.websocket_server:
            await self.websocket_server.stop()

        logger.info("Relay server stopped")

    def _print_banner(self) -> None:
        console.print()
        console.print(Panel(
            "[bold cyan]EntoBot Relay Server[/bold cyan]\n"
            "[dim]Thin message forwarder — no LLM keys, no agent loop[/dim]\n\n"
            "[green]Mobile apps connect here, messages forwarded to your local agent[/green]",
            border_style="cyan",
            padding=(1, 2),
        ))
        console.print()

    def _print_status(self) -> None:
        table = Table(title="Relay Status", show_header=True, header_style="bold cyan")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")

        table.add_row("WebSocket", "Running", f"ws://0.0.0.0:{self.ws_port}")
        table.add_row("REST API", "Running", f"http://0.0.0.0:{self.api_port}/api")
        table.add_row("Bridge", "Waiting", "No bridge connected yet")
        table.add_row("Public URL", "Set" if self.public_url else "Not set", self.public_url or "—")

        console.print(table)
        console.print()
        console.print("[bold]Waiting for bridge client to connect...[/bold]")
        console.print("[dim]Start the bridge on your local machine: nanobot bridge --relay-url <this-url>[/dim]")
        console.print()
