"""
Test script for Supabase phone authentication
Run this script to test the authentication flow
"""

import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# API base URL
BASE_URL = "http://localhost:8000"


async def test_auth_flow():
    """Test the complete authentication flow"""
    
    print("=" * 60)
    print("SUPABASE PHONE AUTHENTICATION TEST")
    print("=" * 60)
    
    # Get phone number from user
    phone_number = input("\nEnter phone number (E.164 format, e.g., +1234567890): ").strip()
    
    async with httpx.AsyncClient() as client:
        # Step 1: Send OTP
        print(f"\n[1/5] Sending OTP to {phone_number}...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/send-otp",
                json={"phone": phone_number}
            )
            response.raise_for_status()
            result = response.json()
            print(f"✓ {result['message']}")
        except httpx.HTTPStatusError as e:
            print(f"✗ Failed to send OTP: {e.response.json()}")
            return
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return
        
        # Step 2: Get OTP from user
        otp = input("\nEnter the OTP code you received: ").strip()
        
        # Step 3: Verify OTP
        print(f"\n[2/5] Verifying OTP...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/verify-otp",
                json={"phone": phone_number, "otp": otp}
            )
            response.raise_for_status()
            result = response.json()
            access_token = result["access_token"]
            refresh_token = result["refresh_token"]
            print(f"✓ OTP verified successfully!")
            print(f"  User ID: {result['user']['id']}")
            print(f"  Phone: {result['user']['phone']}")
        except httpx.HTTPStatusError as e:
            print(f"✗ Failed to verify OTP: {e.response.json()}")
            return
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return
        
        # Step 4: Get current user info
        print(f"\n[3/5] Getting current user info...")
        try:
            response = await client.get(
                f"{BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            result = response.json()
            print(f"✓ User info retrieved:")
            print(f"  ID: {result['id']}")
            print(f"  Phone: {result['phone']}")
            print(f"  Created: {result['created_at']}")
        except httpx.HTTPStatusError as e:
            print(f"✗ Failed to get user info: {e.response.json()}")
            return
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return
        
        # Step 5: Refresh token
        print(f"\n[4/5] Refreshing access token...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            response.raise_for_status()
            result = response.json()
            new_access_token = result["access_token"]
            print(f"✓ Token refreshed successfully!")
        except httpx.HTTPStatusError as e:
            print(f"✗ Failed to refresh token: {e.response.json()}")
            return
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return
        
        # Step 6: Logout
        print(f"\n[5/5] Logging out...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/logout",
                headers={"Authorization": f"Bearer {new_access_token}"}
            )
            response.raise_for_status()
            result = response.json()
            print(f"✓ {result['message']}")
        except httpx.HTTPStatusError as e:
            print(f"✗ Failed to logout: {e.response.json()}")
            return
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)


async def test_protected_endpoint():
    """Test accessing a protected endpoint without authentication"""
    
    print("\n" + "=" * 60)
    print("TESTING PROTECTED ENDPOINT WITHOUT AUTH")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/auth/me")
            print(f"✗ Unexpected success: {response.json()}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                print(f"✓ Protected endpoint correctly rejected unauthenticated request")
            else:
                print(f"✗ Unexpected error: {e.response.json()}")


if __name__ == "__main__":
    print("\nMake sure the API is running on http://localhost:8000")
    print("Run: python app.py\n")
    
    choice = input("Test options:\n1. Full authentication flow\n2. Test protected endpoint\n3. Both\n\nChoice (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(test_auth_flow())
    elif choice == "2":
        asyncio.run(test_protected_endpoint())
    elif choice == "3":
        asyncio.run(test_protected_endpoint())
        asyncio.run(test_auth_flow())
    else:
        print("Invalid choice")
