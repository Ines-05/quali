"""
Example: How to protect routes with authentication

This file demonstrates how to add authentication to existing routes
"""

from fastapi import APIRouter, Depends
from auth.middleware import require_auth, get_current_user_optional

# Example 1: Require authentication for a route
router = APIRouter()

@router.get("/protected-endpoint")
async def protected_endpoint(current_user: dict = Depends(require_auth)):
    """
    This endpoint requires authentication
    Only users with valid access tokens can access it
    """
    return {
        "message": "You are authenticated!",
        "user_id": current_user["id"],
        "phone": current_user["phone"]
    }


# Example 2: Optional authentication
@router.get("/optional-auth-endpoint")
async def optional_auth_endpoint(current_user: dict = Depends(get_current_user_optional)):
    """
    This endpoint works with or without authentication
    Provides different responses based on auth status
    """
    if current_user:
        return {
            "message": f"Welcome back, {current_user['phone']}!",
            "authenticated": True,
            "user_id": current_user["id"]
        }
    else:
        return {
            "message": "Welcome, guest!",
            "authenticated": False
        }


# Example 3: Protect the existing /chat endpoint
# In app.py, modify the chat_endpoint function:

"""
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: dict = Depends(require_auth)  # Add this line
) -> ChatResponse:
    # Now only authenticated users can chat
    # You can use current_user["id"] to personalize responses
    # or track user-specific conversation history
    
    # Example: Add user_id to session_id for user-specific sessions
    session_id = request.session_id or f"user_{current_user['id']}"
    
    # Rest of the implementation...
    ...
"""


# Example 4: Create user-specific endpoints
@router.get("/my-orders")
async def get_my_orders(current_user: dict = Depends(require_auth)):
    """
    Get orders for the authenticated user
    """
    user_id = current_user["id"]
    
    # Fetch orders from database
    # orders = await db.orders.find({"user_id": user_id})
    
    return {
        "user_id": user_id,
        "orders": []  # Replace with actual orders
    }


@router.get("/my-cart")
async def get_my_cart(current_user: dict = Depends(require_auth)):
    """
    Get cart for the authenticated user
    """
    user_id = current_user["id"]
    
    # Fetch cart from database using user_id instead of session_id
    # cart = await cart_service.get_cart(user_id)
    
    return {
        "user_id": user_id,
        "cart": []  # Replace with actual cart
    }
