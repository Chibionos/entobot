"""JWT token manager for secure authentication."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from typing import Any

import jwt
from loguru import logger


@dataclass
class DeviceCredentials:
    """Credentials for an authenticated device."""

    device_id: str
    device_name: str
    issued_at: float
    expires_at: float

    def is_expired(self) -> bool:
        """Check if credentials are expired."""
        return time.time() > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
        }


class JWTManager:
    """
    Manages JWT tokens for device authentication.

    This class handles:
    - Token generation after successful pairing
    - Token validation for authenticated requests
    - Token refresh for long-lived sessions
    """

    def __init__(self, secret: str, algorithm: str = "HS256", expiry_hours: int = 24 * 30):
        """
        Initialize JWT manager.

        Args:
            secret: Secret key for signing tokens (must be strong in production)
            algorithm: JWT signing algorithm (default: HS256)
            expiry_hours: Token expiry time in hours (default: 30 days)
        """
        if not secret or len(secret) < 32:
            logger.warning("JWT secret is weak or missing - generating random secret for this session")
            secret = secrets.token_urlsafe(64)

        self.secret = secret
        self.algorithm = algorithm
        self.expiry_hours = expiry_hours

    def generate_token(self, device_id: str, device_name: str, **extra_claims: Any) -> str:
        """
        Generate a new JWT token for a device.

        Args:
            device_id: Unique device identifier
            device_name: Human-readable device name
            **extra_claims: Additional claims to include in token

        Returns:
            JWT token as string
        """
        now = time.time()
        expires_at = now + (self.expiry_hours * 3600)

        payload = {
            "device_id": device_id,
            "device_name": device_name,
            "iat": int(now),  # Issued at
            "exp": int(expires_at),  # Expiration
            "type": "access",
            **extra_claims,
        }

        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        logger.info(f"Generated JWT token for device: {device_name} ({device_id})")

        return token

    def validate_token(self, token: str) -> str | None:
        """
        Validate a JWT token and extract device_id.

        Args:
            token: JWT token to validate

        Returns:
            device_id if valid, None if invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])

            # Verify required fields
            device_id = payload.get("device_id")
            if not device_id:
                logger.warning("JWT token missing device_id")
                return None

            # Check token type
            if payload.get("type") != "access":
                logger.warning("Invalid JWT token type")
                return None

            logger.debug(f"Validated JWT token for device: {device_id}")
            return device_id

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None

    def get_token_payload(self, token: str) -> dict[str, Any] | None:
        """
        Get full token payload without validation (for inspection).

        Args:
            token: JWT token

        Returns:
            Token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token, self.secret, algorithms=[self.algorithm], options={"verify_signature": True}
            )
            return payload
        except Exception as e:
            logger.warning(f"Failed to decode token: {e}")
            return None

    def refresh_token(self, old_token: str) -> str | None:
        """
        Generate a new token based on an existing valid token.

        Args:
            old_token: Existing JWT token

        Returns:
            New JWT token or None if old token is invalid
        """
        payload = self.get_token_payload(old_token)
        if not payload:
            return None

        device_id = payload.get("device_id")
        device_name = payload.get("device_name")

        if not device_id or not device_name:
            logger.warning("Cannot refresh token: missing device information")
            return None

        # Generate new token with same device info
        extra_claims = {k: v for k, v in payload.items() if k not in ["device_id", "device_name", "iat", "exp", "type"]}

        new_token = self.generate_token(device_id, device_name, **extra_claims)
        logger.info(f"Refreshed token for device: {device_name} ({device_id})")

        return new_token

    def extract_device_credentials(self, token: str) -> DeviceCredentials | None:
        """
        Extract device credentials from a valid token.

        Args:
            token: JWT token

        Returns:
            DeviceCredentials or None if invalid
        """
        payload = self.get_token_payload(token)
        if not payload:
            return None

        try:
            return DeviceCredentials(
                device_id=payload["device_id"],
                device_name=payload["device_name"],
                issued_at=float(payload.get("iat", 0)),
                expires_at=float(payload.get("exp", 0)),
            )
        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to extract credentials from token: {e}")
            return None

    def get_expiry_time(self, token: str) -> float | None:
        """
        Get token expiry timestamp.

        Args:
            token: JWT token

        Returns:
            Unix timestamp of expiry or None
        """
        payload = self.get_token_payload(token)
        if payload:
            return float(payload.get("exp", 0))
        return None

    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired without full validation.

        Args:
            token: JWT token

        Returns:
            True if expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                options={"verify_signature": False, "verify_exp": False},
            )
            exp = payload.get("exp", 0)
            return time.time() > exp
        except Exception:
            return True
