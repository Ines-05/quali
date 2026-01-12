"""
FastAPI routes for authentication endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from .models import (
    PhoneNumberRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    UserResponse,
    ErrorResponse
)
from .auth_service import auth_service
from .middleware import get_current_user, require_auth

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)


@router.post("/send-otp", response_model=SendOTPResponse, status_code=status.HTTP_200_OK)
async def send_otp(request: PhoneNumberRequest):
    """
    Send OTP code to phone number
    
    This endpoint sends a 6-digit OTP code via SMS to the provided phone number.
    The OTP is valid for a limited time (typically 60 seconds).
    
    Args:
        request: Phone number in E.164 format (e.g., +1234567890)
        
    Returns:
        Success message with phone number
        
    Raises:
        HTTPException: If OTP sending fails
    """
    try:
        result = await auth_service.send_otp(request.phone_number)
        return SendOTPResponse(
            message=result["message"],
            phone_number=result["phone_number"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/verify-otp", response_model=VerifyOTPResponse, status_code=status.HTTP_200_OK)
async def verify_otp(request: VerifyOTPRequest):
    """
    Verify OTP code and create session
    
    This endpoint verifies the OTP code sent to the phone number and creates
    an authenticated session. Returns access and refresh tokens.
    
    Args:
        request: Phone number and OTP code
        
    Returns:
        Session data with access_token, refresh_token, and user information
        
    Raises:
        HTTPException: If OTP verification fails (invalid code, expired, etc.)
    """
    try:
        result = await auth_service.verify_otp(request.phone_number, request.otp)
        return VerifyOTPResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/refresh", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token
    
    This endpoint refreshes an expired access token using a valid refresh token.
    Returns new access and refresh tokens.
    
    Args:
        request: Refresh token
        
    Returns:
        New session data with access_token and refresh_token
        
    Raises:
        HTTPException: If token refresh fails
    """
    try:
        result = await auth_service.refresh_session(request.refresh_token)
        return RefreshTokenResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(request: Request, current_user: dict = Depends(require_auth)):
    """
    Logout user and invalidate session
    
    This endpoint signs out the current user and invalidates their session in Supabase.
    Requires a valid access token in the Authorization header.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user (from dependency)
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If logout fails
    """
    try:
        # Extract access token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ")[1]
            await auth_service.sign_out(access_token)
            
        return {"message": "Logged out successfully"}
    except Exception as e:
        # LOGIQUE STRICTE : Si le serveur échoue, on renvoie une erreur 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate session on Supabase: {str(e)}"
        )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(current_user: dict = Depends(require_auth)):
    """
    Get current authenticated user information
    
    This endpoint returns information about the currently authenticated user.
    Requires a valid access token in the Authorization header.
    
    Args:
        current_user: Current authenticated user (from dependency)
        
    Returns:
        User information (id, phone, email, created_at, etc.)
        
    Raises:
        HTTPException: If user retrieval fails or token is invalid
    """
    try:
        return UserResponse(**current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
