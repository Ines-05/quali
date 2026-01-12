"""
Authentication middleware and dependencies for FastAPI
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from .auth_service import auth_service

# Security scheme for JWT bearer tokens
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    FastAPI dependency to get current authenticated user
    
    Args:
        credentials: HTTP Authorization credentials with bearer token
        
    Returns:
        User information dictionary
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        access_token = credentials.credentials
        user = await auth_service.get_user(access_token)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    FastAPI dependency to get current user if authenticated, None otherwise
    
    Args:
        credentials: Optional HTTP Authorization credentials
        
    Returns:
        User information dictionary or None if not authenticated
    """
    if not credentials:
        return None
    
    try:
        access_token = credentials.credentials
        user = await auth_service.get_user(access_token)
        return user
    except Exception:
        return None


def require_auth(user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency to require authentication for a route
    
    Args:
        user: User from get_current_user dependency
        
    Returns:
        User information dictionary
    """
    return user
