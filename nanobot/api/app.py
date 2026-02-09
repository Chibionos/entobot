"""FastAPI application for enterprise mobile backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

if TYPE_CHECKING:
    from nanobot.auth.jwt_manager import JWTManager
    from nanobot.config.schema import Config
    from nanobot.pairing.manager import PairingManager


def create_app(
    config: Config,
    pairing_manager: PairingManager,
    jwt_manager: JWTManager,
) -> FastAPI:
    """
    Create FastAPI application with all routes.

    Args:
        config: Application configuration
        pairing_manager: Pairing manager instance
        jwt_manager: JWT manager instance

    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="Entobot Enterprise API",
        description="REST API for mobile app management and settings",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.network.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store dependencies in app state
    app.state.config = config
    app.state.pairing_manager = pairing_manager
    app.state.jwt_manager = jwt_manager

    # Register routers
    from nanobot.api.auth import router as auth_router
    from nanobot.api.settings import router as settings_router

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(settings_router, prefix="/api/v1")

    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok", "service": "entobot-enterprise"}

    logger.info("FastAPI application created")

    return app
