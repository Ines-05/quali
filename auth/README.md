# Supabase Phone Authentication - Setup Guide

This guide will help you set up and configure Supabase phone authentication for the Qualiwo API.

## Prerequisites

- Python 3.9+
- Supabase account (free tier is sufficient)
- SMS provider account (Twilio recommended for testing)

## Step 1: Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Fill in project details:
   - Name: `qualiwo-auth` (or your preferred name)
   - Database Password: Generate a strong password
   - Region: Choose closest to your users
4. Click "Create new project" and wait for setup to complete

## Step 2: Enable Phone Authentication

1. In your Supabase project dashboard, navigate to **Authentication** → **Providers**
2. Find **Phone** in the list of providers
3. Toggle **Enable Phone provider** to ON
4. Configure SMS provider (Twilio recommended):
   
   ### For Twilio:
   - Sign up at [https://www.twilio.com](https://www.twilio.com)
   - Get your Account SID and Auth Token from the Twilio Console
   - Get a Twilio phone number (for sending SMS)
   - In Supabase, select "Twilio" as the SMS provider
   - Enter your Twilio credentials:
     - Account SID
     - Auth Token
     - Twilio Phone Number
   
   ### For Testing (Twilio Trial):
   - Twilio trial accounts can only send SMS to verified phone numbers
   - Add your test phone number in Twilio Console → Phone Numbers → Verified Caller IDs
   - You'll receive $15 in free credits

5. Click **Save**

## Step 3: Get Supabase Credentials

1. In your Supabase project, go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon public** key (under "Project API keys")
   - **service_role** key (optional, for admin operations)

## Step 4: Configure Environment Variables

1. Open `e:\Qualiwo\Qualiapi\.env` file
2. Add the following variables:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

Replace the values with your actual Supabase credentials from Step 3.

## Step 5: Install Dependencies

```bash
cd e:\Qualiwo\Qualiapi
.\venv\Scripts\activate
pip install -r requirements.txt
```

This will install:
- `supabase` - Supabase Python client
- `python-jose[cryptography]` - JWT token handling
- `phonenumbers` - Phone number validation

## Step 6: Start the API

```bash
python app.py
```

The API will start on `http://localhost:8000`

## Step 7: Test Authentication

### Option 1: Using the Test Script

```bash
cd e:\Qualiwo\auth
python test_auth.py
```

Follow the prompts to test the complete authentication flow.

### Option 2: Using cURL

**Send OTP:**
```bash
curl -X POST http://localhost:8000/auth/send-otp \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\": \"+1234567890\"}"
```

**Verify OTP:**
```bash
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\": \"+1234567890\", \"otp\": \"123456\"}"
```

**Get Current User:**
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Option 3: Using Swagger UI

1. Open `http://localhost:8000/docs`
2. Test the endpoints interactively

## Step 8: Protect Existing Routes (Optional)

To require authentication for existing routes, add the `require_auth` dependency:

```python
from auth.middleware import require_auth

@app.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    current_user: dict = Depends(require_auth)  # Add this
):
    # Now only authenticated users can access this endpoint
    # current_user contains user info (id, phone, etc.)
    ...
```

## Troubleshooting

### "Failed to send OTP"
- Check that phone authentication is enabled in Supabase
- Verify SMS provider credentials are correct
- Ensure phone number is in E.164 format (+country_code + number)
- For Twilio trial, verify the phone number is added to verified caller IDs

### "Invalid or expired token"
- Tokens expire after a certain time (default: 1 hour)
- Use the refresh token to get a new access token
- Check that SUPABASE_URL and SUPABASE_ANON_KEY are correct

### "Phone number must be in E.164 format"
- Phone numbers must start with `+` followed by country code
- Examples:
  - US: `+12025551234`
  - France: `+33612345678`
  - Benin: `+22997123456`

## Next Steps

- Configure phone number validation rules in Supabase
- Set up rate limiting for OTP requests
- Customize OTP message template in Supabase
- Add user profile management
- Implement password reset flow (if using email + password)

## API Documentation

Full API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
