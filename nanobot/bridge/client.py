"""
Bridge client — runs on the user's local machine.

Connects outbound to the relay server on Railway, receives mobile messages,
processes them with the local AgentLoop (LLM + tools), and sends responses
back through the relay to mobile devices.

All tool execution (shell, filesystem, web search) happens HERE on your machine.
"""

from __future__ import annotations

import asyncio
import json

import websockets
from loguru import logger
from rich.console import Console
from rich.panel import Panel

from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.agent.loop import AgentLoop
from nanobot.session.manager import SessionManager

console = Console()


class BridgeClient:
    """
    Bridge client that runs locally, connecting outbound to a relay server.

    The relay (on Railway) forwards mobile messages here. The local AgentLoop
    processes them using LLM providers and tools, then sends responses back
    through the relay to the mobile app.
    """

    def __init__(self, config, relay_url: str, bridge_token: str):
        self.config = config
        self.relay_url = relay_url
        self.bridge_token = bridge_token
        self.ws = None

        # Local components
        self.bus: MessageBus | None = None
        self.agent_loop: AgentLoop | None = None
        self.session_manager: SessionManager | None = None
        self._running = False

    def initialize_components(self) -> None:
        """Initialize local agent components — the full agent stack."""
        logger.info("Initializing local agent components...")

        self.bus = MessageBus()
        self.session_manager = SessionManager(self.config.workspace_path)

        # Build LLM provider
        provider = self._make_provider()

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

        # Subscribe to outbound messages — send them back through the bridge
        self.bus.subscribe_outbound("mobile", self._handle_outbound)

        logger.info("Local agent components initialized")

    async def start(self) -> None:
        """Connect to relay and start processing."""
        self._print_banner()
        self.initialize_components()
        self._running = True

        console.print(f"[cyan]Connecting to relay:[/cyan] {self.relay_url}")
        console.print()

        # Run agent loop, bus dispatcher, and bridge connection in parallel
        try:
            await asyncio.gather(
                self.agent_loop.run(),
                self.bus.dispatch_outbound(),
                self._connect_with_retry(),
            )
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()

    async def _connect_with_retry(self) -> None:
        """Connect to relay with automatic reconnection."""
        backoff = 5

        while self._running:
            try:
                async with websockets.connect(
                    self.relay_url,
                    ping_interval=30,
                    ping_timeout=60,
                    max_size=10_000_000,
                ) as ws:
                    self.ws = ws
                    backoff = 5  # reset on successful connection

                    # Authenticate with bridge token
                    await ws.send(json.dumps({
                        "type": "bridge_auth",
                        "bridge_token": self.bridge_token,
                    }))

                    # Wait for auth response
                    auth_raw = await ws.recv()
                    auth_response = json.loads(auth_raw)

                    if auth_response.get("type") == "bridge_auth_success":
                        console.print("[green]Connected to relay and authenticated[/green]")
                        console.print("[dim]Waiting for mobile messages...[/dim]")
                        console.print("[dim]Press Ctrl+C to stop[/dim]")
                        console.print()
                    else:
                        error = auth_response.get("message", "Unknown error")
                        console.print(f"[red]Bridge auth failed: {error}[/red]")
                        break

                    # Process messages from relay
                    async for message in ws:
                        await self._handle_relay_message(message)

            except websockets.exceptions.ConnectionClosed:
                logger.warning("Bridge connection closed")
            except ConnectionRefusedError:
                logger.warning(f"Relay not reachable at {self.relay_url}")
            except Exception as e:
                logger.error(f"Bridge connection error: {e}")

            self.ws = None

            if self._running:
                console.print(f"[yellow]Reconnecting in {backoff}s...[/yellow]")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)  # exponential backoff, max 30s

    async def _handle_relay_message(self, raw_message: str) -> None:
        """Handle a message from the relay."""
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            logger.error("Invalid JSON from relay")
            return

        msg_type = data.get("type")

        if msg_type == "bridge_message":
            # Forward to local agent via message bus
            inbound = InboundMessage(
                channel="mobile",
                sender_id=data.get("sender", "unknown"),
                chat_id=data.get("device_id", "unknown"),
                content=data.get("content", ""),
            )
            logger.info(f"Message from {inbound.sender_id}: {inbound.content[:50]}...")
            await self.bus.publish_inbound(inbound)

        elif msg_type == "bridge_ping":
            if self.ws:
                await self.ws.send(json.dumps({"type": "bridge_pong"}))

        elif msg_type == "error":
            logger.error(f"Relay error: {data.get('message', 'Unknown')}")

    async def _handle_outbound(self, msg: OutboundMessage) -> None:
        """Send agent response back through the bridge to the relay."""
        if not self.ws:
            logger.warning("Bridge not connected — dropping outbound message")
            return

        response = {
            "type": "bridge_response",
            "device_id": msg.chat_id,  # chat_id IS the device_id for mobile
            "content": msg.content,
        }
        try:
            await self.ws.send(json.dumps(response))
            logger.info(f"Response sent to device {msg.chat_id}: {msg.content[:50]}...")
        except Exception as e:
            logger.error(f"Failed to send bridge response: {e}")

    async def stop(self) -> None:
        """Stop the bridge client."""
        self._running = False
        if self.agent_loop:
            self.agent_loop.stop()
        if self.bus:
            self.bus.stop()
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
        logger.info("Bridge client stopped")

    def _make_provider(self):
        """Create LLM provider from config."""
        from nanobot.providers.litellm_provider import LiteLLMProvider

        provider_config = self.config.get_provider()
        if not provider_config or not provider_config.api_key:
            console.print("[red]Error: No LLM API key configured locally.[/red]")
            console.print("Add an API key to ~/.nanobot/config.json under providers section.")
            raise SystemExit(1)

        return LiteLLMProvider(
            api_key=provider_config.api_key,
            api_base=self.config.get_api_base(),
            default_model=self.config.agents.defaults.model,
            extra_headers=provider_config.extra_headers,
            provider_name=self.config.get_provider_name(),
        )

    def _print_banner(self) -> None:
        console.print()
        console.print(Panel(
            "[bold cyan]EntoBot Bridge Client[/bold cyan]\n"
            "[dim]Local agent — commands execute on YOUR machine[/dim]\n\n"
            f"[green]Model: {self.config.agents.defaults.model}[/green]\n"
            f"[green]Workspace: {self.config.workspace_path}[/green]",
            border_style="cyan",
            padding=(1, 2),
        ))
        console.print()
