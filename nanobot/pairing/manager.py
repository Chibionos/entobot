"""Pairing manager for QR code based device pairing."""

from __future__ import annotations

import asyncio
import secrets
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import qrcode
from loguru import logger


@dataclass
class PairingSession:
    """Represents a temporary pairing session."""

    session_id: str
    temp_token: str
    expires_at: float  # Unix timestamp
    device_info: dict[str, Any] | None = None
    websocket_url: str = ""

    def is_expired(self) -> bool:
        """Check if the pairing session has expired."""
        return time.time() > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "temp_token": self.temp_token,
            "expires_at": self.expires_at,
            "device_info": self.device_info,
            "websocket_url": self.websocket_url,
        }


class PairingManager:
    """
    Manages device pairing via QR codes.

    Flow:
    1. Server calls create_pairing_session() -> generates session_id, temp_token, QR code
    2. Mobile app scans QR code, gets session_id, websocket_url, temp_token
    3. Mobile app connects to WebSocket with pairing credentials
    4. Server validates pairing via validate_pairing() -> returns JWT token
    """

    def __init__(self, websocket_url: str, session_expiry_minutes: int = 5):
        """
        Initialize pairing manager.

        Args:
            websocket_url: WebSocket URL for mobile app to connect to
            session_expiry_minutes: How long pairing sessions remain valid
        """
        self.websocket_url = websocket_url
        self.session_expiry_minutes = session_expiry_minutes
        self.active_sessions: dict[str, PairingSession] = {}
        self._cleanup_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start background cleanup task."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
            logger.info("Pairing manager started")

    async def stop(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Pairing manager stopped")

    async def _cleanup_expired_sessions(self) -> None:
        """Periodically remove expired pairing sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Cleanup every minute
                expired = [
                    sid for sid, session in self.active_sessions.items() if session.is_expired()
                ]
                for sid in expired:
                    del self.active_sessions[sid]
                    logger.debug(f"Removed expired pairing session: {sid}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in pairing session cleanup: {e}")

    def create_pairing_session(self) -> tuple[str, bytes]:
        """
        Create a new pairing session and generate QR code.

        Returns:
            Tuple of (session_id, qr_code_png_bytes)
        """
        # Generate secure session ID and temporary token
        session_id = secrets.token_urlsafe(16)
        temp_token = secrets.token_urlsafe(32)

        # Calculate expiry time
        expires_at = time.time() + (self.session_expiry_minutes * 60)

        # Create session
        session = PairingSession(
            session_id=session_id,
            temp_token=temp_token,
            expires_at=expires_at,
            websocket_url=self.websocket_url,
        )
        self.active_sessions[session_id] = session

        # Generate QR code data
        qr_data = {
            "session_id": session_id,
            "websocket_url": self.websocket_url,
            "temp_token": temp_token,
            "timestamp": int(time.time()),
        }

        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(qr_data))
        qr.make(fit=True)

        # Generate PNG image
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_bytes = buffer.getvalue()

        logger.info(f"Created pairing session: {session_id} (expires in {self.session_expiry_minutes}m)")

        return session_id, qr_code_bytes

    def validate_pairing(
        self, session_id: str, temp_token: str, device_info: dict[str, Any]
    ) -> bool:
        """
        Validate a pairing request from mobile app.

        Args:
            session_id: Session ID from QR code
            temp_token: Temporary token from QR code
            device_info: Device information from mobile app

        Returns:
            True if pairing is valid and should proceed to JWT generation
        """
        session = self.active_sessions.get(session_id)

        if not session:
            logger.warning(f"Pairing validation failed: session not found ({session_id})")
            return False

        if session.is_expired():
            logger.warning(f"Pairing validation failed: session expired ({session_id})")
            del self.active_sessions[session_id]
            return False

        if session.temp_token != temp_token:
            logger.warning(f"Pairing validation failed: invalid token ({session_id})")
            return False

        # Store device info and mark session as used
        session.device_info = device_info

        logger.info(f"Pairing validated successfully: {session_id} - {device_info.get('device_name', 'unknown')}")

        # Remove session after successful pairing (one-time use)
        del self.active_sessions[session_id]

        return True

    def get_session(self, session_id: str) -> PairingSession | None:
        """Get a pairing session by ID."""
        return self.active_sessions.get(session_id)

    def generate_qr_ascii(self, session_id: str, temp_token: str) -> str:
        """
        Generate ASCII art QR code for terminal display.

        Args:
            session_id: Session ID
            temp_token: Temporary token

        Returns:
            ASCII art QR code as string
        """
        qr_data = {
            "session_id": session_id,
            "websocket_url": self.websocket_url,
            "temp_token": temp_token,
            "timestamp": int(time.time()),
        }

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=2,
        )
        qr.add_data(str(qr_data))
        qr.make(fit=True)

        # Generate ASCII art
        ascii_qr = qr.get_matrix()
        output = []
        for row in ascii_qr:
            line = ""
            for cell in row:
                line += "██" if cell else "  "
            output.append(line)

        return "\n".join(output)

    def save_qr_image(self, qr_code_bytes: bytes, output_path: Path) -> None:
        """
        Save QR code image to file.

        Args:
            qr_code_bytes: QR code PNG bytes
            output_path: Path to save the image
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(qr_code_bytes)
        logger.info(f"QR code saved to: {output_path}")

    def get_active_session_count(self) -> int:
        """Get number of active pairing sessions."""
        return len(self.active_sessions)
