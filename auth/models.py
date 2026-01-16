"""
Pydantic models for authentication requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Union, Any, Dict
from datetime import datetime
import phonenumbers


class PhoneNumberRequest(BaseModel):
    """Request model for phone number input"""
    phone: str = Field(..., description="Phone number in E.164 format (e.g., +1234567890)")
    
    @validator('phone')
    def validate_phone(cls, v):
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


class SignUpRequest(BaseModel):
    """Request model for creating a new account"""
    phone: str = Field(..., description="Phone number in E.164 format")
    password: str = Field(..., min_length=8)
    display_name: Optional[str] = Field(None, description="Optional display name")
    
    @validator('phone')
    def validate_phone(cls, v):
        try:
            parsed = phonenumbers.parse(v, "BJ")
            if not phonenumbers.is_possible_number(parsed):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            raise ValueError("Phone number must be in E.164 format")


class LoginRequest(BaseModel):
    """Request model for logging in with phone and password"""
    phone: str = Field(..., description="Phone number in E.164 format")
    password: str = Field(...)
    
    @validator('phone')
    def validate_phone(cls, v):
        try:
            parsed = phonenumbers.parse(v, "BJ")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            raise ValueError("Phone number must be in E.164 format")


class SendOTPResponse(BaseModel):
    """Response after sending OTP"""
    message: str = "OTP sent successfully"
    phone: str


class VerifyOTPRequest(BaseModel):
    """Request model for OTP verification"""
    phone: str = Field(..., description="Phone number in E.164 format")
    otp: str = Field(..., description="6-digit OTP code", min_length=6, max_length=6)
    type: str = Field("sms", description="Verification type: 'sms' (login) or 'signup' (confirmation)")
    password: Optional[str] = Field(None, description="Optional: New password to set upon verification (for seamless signup retry)")
    
    @validator('phone')
    def validate_phone(cls, v):
        try:
            parsed = phonenumbers.parse(v, "BJ")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            raise ValueError("Phone number must be in E.164 format")


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
    """Response model for user profile information"""
    id: str
    phone: str
    display_name: Optional[str] = None
    user_metadata: Optional[Dict[str, Any]] = None
    created_at: Union[str, datetime]
    last_sign_in_at: Optional[Union[str, datetime]] = None


class PasswordRecoveryRequest(BaseModel):
    """Request model for initiating password recovery"""
    phone: str = Field(..., description="Phone number in E.164 format")

    @validator('phone')
    def validate_phone(cls, v):
        try:
            parsed = phonenumbers.parse(v, "BJ")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            raise ValueError("Phone number must be in E.164 format")


class PasswordResetRequest(BaseModel):
    """Request model for resetting password with OTP"""
    phone: str = Field(..., description="Phone number in E.164 format")
    otp: str = Field(..., description="6-digit OTP code", min_length=6, max_length=6)
    new_password: str = Field(..., description="New password (min 8 characters)", min_length=8)

    @validator('phone')
    def validate_phone(cls, v):
        try:
            parsed = phonenumbers.parse(v, "BJ")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            raise ValueError("Phone number must be in E.164 format")


class PhoneChangeRequest(BaseModel):
    """Request model for initiating phone number change"""
    new_phone: str = Field(..., description="New phone number in E.164 format")

    @validator('new_phone')
    def validate_phone(cls, v):
        try:
            parsed = phonenumbers.parse(v, "BJ")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            raise ValueError("Phone number must be in E.164 format")


class VerifyPhoneChangeRequest(BaseModel):
    """Request model for verifying phone number change"""
    new_phone: str = Field(..., description="New phone number in E.164 format")
    otp: str = Field(..., description="6-digit OTP code", min_length=6, max_length=6)

    @validator('new_phone')
    def validate_phone(cls, v):
        try:
            parsed = phonenumbers.parse(v, "BJ")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            raise ValueError("Phone number must be in E.164 format")




class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
