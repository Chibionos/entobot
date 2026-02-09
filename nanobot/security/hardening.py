"""Security hardening components for enterprise deployment."""

from __future__ import annotations

import asyncio
import ipaddress
import json
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class RateLimitEntry:
    """Rate limit entry for a device or IP."""

    identifier: str
    request_count: int
    window_start: float
    blocked_until: float = 0.0

    def is_blocked(self) -> bool:
        """Check if currently blocked."""
        return time.time() < self.blocked_until


class RateLimiter:
    """
    Rate limiter to prevent abuse.

    Implements sliding window rate limiting per device_id.
    """

    def __init__(self, requests_per_minute: int = 60, block_duration_seconds: int = 300):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute
            block_duration_seconds: How long to block after exceeding limit
        """
        self.requests_per_minute = requests_per_minute
        self.block_duration_seconds = block_duration_seconds
        self.window_seconds = 60  # 1 minute sliding window

        self._entries: dict[str, RateLimitEntry] = {}
        self._cleanup_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start background cleanup task."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_old_entries())
            logger.info("Rate limiter started")

    async def stop(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Rate limiter stopped")

    async def _cleanup_old_entries(self) -> None:
        """Periodically remove old entries."""
        while True:
            try:
                await asyncio.sleep(60)  # Cleanup every minute
                now = time.time()
                to_remove = [
                    identifier
                    for identifier, entry in self._entries.items()
                    if now - entry.window_start > self.window_seconds * 2
                ]
                for identifier in to_remove:
                    del self._entries[identifier]
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in rate limit cleanup: {e}")

    def check_rate_limit(self, identifier: str) -> tuple[bool, str | None]:
        """
        Check if request should be allowed.

        Args:
            identifier: Unique identifier (device_id or IP address)

        Returns:
            Tuple of (allowed, error_message)
        """
        now = time.time()
        entry = self._entries.get(identifier)

        # Check if currently blocked
        if entry and entry.is_blocked():
            remaining = int(entry.blocked_until - now)
            return False, f"Rate limit exceeded. Blocked for {remaining} more seconds"

        # Create or reset entry if window expired
        if not entry or (now - entry.window_start) > self.window_seconds:
            entry = RateLimitEntry(
                identifier=identifier, request_count=1, window_start=now, blocked_until=0.0
            )
            self._entries[identifier] = entry
            return True, None

        # Increment request count
        entry.request_count += 1

        # Check if limit exceeded
        if entry.request_count > self.requests_per_minute:
            entry.blocked_until = now + self.block_duration_seconds
            logger.warning(f"Rate limit exceeded for {identifier}: {entry.request_count} requests")
            return False, f"Rate limit exceeded. Blocked for {self.block_duration_seconds} seconds"

        return True, None

    def reset_limit(self, identifier: str) -> None:
        """Reset rate limit for an identifier."""
        if identifier in self._entries:
            del self._entries[identifier]

    def get_stats(self, identifier: str) -> dict[str, Any]:
        """Get rate limit stats for an identifier."""
        entry = self._entries.get(identifier)
        if not entry:
            return {"request_count": 0, "blocked": False}

        return {
            "request_count": entry.request_count,
            "blocked": entry.is_blocked(),
            "blocked_until": entry.blocked_until if entry.is_blocked() else None,
        }


class AuditLogger:
    """
    Audit logger for security events.

    Logs all authentication, authorization, and security-relevant events.
    """

    def __init__(self, log_path: Path, max_file_size_mb: int = 100, max_files: int = 10):
        """
        Initialize audit logger.

        Args:
            log_path: Path to audit log file
            max_file_size_mb: Maximum log file size before rotation
            max_files: Maximum number of rotated log files to keep
        """
        self.log_path = Path(log_path).expanduser()
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.max_files = max_files

        # Create log directory
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Audit logger initialized: {self.log_path}")

    def _rotate_if_needed(self) -> None:
        """Rotate log file if it exceeds max size."""
        if not self.log_path.exists():
            return

        if self.log_path.stat().st_size > self.max_file_size:
            # Rotate existing files
            for i in range(self.max_files - 1, 0, -1):
                old_file = self.log_path.with_suffix(f".{i}")
                new_file = self.log_path.with_suffix(f".{i + 1}")
                if old_file.exists():
                    if new_file.exists():
                        new_file.unlink()
                    old_file.rename(new_file)

            # Rotate current file
            rotated = self.log_path.with_suffix(".1")
            if rotated.exists():
                rotated.unlink()
            self.log_path.rename(rotated)

            logger.info(f"Rotated audit log: {self.log_path}")

    def log(
        self,
        event_type: str,
        device_id: str | None = None,
        ip_address: str | None = None,
        details: dict[str, Any] | None = None,
        success: bool = True,
    ) -> None:
        """
        Log security event.

        Args:
            event_type: Type of event (e.g., "auth", "pairing", "rate_limit")
            device_id: Device ID if applicable
            ip_address: IP address if applicable
            details: Additional event details
            success: Whether the event was successful
        """
        self._rotate_if_needed()

        timestamp = datetime.utcnow().isoformat() + "Z"
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "device_id": device_id,
            "ip_address": ip_address,
            "success": success,
            "details": details or {},
        }

        try:
            with self.log_path.open("a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def log_authentication(
        self, device_id: str, ip_address: str, success: bool, method: str = "jwt"
    ) -> None:
        """Log authentication event."""
        self.log(
            "authentication",
            device_id=device_id,
            ip_address=ip_address,
            success=success,
            details={"method": method},
        )

    def log_pairing(
        self, session_id: str, device_id: str, ip_address: str, success: bool
    ) -> None:
        """Log device pairing event."""
        self.log(
            "pairing",
            device_id=device_id,
            ip_address=ip_address,
            success=success,
            details={"session_id": session_id},
        )

    def log_rate_limit(self, identifier: str, ip_address: str | None = None) -> None:
        """Log rate limit violation."""
        self.log(
            "rate_limit_exceeded",
            device_id=identifier if not ip_address else None,
            ip_address=ip_address,
            success=False,
        )

    def log_access_denied(
        self, reason: str, device_id: str | None = None, ip_address: str | None = None
    ) -> None:
        """Log access denied event."""
        self.log(
            "access_denied",
            device_id=device_id,
            ip_address=ip_address,
            success=False,
            details={"reason": reason},
        )

    def get_recent_events(self, count: int = 100) -> list[dict[str, Any]]:
        """
        Get recent audit events.

        Args:
            count: Number of events to retrieve

        Returns:
            List of recent events
        """
        if not self.log_path.exists():
            return []

        try:
            with self.log_path.open("r") as f:
                lines = f.readlines()
                recent_lines = lines[-count:]
                return [json.loads(line) for line in recent_lines]
        except Exception as e:
            logger.error(f"Failed to read audit log: {e}")
            return []


class SecurityValidator:
    """
    Security validator for input validation and IP whitelisting.
    """

    def __init__(self, ip_whitelist: list[str] | None = None, enable_whitelist: bool = False):
        """
        Initialize security validator.

        Args:
            ip_whitelist: List of allowed IP addresses/CIDR ranges
            enable_whitelist: Enable IP whitelist checking
        """
        self.enable_whitelist = enable_whitelist
        self.ip_whitelist = self._parse_ip_whitelist(ip_whitelist or [])

        logger.info(
            f"Security validator initialized (whitelist: {enable_whitelist}, "
            f"entries: {len(self.ip_whitelist)})"
        )

    def _parse_ip_whitelist(self, whitelist: list[str]) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
        """Parse IP whitelist into network objects."""
        networks = []
        for entry in whitelist:
            try:
                networks.append(ipaddress.ip_network(entry, strict=False))
            except ValueError as e:
                logger.warning(f"Invalid IP whitelist entry '{entry}': {e}")
        return networks

    def validate_ip_address(self, ip_address: str) -> tuple[bool, str | None]:
        """
        Validate IP address against whitelist.

        Args:
            ip_address: IP address to validate

        Returns:
            Tuple of (allowed, error_message)
        """
        if not self.enable_whitelist:
            return True, None

        if not self.ip_whitelist:
            # Whitelist enabled but empty - allow all (with warning)
            logger.warning("IP whitelist enabled but empty - allowing all IPs")
            return True, None

        try:
            ip = ipaddress.ip_address(ip_address)
            for network in self.ip_whitelist:
                if ip in network:
                    return True, None

            logger.warning(f"IP address not in whitelist: {ip_address}")
            return False, "IP address not allowed"

        except ValueError as e:
            logger.error(f"Invalid IP address: {ip_address} - {e}")
            return False, "Invalid IP address"

    def validate_device_info(self, device_info: dict[str, Any]) -> tuple[bool, str | None]:
        """
        Validate device information from pairing request.

        Args:
            device_info: Device information dictionary

        Returns:
            Tuple of (valid, error_message)
        """
        required_fields = ["device_name", "platform"]

        for field in required_fields:
            if field not in device_info:
                return False, f"Missing required field: {field}"

        # Validate device_name (alphanumeric, spaces, dashes, underscores only)
        device_name = device_info.get("device_name", "")
        if not re.match(r"^[a-zA-Z0-9\s\-_]{1,50}$", device_name):
            return False, "Invalid device_name format (max 50 chars, alphanumeric only)"

        # Validate platform
        platform = device_info.get("platform", "")
        valid_platforms = ["ios", "android", "web", "desktop"]
        if platform not in valid_platforms:
            return False, f"Invalid platform (must be one of: {', '.join(valid_platforms)})"

        return True, None

    def validate_message_content(self, content: str) -> tuple[bool, str | None]:
        """
        Validate message content for security issues.

        Args:
            content: Message content

        Returns:
            Tuple of (valid, error_message)
        """
        # Check length
        if len(content) > 100_000:  # 100KB max
            return False, "Message content too large (max 100KB)"

        if len(content) == 0:
            return False, "Message content empty"

        # Basic XSS/injection detection (can be enhanced)
        suspicious_patterns = [
            r"<script[^>]*>.*?</script>",  # Script tags
            r"javascript:",  # JavaScript protocol
            r"on\w+\s*=",  # Event handlers
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                logger.warning(f"Suspicious pattern detected in message: {pattern}")
                return False, "Message content contains suspicious patterns"

        return True, None

    def sanitize_input(self, text: str, max_length: int = 1000) -> str:
        """
        Sanitize user input.

        Args:
            text: Input text
            max_length: Maximum allowed length

        Returns:
            Sanitized text
        """
        # Truncate
        text = text[:max_length]

        # Remove null bytes
        text = text.replace("\x00", "")

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text
