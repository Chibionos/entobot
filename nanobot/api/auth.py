"""Authentication API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from loguru import logger


router = APIRouter(prefix="/auth", tags=["Authentication"])


class PairRequest(BaseModel):
    """Device pairing request."""

    session_id: str
    temp_token: str
    device_info: dict[str, Any]


class PairResponse(BaseModel):
    """Device pairing response."""

    success: bool
    jwt_token: str | None = None
    device_id: str | None = None
    device_name: str | None = None
    message: str


class RefreshRequest(BaseModel):
    """Token refresh request."""

    jwt_token: str


class RefreshResponse(BaseModel):
    """Token refresh response."""

    success: bool
    jwt_token: str | None = None
    message: str


class DeviceInfo(BaseModel):
    """Device information."""

    device_id: str
    device_name: str
    authenticated_at: float


class DevicesResponse(BaseModel):
    """List of devices response."""

    devices: list[DeviceInfo]


def get_pairing_manager(request: Request):
    """Get pairing manager from app state."""
    return request.app.state.pairing_manager


def get_jwt_manager(request: Request):
    """Get JWT manager from app state."""
    return request.app.state.jwt_manager


@router.post("/pair", response_model=PairResponse)
async def pair_device(
    pair_req: PairRequest,
    pairing_manager=Depends(get_pairing_manager),
    jwt_manager=Depends(get_jwt_manager),
):
    """
    Pair a new device using QR code session.

    This endpoint is called by the mobile app after scanning the QR code.
    """
    try:
        # Validate pairing
        if not pairing_manager.validate_pairing(
            pair_req.session_id, pair_req.temp_token, pair_req.device_info
        ):
            logger.warning(f"Pairing validation failed for session: {pair_req.session_id}")
            return PairResponse(success=False, message="Invalid pairing credentials")

        # Generate device ID and JWT
        device_name = pair_req.device_info.get("device_name", "Unknown Device")
        device_id = f"device_{pair_req.session_id[:8]}"

        jwt_token = jwt_manager.generate_token(device_id, device_name)

        logger.info(f"Device paired successfully: {device_name} ({device_id})")

        return PairResponse(
            success=True,
            jwt_token=jwt_token,
            device_id=device_id,
            device_name=device_name,
            message="Pairing successful",
        )

    except Exception as e:
        logger.error(f"Error during pairing: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    refresh_req: RefreshRequest,
    jwt_manager=Depends(get_jwt_manager),
):
    """
    Refresh an existing JWT token.

    This extends the token expiry without requiring re-pairing.
    """
    try:
        new_token = jwt_manager.refresh_token(refresh_req.jwt_token)

        if not new_token:
            logger.warning("Token refresh failed: invalid or expired token")
            return RefreshResponse(success=False, message="Invalid or expired token")

        logger.info("Token refreshed successfully")

        return RefreshResponse(
            success=True, jwt_token=new_token, message="Token refreshed successfully"
        )

    except Exception as e:
        logger.error(f"Error during token refresh: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/devices", response_model=DevicesResponse)
async def list_devices(request: Request):
    """
    List all currently connected devices.

    Note: This requires authentication (JWT token in Authorization header).
    """
    # TODO: Add JWT authentication middleware
    # For now, return empty list as placeholder

    return DevicesResponse(devices=[])


@router.delete("/devices/{device_id}")
async def revoke_device(device_id: str, request: Request):
    """
    Revoke access for a specific device.

    This would typically disconnect the device and invalidate its token.
    """
    # TODO: Implement device revocation
    # This would require maintaining a list of revoked tokens or active sessions

    logger.info(f"Device revocation requested: {device_id}")

    return {"success": True, "message": f"Device {device_id} access revoked"}


@router.post("/pairing/create-session")
async def create_pairing_session(
    pairing_manager=Depends(get_pairing_manager),
):
    """
    Create a new pairing session on the relay.

    Called by the local CLI (nanobot pairing generate-qr --relay-url ...)
    to create a session on the relay, then generate the QR code locally.
    """
    try:
        session_id, qr_bytes = pairing_manager.create_pairing_session()
        session = pairing_manager.get_session(session_id)

        return {
            "session_id": session_id,
            "temp_token": session.temp_token,
            "websocket_url": pairing_manager.websocket_url,
            "expires_at": session.expires_at,
        }

    except Exception as e:
        logger.error(f"Error creating pairing session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create pairing session")
