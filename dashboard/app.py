"""Entobot Enterprise Dashboard - FastAPI Server"""

from __future__ import annotations

import asyncio
import base64
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn

# Import from main project
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from nanobot.pairing.manager import PairingManager
from nanobot.gateway.websocket import SecureWebSocketServer

app = FastAPI(title="Entobot Enterprise Dashboard")

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
DASHBOARD_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(DASHBOARD_DIR / "templates"))

# Global state (in production, use proper state management)
class DashboardState:
    """Dashboard global state"""
    def __init__(self):
        self.start_time = time.time()
        self.pairing_manager: PairingManager | None = None
        self.websocket_server: SecureWebSocketServer | None = None
        self.activity_log: list[dict[str, Any]] = []
        self.audit_log: list[dict[str, Any]] = []
        self.message_count = 0
        self.dashboard_clients: list[WebSocket] = []
        self.demo_mode = True  # Enable demo mode by default

    def add_activity(self, activity_type: str, message: str, details: dict[str, Any] | None = None):
        """Add activity to log"""
        activity = {
            "timestamp": datetime.now().isoformat(),
            "type": activity_type,
            "message": message,
            "details": details or {}
        }
        self.activity_log.insert(0, activity)  # Most recent first
        if len(self.activity_log) > 100:
            self.activity_log = self.activity_log[:100]

    def add_audit_event(self, event_type: str, message: str, severity: str = "info"):
        """Add audit event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
            "severity": severity
        }
        self.audit_log.insert(0, event)
        if len(self.audit_log) > 100:
            self.audit_log = self.audit_log[:100]

    def get_uptime(self) -> dict[str, int]:
        """Get uptime in hours, minutes, seconds"""
        uptime_seconds = int(time.time() - self.start_time)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        return {"hours": hours, "minutes": minutes, "seconds": seconds}

state = DashboardState()

# Initialize managers
def init_managers():
    """Initialize pairing and websocket managers"""
    if not state.pairing_manager:
        state.pairing_manager = PairingManager(
            websocket_url="ws://localhost:8765",
            session_expiry_minutes=5
        )
        logger.info("Pairing manager initialized for dashboard")

    # Add initial demo data
    if state.demo_mode:
        state.add_activity("system", "Dashboard initialized", {"mode": "demo"})
        state.add_audit_event("system_start", "Dashboard started in demo mode", "info")

init_managers()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve main dashboard page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/dashboard/status")
async def get_status():
    """Get dashboard status metrics"""

    # If demo mode, return mock data
    if state.demo_mode:
        import random
        return {
            "status": "online",
            "devices": random.randint(2, 5),
            "sessions": random.randint(1, 3),
            "messages": state.message_count + random.randint(40, 60),
            "uptime": state.get_uptime(),
            "demo_mode": True
        }

    # Real data from WebSocket server
    devices = 0
    if state.websocket_server:
        devices = state.websocket_server.connection_count

    return {
        "status": "online" if state.websocket_server and state.websocket_server.is_running else "offline",
        "devices": devices,
        "sessions": len(state.activity_log),
        "messages": state.message_count,
        "uptime": state.get_uptime(),
        "demo_mode": False
    }


@app.get("/api/dashboard/devices")
async def get_devices():
    """Get connected devices"""

    if state.demo_mode:
        # Mock devices
        return [
            {
                "device_id": "device_abc123",
                "name": "iPhone 13 Pro",
                "platform": "iOS 17.2",
                "connected_at": (datetime.now()).isoformat(),
                "last_seen": datetime.now().isoformat(),
                "status": "active"
            },
            {
                "device_id": "device_xyz789",
                "name": "Pixel 8",
                "platform": "Android 14",
                "connected_at": (datetime.now()).isoformat(),
                "last_seen": datetime.now().isoformat(),
                "status": "active"
            }
        ]

    if state.websocket_server:
        devices = state.websocket_server.get_connected_devices()
        return devices

    return []


@app.get("/api/dashboard/activity")
async def get_activity():
    """Get recent activity feed"""

    # Add some demo activity if in demo mode
    if state.demo_mode and len(state.activity_log) < 10:
        demo_activities = [
            ("message_received", "New message from iPhone 13 Pro", {"device": "iPhone 13 Pro"}),
            ("device_connected", "Pixel 8 connected successfully", {"device_id": "device_xyz789"}),
            ("message_sent", "Response sent to iPhone 13 Pro", {"length": 142}),
            ("config_updated", "AI model changed to gpt-4o", {"model": "gpt-4o"}),
            ("message_received", "Message from Pixel 8", {"device": "Pixel 8"}),
        ]
        for activity_type, msg, details in demo_activities:
            if len(state.activity_log) < 20:
                state.add_activity(activity_type, msg, details)

    return state.activity_log[:50]


@app.get("/api/dashboard/audit")
async def get_audit_log():
    """Get security audit log"""

    # Add demo audit events
    if state.demo_mode and len(state.audit_log) < 5:
        demo_audits = [
            ("auth_success", "Device authenticated successfully: device_abc123", "info"),
            ("config_change", "Configuration updated: model=gpt-4o", "info"),
            ("rate_limit", "Rate limit applied to device_xyz789", "warning"),
            ("auth_success", "Device authenticated successfully: device_xyz789", "info"),
        ]
        for event_type, msg, severity in demo_audits:
            if len(state.audit_log) < 20:
                state.add_audit_event(event_type, msg, severity)

    return state.audit_log[:50]


@app.post("/api/dashboard/generate-qr")
async def generate_qr():
    """Generate QR code for device pairing"""

    if not state.pairing_manager:
        return {"error": "Pairing manager not initialized"}

    try:
        # Create pairing session
        session_id, qr_bytes = state.pairing_manager.create_pairing_session()

        # Convert to base64
        qr_base64 = base64.b64encode(qr_bytes).decode('utf-8')

        # Get session details
        session = state.pairing_manager.get_session(session_id)

        # Log activity
        state.add_activity("qr_generated", f"QR code generated for pairing", {
            "session_id": session_id,
            "expires_in_minutes": state.pairing_manager.session_expiry_minutes
        })
        state.add_audit_event("qr_generated", f"Pairing QR code generated: {session_id}", "info")

        # Broadcast to dashboard clients
        await broadcast_dashboard_update({
            "type": "qr_generated",
            "session_id": session_id
        })

        return {
            "success": True,
            "session_id": session_id,
            "qr_code": f"data:image/png;base64,{qr_base64}",
            "websocket_url": session.websocket_url if session else "ws://localhost:8765",
            "expires_in_minutes": state.pairing_manager.session_expiry_minutes,
            "valid_until": datetime.fromtimestamp(session.expires_at).isoformat() if session else None
        }

    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        return {"error": str(e)}


@app.post("/api/dashboard/demo-mode")
async def toggle_demo_mode(enabled: bool):
    """Toggle demo mode"""
    state.demo_mode = enabled
    logger.info(f"Demo mode {'enabled' if enabled else 'disabled'}")
    return {"demo_mode": enabled}


@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket.accept()
    state.dashboard_clients.append(websocket)

    logger.info("Dashboard client connected via WebSocket")

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "Dashboard WebSocket connected"
        })

        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_json()

            # Handle ping
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info("Dashboard client disconnected")
        state.dashboard_clients.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in state.dashboard_clients:
            state.dashboard_clients.remove(websocket)


async def broadcast_dashboard_update(update: dict[str, Any]):
    """Broadcast update to all connected dashboard clients"""
    for client in state.dashboard_clients:
        try:
            await client.send_json(update)
        except Exception as e:
            logger.error(f"Error broadcasting to dashboard client: {e}")


# Background task to simulate activity in demo mode
async def demo_activity_generator():
    """Generate demo activity for impressive demo"""
    while True:
        await asyncio.sleep(10)  # Every 10 seconds

        if state.demo_mode and len(state.dashboard_clients) > 0:
            import random

            activities = [
                ("message_received", "Received: 'What's the weather today?'", {"device": "iPhone 13 Pro"}),
                ("message_sent", "Sent: 'The weather is sunny and 72°F'", {"device": "iPhone 13 Pro"}),
                ("message_received", "Received: 'Remind me to call John'", {"device": "Pixel 8"}),
                ("message_sent", "Sent: 'Reminder set for 3:00 PM'", {"device": "Pixel 8"}),
            ]

            activity_type, msg, details = random.choice(activities)
            state.add_activity(activity_type, msg, details)
            state.message_count += 1

            # Broadcast update
            await broadcast_dashboard_update({
                "type": "activity_update",
                "activity": state.activity_log[0]
            })


@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(demo_activity_generator())
    logger.info("Dashboard startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Close all dashboard WebSocket connections
    for client in state.dashboard_clients:
        try:
            await client.close()
        except:
            pass

    logger.info("Dashboard shutdown complete")


def run_dashboard(host: str = "0.0.0.0", port: int = 8080):
    """Run the dashboard server"""
    logger.info(f"Starting Entobot Enterprise Dashboard on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_dashboard()
