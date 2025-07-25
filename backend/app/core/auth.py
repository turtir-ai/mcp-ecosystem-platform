"""
Authentication module for MCP Ecosystem Platform
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel


class User(BaseModel):
    """User model"""
    id: str
    username: str
    email: str
    is_active: bool = True


# Simple bearer token security - auto_error=False for development
security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> User:
    """
    Get current user from token
    For now, this is a simple mock implementation that allows no auth for development
    """
    # Mock user for development - allow access without token
    return User(
        id="dev-user-1",
        username="developer",
        email="dev@example.com",
        is_active=True
    )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


# Optional auth dependency for development
async def optional_auth() -> Optional[User]:
    """Optional authentication for development"""
    return User(
        id="dev-user-1",
        username="developer",
        email="dev@example.com",
        is_active=True
    )
