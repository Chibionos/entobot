"""Settings API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from loguru import logger


router = APIRouter(prefix="/settings", tags=["Settings"])


class BotSettings(BaseModel):
    """Bot configuration settings."""

    model: str
    max_tokens: int
    temperature: float
    workspace: str


class BotSettingsResponse(BaseModel):
    """Bot settings response."""

    settings: BotSettings


class UpdateBotSettingsRequest(BaseModel):
    """Update bot settings request."""

    model: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None


class ProviderSettings(BaseModel):
    """Provider configuration settings."""

    name: str
    api_key_set: bool
    api_base: str | None = None


class ProvidersResponse(BaseModel):
    """List of providers response."""

    providers: list[ProviderSettings]


class UpdateProviderRequest(BaseModel):
    """Update provider settings request."""

    api_key: str | None = None
    api_base: str | None = None


def get_config(request: Request):
    """Get config from app state."""
    return request.app.state.config


@router.get("/bot", response_model=BotSettingsResponse)
async def get_bot_settings(config=Depends(get_config)):
    """
    Get current bot settings.

    Returns model, max_tokens, temperature, and workspace path.
    """
    settings = BotSettings(
        model=config.agents.defaults.model,
        max_tokens=config.agents.defaults.max_tokens,
        temperature=config.agents.defaults.temperature,
        workspace=str(config.workspace_path),
    )

    return BotSettingsResponse(settings=settings)


@router.put("/bot")
async def update_bot_settings(
    update_req: UpdateBotSettingsRequest,
    config=Depends(get_config),
):
    """
    Update bot settings.

    Note: This updates runtime settings only. To persist, changes need to be
    written back to config file.
    """
    try:
        if update_req.model is not None:
            config.agents.defaults.model = update_req.model
            logger.info(f"Updated model to: {update_req.model}")

        if update_req.max_tokens is not None:
            config.agents.defaults.max_tokens = update_req.max_tokens
            logger.info(f"Updated max_tokens to: {update_req.max_tokens}")

        if update_req.temperature is not None:
            if not 0.0 <= update_req.temperature <= 2.0:
                raise HTTPException(status_code=400, detail="Temperature must be between 0 and 2")
            config.agents.defaults.temperature = update_req.temperature
            logger.info(f"Updated temperature to: {update_req.temperature}")

        # TODO: Persist changes to config file
        # from nanobot.config.loader import save_config
        # save_config(config)

        return {"success": True, "message": "Bot settings updated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bot settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/providers", response_model=ProvidersResponse)
async def get_providers(config=Depends(get_config)):
    """
    Get list of configured providers.

    Returns provider name, whether API key is set, and API base URL.
    """
    from nanobot.providers.registry import PROVIDERS

    providers = []
    for spec in PROVIDERS:
        p = getattr(config.providers, spec.name, None)
        if p:
            providers.append(
                ProviderSettings(
                    name=spec.name,
                    api_key_set=bool(p.api_key),
                    api_base=p.api_base,
                )
            )

    return ProvidersResponse(providers=providers)


@router.put("/providers/{provider_name}")
async def update_provider(
    provider_name: str,
    update_req: UpdateProviderRequest,
    config=Depends(get_config),
):
    """
    Update provider settings.

    Allows updating API key and base URL for a specific provider.
    """
    try:
        # Get provider config
        provider_config = getattr(config.providers, provider_name, None)
        if not provider_config:
            raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

        if update_req.api_key is not None:
            provider_config.api_key = update_req.api_key
            logger.info(f"Updated API key for provider: {provider_name}")

        if update_req.api_base is not None:
            provider_config.api_base = update_req.api_base
            logger.info(f"Updated API base for provider: {provider_name} to {update_req.api_base}")

        # TODO: Persist changes to config file
        # from nanobot.config.loader import save_config
        # save_config(config)

        return {"success": True, "message": f"Provider '{provider_name}' updated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating provider: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/enterprise")
async def get_enterprise_settings(config=Depends(get_config)):
    """
    Get enterprise configuration settings.

    Returns organization info, rate limiting, audit logging, etc.
    """
    return {
        "organization_name": config.enterprise.organization_name,
        "rate_limit_enabled": config.enterprise.rate_limit_enabled,
        "rate_limit_requests_per_minute": config.enterprise.rate_limit_requests_per_minute,
        "audit_log_enabled": config.enterprise.audit_log_enabled,
        "ip_whitelist_enabled": config.enterprise.ip_whitelist_enabled,
    }


@router.get("/mobile")
async def get_mobile_settings(config=Depends(get_config)):
    """
    Get mobile app configuration settings.

    Returns WebSocket settings, TLS config, connection limits, etc.
    """
    return {
        "enabled": config.channels.mobile.enabled,
        "websocket_port": config.channels.mobile.websocket_port,
        "tls_enabled": config.channels.mobile.tls_enabled,
        "max_connections": config.channels.mobile.max_connections,
        "heartbeat_interval": config.channels.mobile.heartbeat_interval,
    }
