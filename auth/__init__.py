"""
Authentication module for Supabase phone authentication
"""

from .routes import router
from .auth_service import auth_service
from .middleware import get_current_user, get_current_user_optional, require_auth

__all__ = [
    "router",
    "auth_service",
    "get_current_user",
    "get_current_user_optional",
    "require_auth"
]
