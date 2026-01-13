# Supabase Phone Authentication - Quick Reference

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd e:\Qualiwo\Qualiapi
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
Add to `e:\Qualiwo\Qualiapi\.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### 3. Start API
```bash
python app.py
```

### 4. Test
```bash
cd e:\Qualiwo\auth
python test_auth.py
```

## 📡 API Endpoints

### Sign Up
```bash
POST /auth/signup
{
  "phone": "+1234567890",
  "password": "your-password"
}
```

### Login (Password)
```bash
POST /auth/login
{
  "phone": "+1234567890",
  "password": "your-password"
}
```

### Send OTP (Passwordless Login / Verification)
```bash
POST /auth/send-otp
{
  "phone": "+1234567890"
}
```

### Verify OTP
```bash
POST /auth/verify-otp
{
  "phone": "+1234567890",
  "otp": "123456"
}
```

### Password Recovery
1. **Send Recovery OTP**: `POST /auth/password-recovery/send-otp`
   ```json
   {"phone": "+1234567890"}
   ```
2. **Reset Password**: `POST /auth/password-recovery/reset`
   ```json
   {
     "phone": "+1234567890",
     "otp": "123456",
     "new_password": "new-secure-password"
   }
   ```

### Phone Number Change
1. **Initiate**: `POST /auth/phone-change/initiate` (Requires Auth)
   ```json
   {"new_phone": "+1234567891"}
   ```
2. **Verify**: `POST /auth/phone-change/verify` (Requires Auth)
   ```json
   {
     "new_phone": "+1234567891",
     "otp": "123456"
   }
   ```


### Get User Info
```bash
GET /auth/me
Headers: Authorization: Bearer {access_token}
```

### Refresh Token
```bash
POST /auth/refresh
{
  "refresh_token": "your-refresh-token"
}
```

### Logout
```bash
POST /auth/logout
Headers: Authorization: Bearer {access_token}
```

## 🔒 Protect Routes

```python
from auth.middleware import require_auth

@app.get("/protected")
async def protected(user: dict = Depends(require_auth)):
    return {"user_id": user["id"]}
```

## 📚 Documentation

- **Setup Guide**: `e:\Qualiwo\auth\README.md`
- **Examples**: `e:\Qualiwo\auth\example_protected_routes.py`
- **API Docs**: http://localhost:8000/docs

## ✅ Files Created

```
auth/
├── __init__.py                    # Package init
├── models.py                      # Pydantic models
├── auth_service.py                # Supabase service
├── middleware.py                  # Auth dependencies
├── routes.py                      # API endpoints
├── test_auth.py                   # Test script
├── example_protected_routes.py    # Usage examples
└── README.md                      # Setup guide
```

## 🔧 Next Steps

1. Create Supabase project at https://supabase.com
2. Enable phone authentication in dashboard
3. Configure SMS provider (Twilio)
4. Add credentials to `.env`
5. Run `pip install -r requirements.txt`
6. Test with `python test_auth.py`
