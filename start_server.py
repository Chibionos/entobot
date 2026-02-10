#!/usr/bin/env python3
"""
Enterprise Entobot Server Startup Script

This script starts all components required for mobile app communication:
1. Configuration loading
2. Pairing manager initialization
3. JWT authentication manager
4. Secure WebSocket server (port 18791)
5. REST API server (port 18790)
6. Mobile channel integration
7. Message bus and agent loop

Usage:
    python start_server.py
    python start_server.py --verbose
    python start_server.py --ws-port 18791 --api-port 18790
"""

import asyncio
import signal
import sys
from pathlib import Path

import uvicorn
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from nanobot import __logo__, __version__
from nanobot.api.app import create_app
from nanobot.auth.jwt_manager import JWTManager
from nanobot.bus.queue import MessageBus
from nanobot.channels.manager import ChannelManager
from nanobot.channels.mobile import MobileChannel
from nanobot.config.loader import load_config
from nanobot.gateway.websocket import SecureWebSocketServer
from nanobot.pairing.manager import PairingManager
from nanobot.agent.loop import AgentLoop
from nanobot.session.manager import SessionManager

console = Console()


class EnterpriseServer:
    """Enterprise Entobot server managing all components."""

    def __init__(self, config, ws_port: int | None = None, api_port: int | None = None):
        """
        Initialize server with configuration.

        Args:
            config: Application configuration
            ws_port: Override WebSocket port
            api_port: Override REST API port
        """
        self.config = config
        self.ws_port = ws_port or config.channels.mobile.websocket_port
        self.api_port = api_port or config.gateway.port
        self.running = False

        # Core components
        self.bus: MessageBus | None = None
        self.jwt_manager: JWTManager | None = None
        self.pairing_manager: PairingManager | None = None
        self.websocket_server: SecureWebSocketServer | None = None
        self.mobile_channel: MobileChannel | None = None
        self.agent_loop: AgentLoop | None = None
        self.session_manager: SessionManager | None = None
        self.channel_manager: ChannelManager | None = None
        self.api_server_task: asyncio.Task | None = None

    def initialize_components(self):
        """Initialize all server components in correct order."""
        logger.info("Initializing Enterprise Entobot server components...")

        # 1. Message Bus
        self.bus = MessageBus()
        logger.info("✓ Message bus initialized")

        # 2. Session Manager
        self.session_manager = SessionManager(self.config.workspace_path)
        logger.info("✓ Session manager initialized")

        # 3. JWT Manager
        jwt_secret = self.config.auth.jwt_secret
        if not jwt_secret:
            logger.warning("JWT secret not set in config - generating temporary secret")
            import secrets
            jwt_secret = secrets.token_urlsafe(64)

        self.jwt_manager = JWTManager(
            secret=jwt_secret,
            algorithm=self.config.auth.jwt_algorithm,
            expiry_hours=self.config.auth.jwt_expiry_hours,
        )
        logger.info("✓ JWT manager initialized")

        # 4. Pairing Manager
        protocol = "wss" if self.config.channels.mobile.tls_enabled else "ws"
        websocket_url = f"{protocol}://localhost:{self.ws_port}"

        self.pairing_manager = PairingManager(
            websocket_url=websocket_url,
            session_expiry_minutes=self.config.auth.pairing_session_expiry_minutes,
        )
        logger.info(f"✓ Pairing manager initialized (URL: {websocket_url})")

        # 5. Secure WebSocket Server
        self.websocket_server = SecureWebSocketServer(
            host="0.0.0.0",
            port=self.ws_port,
            pairing_manager=self.pairing_manager,
            jwt_manager=self.jwt_manager,
            message_bus=self.bus,
            tls_enabled=self.config.channels.mobile.tls_enabled,
            tls_cert_path=Path(self.config.channels.mobile.tls_cert_path) if self.config.channels.mobile.tls_cert_path else None,
            tls_key_path=Path(self.config.channels.mobile.tls_key_path) if self.config.channels.mobile.tls_key_path else None,
            max_connections=self.config.channels.mobile.max_connections,
            heartbeat_interval=self.config.channels.mobile.heartbeat_interval,
        )
        logger.info(f"✓ WebSocket server initialized (port: {self.ws_port})")

        # 6. Mobile Channel
        self.mobile_channel = MobileChannel(
            config=self.config.channels.mobile,
            bus=self.bus,
            websocket_server=self.websocket_server,
        )
        logger.info("✓ Mobile channel initialized")

        # 7. Agent Loop
        from nanobot.providers.litellm_provider import LiteLLMProvider

        provider_config = self.config.get_provider()
        provider = LiteLLMProvider(
            api_key=provider_config.api_key if provider_config else None,
            api_base=self.config.get_api_base(),
            default_model=self.config.agents.defaults.model,
            extra_headers=provider_config.extra_headers if provider_config else None,
            provider_name=self.config.get_provider_name(),
        )

        self.agent_loop = AgentLoop(
            bus=self.bus,
            provider=provider,
            workspace=self.config.workspace_path,
            model=self.config.agents.defaults.model,
            max_iterations=self.config.agents.defaults.max_tool_iterations,
            brave_api_key=self.config.tools.web.search.api_key or None,
            exec_config=self.config.tools.exec,
            restrict_to_workspace=self.config.tools.restrict_to_workspace,
            session_manager=self.session_manager,
        )
        logger.info("✓ Agent loop initialized")

        # 8. Channel Manager (with mobile channel registered)
        self.channel_manager = ChannelManager(
            config=self.config,
            bus=self.bus,
            session_manager=self.session_manager,
        )
        # Manually register mobile channel
        self.channel_manager.channels["mobile"] = self.mobile_channel
        logger.info("✓ Channel manager initialized")

        logger.info("All components initialized successfully")

    async def start(self):
        """Start all server components."""
        if self.running:
            logger.warning("Server already running")
            return

        self.print_startup_banner()

        # Initialize components if not already done
        if not self.bus:
            self.initialize_components()

        # Start components in order
        logger.info("Starting server components...")

        # 1. Start pairing manager
        await self.pairing_manager.start()

        # 2. Start WebSocket server
        await self.websocket_server.start()

        # 3. Start mobile channel
        await self.mobile_channel.start()

        # 4. Start REST API server
        self.api_server_task = asyncio.create_task(self._run_api_server())

        # 5. Start agent loop and channel dispatcher
        self.running = True

        logger.info("✓ All components started successfully")
        self.print_server_info()

        # Run agent loop and channel manager
        try:
            await asyncio.gather(
                self.agent_loop.run(),
                self._keep_alive(),
            )
        except asyncio.CancelledError:
            logger.info("Server cancelled")

    async def _run_api_server(self):
        """Run FastAPI server."""
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

        logger.info(f"✓ REST API server starting on port {self.api_port}")

        try:
            await server.serve()
        except asyncio.CancelledError:
            logger.info("API server cancelled")

    async def _keep_alive(self):
        """Keep server alive and handle graceful shutdown."""
        while self.running:
            await asyncio.sleep(1)

    async def stop(self):
        """Stop all server components gracefully."""
        if not self.running:
            return

        logger.info("Stopping server components...")
        self.running = False

        # Stop components in reverse order
        if self.agent_loop:
            self.agent_loop.stop()

        if self.mobile_channel:
            await self.mobile_channel.stop()

        if self.websocket_server:
            await self.websocket_server.stop()

        if self.pairing_manager:
            await self.pairing_manager.stop()

        if self.api_server_task:
            self.api_server_task.cancel()
            try:
                await self.api_server_task
            except asyncio.CancelledError:
                pass

        if self.bus:
            self.bus.stop()

        logger.info("Server stopped gracefully")

    def print_startup_banner(self):
        """Print startup banner."""
        console.print()
        console.print(Panel(
            f"[bold cyan]{__logo__} Enterprise Entobot Server[/bold cyan]\n"
            f"Version: {__version__}\n\n"
            f"[green]Starting secure mobile communication platform...[/green]",
            border_style="cyan",
            padding=(1, 2),
        ))
        console.print()

    def print_server_info(self):
        """Print server information."""
        table = Table(title="Server Status", show_header=True, header_style="bold cyan")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")

        protocol_ws = "wss" if self.config.channels.mobile.tls_enabled else "ws"
        ws_url = f"{protocol_ws}://localhost:{self.ws_port}"

        table.add_row("WebSocket Server", "✓ Running", ws_url)
        table.add_row("REST API", "✓ Running", f"http://localhost:{self.api_port}/api")
        table.add_row("Mobile Channel", "✓ Active", f"{self.mobile_channel.connection_count} devices connected")
        table.add_row("Agent Loop", "✓ Running", self.config.agents.defaults.model)
        table.add_row("Message Bus", "✓ Running", f"In: {self.bus.inbound_size}, Out: {self.bus.outbound_size}")

        console.print(table)
        console.print()

        console.print("[bold]Next Steps:[/bold]")
        console.print(f"1. Generate QR code: [cyan]nanobot pairing generate-qr[/cyan]")
        console.print(f"2. Open mobile app and scan QR code")
        console.print(f"3. Start chatting with your AI assistant")
        console.print()
        console.print("[bold]API Endpoints:[/bold]")
        console.print(f"  • Health check: [cyan]http://localhost:{self.api_port}/api/health[/cyan]")
        console.print(f"  • API docs: [cyan]http://localhost:{self.api_port}/api/docs[/cyan]")
        console.print(f"  • Settings: [cyan]http://localhost:{self.api_port}/api/v1/settings/bot[/cyan]")
        console.print()
        console.print("[dim]Press Ctrl+C to stop the server[/dim]")
        console.print()


async def main(verbose: bool = False, ws_port: int | None = None, api_port: int | None = None):
    """
    Main entry point for server startup.

    Args:
        verbose: Enable verbose logging
        ws_port: Override WebSocket port
        api_port: Override API port
    """
    # Configure logging
    if verbose:
        logger.enable("nanobot")
    else:
        logger.disable("nanobot")

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        console.print(f"[red]Failed to load configuration: {e}[/red]")
        console.print("[yellow]Run 'nanobot onboard' to initialize configuration[/yellow]")
        sys.exit(1)

    # Validate configuration
    if not config.get_api_key():
        console.print("[red]No API key configured![/red]")
        console.print("[yellow]Add an API key to ~/.nanobot/config.json[/yellow]")
        console.print("Example: providers.openrouter.api_key = 'your-key-here'")
        sys.exit(1)

    # Create server
    server = EnterpriseServer(config, ws_port=ws_port, api_port=api_port)

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()

    def signal_handler():
        logger.info("Shutdown signal received")
        asyncio.create_task(server.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    # Start server
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        await server.stop()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start Enterprise Entobot server")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--ws-port", type=int, help="WebSocket server port (default: 18791)")
    parser.add_argument("--api-port", type=int, help="REST API server port (default: 18790)")

    args = parser.parse_args()

    asyncio.run(main(verbose=args.verbose, ws_port=args.ws_port, api_port=args.api_port))
