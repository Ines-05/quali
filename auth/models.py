"""
Pydantic models for authentication requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Union, Any
from datetime import datetime
import phonenumbers


class PhoneNumberRequest(BaseModel):
    """Request model for phone number input"""
    phone: str = Field(..., description="Phone number in E.164 format (e.g., +1234567890)")
    
    @validator('phone')
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        try:
            # Try parsing as international first
            parsed = phonenumbers.parse(v, None)
        except phonenumbers.NumberParseException:
            try:
                # If that fails, try parsing as Benin number (default)
                parsed = phonenumbers.parse(v, "BJ")
            except phonenumbers.NumberParseException:
                raise ValueError("Phone number must be in E.164 format (e.g., +1234567890)")
        
        if not phonenumbers.is_possible_number(parsed):
            raise ValueError("Invalid phone number")
        
        # Return in E.164 format
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


class SendOTPResponse(BaseModel):
    """Response after sending OTP"""
    message: str = "OTP sent successfully"
    phone: str


class VerifyOTPRequest(BaseModel):
    """Request model for OTP verification"""
    phone: str = Field(..., description="Phone number in E.164 format")
    otp: str = Field(..., description="6-digit OTP code", min_length=6, max_length=6)
    
    @validator('phone')
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        try:
            # Try parsing as international first
            parsed = phonenumbers.parse(v, None)
        except phonenumbers.NumberParseException:
            try:
                # If that fails, try parsing as Benin number (default)
                parsed = phonenumbers.parse(v, "BJ")
            except phonenumbers.NumberParseException:
                raise ValueError("Phone number must be in E.164 format (e.g., +1234567890)")
        
        if not phonenumbers.is_possible_number(parsed):
            raise ValueError("Invalid phone number")
        
        # Return in E.164 format
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


class VerifyOTPResponse(BaseModel):
    """Response after successful OTP verification"""
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"
    user: dict


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh"""
    refresh_token: str = Field(..., description="Refresh token")


class RefreshTokenResponse(BaseModel):
    """Response after token refresh"""
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User information response"""
    id: str
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: Union[str, datetime, Any]
    last_sign_in_at: Optional[Union[str, datetime, Any]] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
