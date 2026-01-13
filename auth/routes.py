"""
FastAPI routes for authentication endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from .models import (
    PhoneNumberRequest,
    SignUpRequest,
    LoginRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    UserResponse,
    ErrorResponse,
    PasswordRecoveryRequest,
    PasswordResetRequest,
    PhoneChangeRequest,
    VerifyPhoneChangeRequest
)
from .auth_service import auth_service
from .middleware import get_current_user, require_auth, security

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(request: SignUpRequest):
    """
    Sign up a new user with phone and password.
    Triggers a one-time SMS verification.
    """
    try:
        result = await auth_service.sign_up(
            request.phone, 
            request.password, 
            request.display_name
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=VerifyOTPResponse, status_code=status.HTTP_200_OK)
async def login(request: LoginRequest):
    """
    Login with phone and password.
    No SMS sent.
    """
    try:
        result = await auth_service.sign_in_with_password(request.phone, request.password)
        return VerifyOTPResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/send-otp", response_model=SendOTPResponse, status_code=status.HTTP_200_OK)
async def send_otp(request: PhoneNumberRequest):
    """
    Send OTP code to phone number (Passwordless flow)
    """
    try:
        result = await auth_service.send_otp(request.phone)
        return SendOTPResponse(
            message=result["message"],
            phone=result["phone_number"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/verify-otp", response_model=VerifyOTPResponse, status_code=status.HTTP_200_OK)
async def verify_otp(request: VerifyOTPRequest):
    """
    Verify OTP code (for both Signup verification and Passwordless login)
    """
    try:
        result = await auth_service.verify_otp(request.phone, request.otp, request.type)
        return VerifyOTPResponse(**result)
    except Exception as e:
        print(f"DEBUG: Verification failed for {request.phone} with type {request.type}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/refresh", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token
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
    Logout user and invalidate session in Supabase
    """
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ")[1]
            await auth_service.sign_out(access_token)
            
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate session on Supabase: {str(e)}"
        )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(current_user: dict = Depends(require_auth)):
    """
    Get current authenticated user information
    """
    try:
        return UserResponse(**current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/password-recovery/send-otp", status_code=status.HTTP_200_OK)
async def send_recovery_otp(request: PasswordRecoveryRequest):
    """
    Send OTP for password recovery
    """
    try:
        # Reusing send_otp since it's the same logic for phone-based recovery in Supabase
        result = await auth_service.send_otp(request.phone)
        return {"message": "Recovery OTP sent", "phone": request.phone}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/password-recovery/reset", status_code=status.HTTP_200_OK)
async def reset_password(request: PasswordResetRequest):
    """
    Reset password using OTP
    """
    try:
        result = await auth_service.reset_password_after_otp(
            request.phone, 
            request.otp, 
            request.new_password
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/phone-change/initiate", status_code=status.HTTP_200_OK)
async def initiate_phone_change_route(
    request: PhoneChangeRequest, 
    current_user: dict = Depends(require_auth),
    auth_credentials=Depends(security)
):
    """
    Initiate phone number change
    """
    try:
        result = await auth_service.initiate_phone_change(
            auth_credentials.credentials, 
            request.new_phone
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/phone-change/verify", status_code=status.HTTP_200_OK)
async def verify_phone_change_route(
    request: VerifyPhoneChangeRequest, 
    current_user: dict = Depends(require_auth),
    auth_credentials=Depends(security)
):
    """
    Verify phone number change
    """
    try:
        result = await auth_service.verify_phone_change(
            auth_credentials.credentials, 
            request.new_phone, 
            request.otp
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )



