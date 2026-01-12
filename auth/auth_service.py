"""
Supabase authentication service
Handles phone authentication, OTP sending/verification, and session management
"""

import os
from typing import Dict, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class AuthService:
    """Service for handling Supabase authentication operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables"
            )
        
        self.client: Client = create_client(supabase_url, supabase_key)
    
    async def send_otp(self, phone_number: str) -> Dict[str, Any]:
        """
        Send OTP code to phone number
        
        Args:
            phone_number: Phone number in E.164 format (e.g., +1234567890)
            
        Returns:
            Dictionary with success status and message
            
        Raises:
            Exception: If OTP sending fails
        """
        try:
            response = self.client.auth.sign_in_with_otp({
                "phone": phone_number
            })
            
            return {
                "success": True,
                "message": "OTP sent successfully",
                "phone_number": phone_number
            }
        except Exception as e:
            raise Exception(f"Failed to send OTP: {str(e)}")
    
    async def verify_otp(self, phone_number: str, otp: str) -> Dict[str, Any]:
        """
        Verify OTP code and create session
        
        Args:
            phone_number: Phone number in E.164 format
            otp: 6-digit OTP code
            
        Returns:
            Dictionary with session data (access_token, refresh_token, user)
            
        Raises:
            Exception: If OTP verification fails
        """
        try:
            response = self.client.auth.verify_otp({
                "phone": phone_number,
                "token": otp,
                "type": "sms"
            })
            
            if not response.session:
                raise Exception("Failed to create session")
            
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_in": response.session.expires_in,
                "token_type": "bearer",
                "user": {
                    "id": response.user.id,
                    "phone": response.user.phone,
                    "email": response.user.email,
                    "created_at": response.user.created_at,
                    "last_sign_in_at": response.user.last_sign_in_at
                }
            }
        except Exception as e:
            raise Exception(f"Failed to verify OTP: {str(e)}")
    
    async def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Refresh token from previous authentication
            
        Returns:
            Dictionary with new session data
            
        Raises:
            Exception: If token refresh fails
        """
        try:
            response = self.client.auth.refresh_session(refresh_token)
            
            if not response.session:
                raise Exception("Failed to refresh session")
            
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_in": response.session.expires_in,
                "token_type": "bearer"
            }
        except Exception as e:
            raise Exception(f"Failed to refresh session: {str(e)}")
    
    async def sign_out(self, access_token: str) -> Dict[str, Any]:
        """
        Sign out user and invalidate session
        
        Args:
            access_token: Access token to invalidate
            
        Returns:
            Dictionary with success status
            
        Raises:
            Exception: If sign out fails
        """
        try:
            # Set the session for the client
            self.client.auth.set_session(access_token, access_token)
            
            # Sign out
            self.client.auth.sign_out()
            
            return {
                "success": True,
                "message": "Signed out successfully"
            }
        except Exception as e:
            raise Exception(f"Failed to sign out: {str(e)}")
    
    async def get_user(self, access_token: str) -> Dict[str, Any]:
        """
        Get current user information
        
        Args:
            access_token: Valid access token
            
        Returns:
            Dictionary with user information
            
        Raises:
            Exception: If user retrieval fails
        """
        try:
            # Set the session for the client
            self.client.auth.set_session(access_token, access_token)
            
            # Get user
            response = self.client.auth.get_user()
            
            if not response.user:
                raise Exception("User not found")
            
            return {
                "id": response.user.id,
                "phone": response.user.phone,
                "email": response.user.email,
                "created_at": response.user.created_at,
                "last_sign_in_at": response.user.last_sign_in_at
            }
        except Exception as e:
            raise Exception(f"Failed to get user: {str(e)}")


# Singleton instance
auth_service = AuthService()
