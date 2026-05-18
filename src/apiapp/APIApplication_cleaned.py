"""
FastAPI Application Configuration

This module configures and initializes the FastAPI application for the
knowledge management SQL API server.
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
import copy

from database import TORTOISE_ORM

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Route imports
from src.controllers.apis.api_ws import router as router_ws
from src.controllers.apis.api_file import router as router_file
from src.controllers.apis.api_file_estest import router as router_file_estest
from src.controllers.apis.api_health import router as router_health
from src.controllers.apis.api_category import router as router_category
from src.controllers.apis.api_user import router as router_user
from src.controllers.apis.api_role import router as router_role
from src.controllers.apis.api_permission import router as router_permission
from src.controllers.apis.api_party import router as router_party
from src.controllers.apis.api_auth import router as router_auth
from src.controllers.apis.api_party_shared_categorys import router as router_party_shared_categorys
from src.controllers.apis.api_role_accessible_categorys import router as router_role_accessible_categorys
from src.controllers.apis.api_role_permission import router as router_role_permission


def _mount_static_directory(app: FastAPI, path: str, name: str) -> None:
    """Mount a static directory with proper error handling."""
    try:
        static_path = Path(path)
        static_path.mkdir(parents=True, exist_ok=True)
        app.mount(f"/{name}", StaticFiles(directory=str(static_path)), name=name)
        logger.info(f"Static directory mounted: /{name} -> {static_path}")
    except Exception as e:
        logger.error(f"Failed to mount static directory {path}: {e}")
        # Only raise in production environments
        if os.getenv("ENVIRONMENT", "development") == "production":
            raise RuntimeError(f"Failed to mount static directory: {e}")


def _configure_database(app: FastAPI) -> None:
    """Configure Tortoise ORM database connection with proper error handling."""
    try:
        # Deep copy to avoid modifying the original config
        db_config = copy.deepcopy(TORTOISE_ORM)

        # Update models configuration
        db_config["apps"]["models"]["models"] = [
            "src.schemas.master",
            "aerich.models",
        ]
        db_config["apps"]["models"]["default_connection"] = "default"

        register_tortoise(
            app,
            config=db_config,
            generate_schemas=False,  # Use migrations instead
            add_exception_handlers=True,
        )

        logger.info("Tortoise ORM database configuration completed")
    except Exception as e:
        logger.error(f"Failed to configure database: {e}")
        raise RuntimeError("Database configuration failed") from e


def create_app() -> FastAPI:
    """Create and configure the FastAPI application with professional standards."""

    # Create FastAPI app with metadata
    app = FastAPI(
        title="Knowledge Management API Server",
        description="SQL API server for knowledge management with RAG capabilities",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/v1/openapi.json"
    )

    logger.info("FastAPI application initialization started")

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict to specific origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("CORS middleware configured")

    # Mount static directories
    _mount_static_directory(app, "./static", "static")
    _mount_static_directory(app, "./upload", "upload")

    # Configure database
    _configure_database(app)

    # Include routers in logical order
    routers = [
        router_health,      # Basic health checks first
        router_auth,        # Authentication
        router_ws,          # WebSocket support
        router_user,        # User management
        router_role,        # Role management
        router_permission,  # Permissions
        router_party,       # Party/organization
        router_category,    # Categories
        router_file,        # File operations
        router_party_shared_categorys,       # Share categories
        router_role_accessible_categorys,    # Role-based access
        router_role_permission,              # Role permissions
        # Development/testing routers (last - should be conditional)
        router_file_estest,
    ]

    for router in routers:
        try:
            app.include_router(router)
            router_name = router.prefix or "root"
            logger.info(f"Router included: {router_name}")
        except Exception as e:
            logger.error(f"Failed to include router {router}: {e}")
            raise RuntimeError(f"Router inclusion failed: {e}")

    logger.info("FastAPI application initialization completed successfully")
    return app


# Initialize the application
app = create_app()

# Export for wsgi/asgi servers
__all__ = ["app"]