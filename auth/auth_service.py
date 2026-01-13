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
    
    def _format_user(self, user) -> Dict[str, Any]:
        """Helper to format user object with metadata"""
        if not user:
            return {}
            
        # Exhaustive metadata check
        metadata = {}
        for attr in ["user_metadata", "raw_user_meta_data", "app_metadata"]:
            val = getattr(user, attr, None)
            if val and isinstance(val, dict):
                metadata.update(val)
        
        # Priority mapping
        display_name = metadata.get("display_name") or metadata.get("full_name") or metadata.get("name")
        
        return {
            "id": user.id,
            "phone": user.phone,
            "display_name": display_name,
            "user_metadata": metadata,
            "created_at": user.created_at,
            "last_sign_in_at": getattr(user, "last_sign_in_at", None)
        }
    
    async def sign_up(self, phone: str, password: str, display_name: str = None) -> Dict[str, Any]:
        """
        Register a new user with phone and password
        """
        try:
            # Metadata is crucial for "attaching" info without complicating auth logic
            user_metadata = {}
            if display_name:
                user_metadata["display_name"] = display_name
                
            # Attempt 1: Dictionary style (commonly used in v2+ and wrappers)
            credentials = {
                "phone": phone,
                "password": password
            }
            if user_metadata:
                # Modern GoTrue-python uses 'options': {'data': ...}
                credentials["options"] = {"data": user_metadata}
                # Some wrappers might prefer 'data' at root
                credentials["data"] = user_metadata
            
            try:
                # Try passing as a single dict first
                response = self.client.auth.sign_up(credentials)
            except Exception as e:
                # Fallback: Try keyword arguments style (v1 or direct library calls)
                try:
                    # In keyword style, 'data' is the common param for metadata
                    response = self.client.auth.sign_up(
                        phone=phone,
                        password=password,
                        data=user_metadata if user_metadata else None
                    )
                except Exception as inner_e:
                    # If both fail, raise the original error or a clearer one
                    raise Exception(f"GoTrue sign_up failed with both dict and kwargs. Last error: {str(inner_e)}")
            
            formatted_user = self._format_user(response.user)
            # Manual injection for immediate feedback if Supabase hasn't synced it yet
            if not formatted_user.get("display_name") and display_name:
                formatted_user["display_name"] = display_name
                
            return {
                "success": True,
                "message": "User created successfully. Please verify your phone number with the OTP sent.",
                "user": formatted_user
            }
        except Exception as e:
            raise Exception(f"Failed to sign up: {str(e)}")

    async def sign_in_with_password(self, phone: str, password: str) -> Dict[str, Any]:
        """
        Sign in with phone and password
        """
        try:
            response = self.client.auth.sign_in_with_password({
                "phone": phone,
                "password": password
            })
            
            if not response.session:
                raise Exception("Login failed: No session created")
                
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_in": response.session.expires_in,
                "token_type": "bearer",
                "user": self._format_user(response.user)
            }
        except Exception as e:
            raise Exception(f"Login failed: {str(e)}")
    
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
    
    async def verify_otp(self, phone_number: str, otp: str, type: str = "sms") -> Dict[str, Any]:
        """
        Verify OTP code and create session
        
        Args:
            phone_number: Phone number in E.164 format
            otp: 6-digit OTP code
            type: Verification type ('sms', 'signup', etc.)
            
        Returns:
            Dictionary with session data
            
        Raises:
            Exception: If OTP verification fails
        """
        try:
            response = self.client.auth.verify_otp({
                "phone": phone_number,
                "token": otp,
                "type": type
            })
            
            if not response.session:
                raise Exception("Failed to create session")
            
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_in": response.session.expires_in,
                "token_type": "bearer",
                "user": self._format_user(response.user)
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
            
            return self._format_user(response.user)
        except Exception as e:
            raise Exception(f"Failed to get user: {str(e)}")

    async def reset_password_after_otp(self, phone: str, otp: str, new_password: str) -> Dict[str, Any]:
        """
        Reset password after verifying OTP
        1. Verify OTP to get a temporary session
        2. Update password using that session
        """
        try:
            # 1. Verify OTP (type="sms" or type="recovery" depending on Supabase config, 
            # usually for phone recovery it might be 'sms')
            verify_response = self.client.auth.verify_otp({
                "phone": phone,
                "token": otp,
                "type": "sms"
            })
            
            if not verify_response.session:
                raise Exception("OTP verification failed, no session created")
            
            # 2. Set session for the update
            self.client.auth.set_session(verify_response.session.access_token, verify_response.session.refresh_token)
            
            # 3. Update password
            update_response = self.client.auth.update_user({
                "password": new_password
            })
            
            return {
                "success": True,
                "message": "Password updated successfully",
                "user_id": update_response.user.id
            }
        except Exception as e:
            raise Exception(f"Failed to reset password: {str(e)}")

    async def initiate_phone_change(self, access_token: str, new_phone: str) -> Dict[str, Any]:
        """
        Initiate phone number change.
        This sends a verification code to the NEW phone number.
        """
        try:
            self.client.auth.set_session(access_token, access_token)
            # update_user will trigger a verification SMS to the new phone
            response = self.client.auth.update_user({
                "phone": new_phone
            })
            return {
                "success": True,
                "message": f"Verification code sent to {new_phone}. Please verify to complete the change.",
                "user": response.user
            }
        except Exception as e:
            raise Exception(f"Failed to initiate phone change: {str(e)}")

    async def verify_phone_change(self, access_token: str, new_phone: str, otp: str) -> Dict[str, Any]:
        """
        Verify the phone change with the OTP sent to the new number.
        """
        try:
            self.client.auth.set_session(access_token, access_token)
            response = self.client.auth.verify_otp({
                "phone": new_phone,
                "token": otp,
                "type": "phone_change"
            })
            
            if not response.user:
                raise Exception("Phone change verification failed")
                
            return {
                "success": True,
                "message": "Phone number updated successfully",
                "phone": response.user.phone
            }
        except Exception as e:
            raise Exception(f"Failed to verify phone change: {str(e)}")


# Singleton instance
auth_service = AuthService()
