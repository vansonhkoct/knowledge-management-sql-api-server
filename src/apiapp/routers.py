"""
Router Configuration Module

Centralizes API router registration for the application.
"""

from typing import List
from fastapi import APIRouter

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

def get_all_routers() -> List[APIRouter]:
    """Get all API routers organized by functional groups."""

    # Core application routers
    core_routers = [
        router_health,      # Health checks
        router_ws,          # WebSocket support
        router_auth,        # Authentication
    ]

    # User management routers
    user_routers = [
        router_user,        # User operations
        router_role,        # Role management
        router_permission,  # Permissions
    ]

    # Content management routers
    content_routers = [
        router_file,        # File operations
        router_category,    # Category management
        router_party,       # Party/organization management
        router_party_shared_categorys,       # Party shared categories
        router_role_accessible_categorys,    # Role accessible categories
        router_role_permission,              # Role permissions
    ]

    # Development/testing routers
    test_routers = [
        router_file_estest, # ES Integration testing (should be conditional on environment)
    ]

    # Combine all routers in order of priority
    all_routers = core_routers + user_routers + content_routers + test_routers

    return all_routers