"""
Test script for QualiAPI Authentication
Tests the password-based flow, passwordless flow, and advanced features (Recovery, Phone Change).
"""

import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# API base URL
BASE_URL = "http://localhost:8000"


async def test_password_auth_flow():
    """Test SignUp + VerifyOTP + Login with Password"""
    
    print("\n" + "=" * 60)
    print("TEST: PASSWORD-BASED AUTHENTICATION (SignUp -> Verify -> Login)")
    print("=" * 60)
    
    phone = input("\nEnter phone number (+229...): ").strip()
    password = input("Enter password (min 8 chars): ").strip()
    display_name = input("Enter display name (optional, press Enter to skip): ").strip() or None
    
    async with httpx.AsyncClient() as client:
        # 1. Sign Up
        print(f"\n[1/4] Signing up {phone}...")
        try:
            signup_data = {
                "phone": phone, 
                "password": password,
                "display_name": display_name
            }
            response = await client.post(
                f"{BASE_URL}/auth/signup",
                json={k: v for k, v in signup_data.items() if v is not None}
            )
            response.raise_for_status()
            result = response.json()
            print(f"✓ {result['message']}")
            if "user" in result:
                user = result["user"]
                print(f"  User ID: {user['id']}")
                if "user_metadata" in user:
                    print(f"  Metadata: {user['user_metadata']}")
        except httpx.HTTPStatusError as e:
            print(f"✗ Failed to sign up: {e.response.json()}")
            if "already registered" not in str(e.response.json()):
                return
            print("! User already exists, proceeding to login test.")
            result = {} # Prevent UnboundLocalError

        # 2. Verify OTP (Only required once after signup)
        if "User created" in (result.get("message") or "") or "Please verify" in (result.get("message") or ""):
            otp = input("\nEnter the OTP code received by SMS: ").strip()
            print(f"\n[2/4] Verifying OTP for account activation (and password sync)...")
            try:
                # We send the password here to ensure it's synced if the user already existed!
                verify_payload = {
                    "phone": phone, 
                    "otp": otp,
                    "password": password  # <--- CRITICAL: Send password to rewrite it if user existed
                }
                response = await client.post(
                    f"{BASE_URL}/auth/verify-otp",
                    json=verify_payload
                )
                response.raise_for_status()
                print(f"✓ Account verified and password synced!")
            except httpx.HTTPStatusError as e:
                print(f"✗ Verification failed: {e.response.json()}")
                return

        # 3. Login with Password (No SMS required)
        print(f"\n[3/4] Logging in with password '{password}'...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/login",
                json={"phone": phone, "password": password}
            )
            response.raise_for_status()
            result = response.json()
            access_token = result["access_token"]
            print(f"✓ Login successful! User ID: {result['user']['id']}")
        except httpx.HTTPStatusError as e:
            print(f"✗ Login failed: {e.response.json()}")
            return

        # 4. Access Protected Route
        print(f"\n[4/4] Verifying access with token...")
        try:
            response = await client.get(
                f"{BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            data = response.json()
            display_name = data.get('display_name')
            phone = data.get('phone')
            print(f"✓ Profile retrieved: Hello {display_name if display_name else phone}")
            if data.get('user_metadata'):
                print(f"  Full Metadata: {data.get('user_metadata')}")
            return access_token
        except httpx.HTTPStatusError as e:
            print(f"✗ Access denied: {e.response.json()}")
            return None

        print("\n✓ PASSWORD AUTH FLOW TEST COMPLETED!")


async def test_password_recovery():
    """Test Password Recovery flow"""
    print("\n" + "=" * 60)
    print("TEST: PASSWORD RECOVERY (OTP -> Reset)")
    print("=" * 60)
    
    phone = input("\nEnter phone number (+229...): ").strip()
    
    async with httpx.AsyncClient() as client:
        # 1. Send Recovery OTP
        print(f"\n[1/2] Sending recovery OTP...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/password-recovery/send-otp",
                json={"phone": phone}
            )
            response.raise_for_status()
            print(f"✓ {response.json()['message']}")
        except httpx.HTTPStatusError as e:
            print(f"✗ Failed: {e.response.json()}")
            return

        # 2. Reset Password
        otp = input("\nEnter OTP: ").strip()
        new_password = input("Enter NEW password: ").strip()
        print(f"\n[2/2] Resetting password...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/password-recovery/reset",
                json={"phone": phone, "otp": otp, "new_password": new_password}
            )
            response.raise_for_status()
            print(f"✓ {response.json()['message']}")
        except httpx.HTTPStatusError as e:
            print(f"✗ Failed: {e.response.json()}")


async def test_account_management():
    """Test Phone Change and Email Update"""
    print("\n" + "=" * 60)
    print("TEST: ACCOUNT MANAGEMENT (Phone Change & Email Update)")
    print("=" * 60)
    
    access_token = input("\nEnter valid access token (or run Login test first): ").strip()
    if not access_token:
        print("Access token required for these tests.")
        return

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 1. Email Update
        new_email = input("\nEnter new email (or press Enter to skip): ").strip()
        if new_email:
            print(f"\n[1/3] Updating email to {new_email}...")
            try:
                response = await client.post(
                    f"{BASE_URL}/auth/email/update",
                    headers=headers,
                    json={"email": new_email}
                )
                response.raise_for_status()
                print(f"✓ {response.json()['message']}")
            except httpx.HTTPStatusError as e:
                print(f"✗ Email update failed: {e.response.json()}")

        # 2. Phone Change Initiate
        new_phone = input("\nEnter NEW phone number to change to (or Enter to skip): ").strip()
        if new_phone:
            print(f"\n[2/3] Initiating phone change to {new_phone}...")
            try:
                response = await client.post(
                    f"{BASE_URL}/auth/phone-change/initiate",
                    headers=headers,
                    json={"new_phone": new_phone}
                )
                response.raise_for_status()
                print(f"✓ {response.json()['message']}")
                
                # 3. Phone Change Verify
                otp = input("\nEnter OTP sent to NEW phone: ").strip()
                print(f"\n[3/3] Verifying phone change...")
                try:
                    response = await client.post(
                        f"{BASE_URL}/auth/phone-change/verify",
                        headers=headers,
                        json={"new_phone": new_phone, "otp": otp}
                    )
                    response.raise_for_status()
                    print(f"✓ {response.json()['message']}")
                except httpx.HTTPStatusError as e:
                    print(f"✗ Phone verification failed: {e.response.json()}")
            except httpx.HTTPStatusError as e:
                print(f"✗ Phone change initiation failed: {e.response.json()}")


async def test_passwordless_flow():
    """Test the legacy OTP-only flow"""
    
    print("\n" + "=" * 60)
    print("TEST: PASSWORDLESS AUTHENTICATION (OTP Only)")
    print("=" * 60)
    
    phone = input("\nEnter phone number (+229...): ").strip()
    
    async with httpx.AsyncClient() as client:
        # 1. Send OTP
        print(f"\n[1/2] Sending OTP...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/send-otp",
                json={"phone": phone}
            )
            response.raise_for_status()
            print(f"✓ {response.json()['message']}")
        except httpx.HTTPStatusError as e:
            print(f"✗ Failed: {e.response.json()}")
            return
            
        # 2. Verify
        otp = input("\nEnter OTP: ").strip()
        print(f"\n[2/2] Verifying...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/verify-otp",
                json={"phone": phone, "otp": otp, "type": "sms"}
            )
            response.raise_for_status()
            print(f"✓ Success! User: {response.json()['user']['id']}")
        except httpx.HTTPStatusError as e:
            print(f"✗ Verification failed: {e.response.json()}")


if __name__ == "__main__":
    print("\nQualiAPI Auth Tester - Advanced")
    print("Make sure the API is running (python app.py)")
    
    while True:
        print("\n--- MENU ---")
        print("1. Test Password Flow (Signup/Login)")
        print("2. Test Passwordless Flow (OTP only)")
        print("3. Test Password Recovery (Forgot Password)")
        print("4. Test Account Management (Phone Change/Email)")
        print("q. Quit")
        choice = input("Choice: ").strip().lower()
        
        if choice == "1":
            asyncio.run(test_password_auth_flow())
        elif choice == "2":
            asyncio.run(test_passwordless_flow())
        elif choice == "3":
            asyncio.run(test_password_recovery())
        elif choice == "4":
            asyncio.run(test_account_management())
        elif choice == "q":
            break
        else:
            print("Invalid choice")
