
"""Tools for the React LangChain Agent
Each tool represents a specific action the agent can perform to assist users
"""

from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
import httpx
import os
import time
from dotenv import load_dotenv
from .cart_service import cart_service
from .user_service import user_service
from langchain_core.runnables import RunnableConfig

load_dotenv()

# External API Configuration
QUALIWO_SEARCH_API_URL = "https://apiquali.vercel.app"


@tool
def product_search_tool(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search for products in the catalog based on user query.
    
    ═══════════════════════════════════════════════════════════════════
    PURPOSE
    ═══════════════════════════════════════════════════════════════════
    This tool searches the product catalog and returns relevant items matching
    the user's search criteria. It uses the Qualiwo Search API to find products
    and returns them in a normalized format ready for display.
    
    ═══════════════════════════════════════════════════════════════════
    WHEN TO USE
    ═══════════════════════════════════════════════════════════════════
    Use this tool when:
    • User asks about specific products (e.g., "show me iPhones")
    • User mentions product categories (e.g., "I need kitchen items")
    • User wants to browse or discover products
    • User asks "what do you have?" or "show me your catalog"
    
    DO NOT use when:
    • User is asking about their cart contents
    • User wants to checkout or pay
    • User is providing personal information
    
    ═══════════════════════════════════════════════════════════════════
    INPUT FORMAT
    ═══════════════════════════════════════════════════════════════════
    Args:
        query (str): Search query in french. Use clear, concise terms.
                    Examples: "iPhone", "ustensils de cuisine", "t-shirt noir à 5000", "decoration"
                    Note: Always translate English queries to French before calling
                    
        limit (int): Maximum number of products to return (default: 10)
                    Recommended: 10 for general searches, 5 for specific queries
    
    ═══════════════════════════════════════════════════════════════════
    OUTPUT FORMAT
    ═══════════════════════════════════════════════════════════════════
    Returns:
        Dict[str, Any]: {
            "items": [
                {
                    "id": "prod_123",
                    "name": "Product Name",
                    "type": "product",
                    "brand": "Brand Name" or None,
                    "price": {
                        "amount": 29.99,
                        "currency": "EUR"
                    },
                    "categories": ["Category1", "Category2"],
                    "image_url": "https://...",
                    "short_description": "Brief description" or None,
                    "tags": ["tag1", "tag2"],
                    "keywords": ["keyword1", "keyword2"],
                    "sku": "SKU123" or None,
                    "meta": {
                        "source": "Qualiwo"
                    }
                },
                ...
            ],
            "totalFound": 15,
            "productsSummary": "Found 15 products for 'kitchen utensils':\n1. 'Spatula Set' - Orca déco - 19.99 EUR - Categories: Kitchen\n2. ..."
        }
    
    ═══════════════════════════════════════════════════════════════════
    IMPORTANT NOTES
    ═══════════════════════════════════════════════════════════════════
    1. ALWAYS check the "productsSummary" field to verify result relevance
    2. If totalFound is 0, inform the user no products were found
    3. If products don't match the query, be honest with the user
    4. The API call may fail - error handling is built-in
    5. Products are automatically normalized for frontend compatibility
    
    ═══════════════════════════════════════════════════════════════════
    USAGE EXAMPLES
    ═══════════════════════════════════════════════════════════════════
    
    Example 1 - Successful Search:
    product_search_tool(query="ustensils de cuisine", limit=5)
    {
        "items": [...],  # 5 kitchen products
        "totalFound": 12,
        "productsSummary": "Found 12 products for 'kitchen utensils':\n1. ..."
    }
    
    Example 2 - No Results:
     product_search_tool(query="t-shirt noir", limit=10)
    {
        "items": [],
        "totalFound": 0,
        "productsSummary": "No products found for 't-shirt noir'."
    }
    
    Example 3 - API Error:
     product_search_tool(query="smartphone de la marque Xiaomi", limit=10)
    {
        "items": [],
        "totalFound": 0,
        "productsSummary": "Error during search: Status 500"
    }
    """
    try:
        url = f"{QUALIWO_SEARCH_API_URL}/search"
        payload = {
            "query": query,
            "limit": limit
        }

        response = httpx.post(url, json=payload, timeout=10.0)

        if response.status_code != 200:
            return {
                "items": [],
                "totalFound": 0,
                "productsSummary": f"Error during search: Status {response.status_code}"
            }

        data = response.json()
        results = data.get("results", [])
        total_found = data.get("count", len(results))

        # Normalize products for frontend consistency
        normalized_products = []
        for p in results:
            normalized_p = p.copy()
            
            # Ensure product type
            normalized_p["type"] = "product"
            
            # Structure metadata
            if "meta" not in normalized_p or normalized_p["meta"] is None:
                normalized_p["meta"] = {}
            
            if "source" in normalized_p:
                normalized_p["meta"]["source"] = normalized_p.get("source") or "Qualiwo"
            
            # Set defaults for missing fields
            defaults = {
                "brand": None,
                "short_description": None,
                "tags": [],
                "keywords": [],
                "sku": None
            }
            for key, value in defaults.items():
                if key not in normalized_p:
                    normalized_p[key] = value
            
            normalized_products.append(normalized_p)

        # Generate AI-readable summary
        if not normalized_products:
            productsSummary = f'No products found for "{query}".'
        else:
            summary_lines = []
            for i, p in enumerate(normalized_products[:5]):  # Top 5 for summary
                brand = p.get("brand") or p.get("meta", {}).get("source") or "Unknown Brand"
                price_info = p.get("price", {})
                price = price_info.get("amount", "N/A")
                currency = price_info.get("currency", "EUR")
                categories = ", ".join(p.get("categories", ["N/A"]))
                summary_lines.append(
                    f'{i + 1}. "{p.get("name")}" - {brand} - {price} {currency} - Categories: {categories}'
                )
            productsSummary = f'Found {total_found} products for "{query}":\n' + "\n".join(summary_lines)

        return {
            "items": normalized_products,
            "totalFound": total_found,
            "productsSummary": productsSummary
        }

    except Exception as e:
        return {
            "items": [],
            "totalFound": 0,
            "productsSummary": f"Error during search: {str(e)}"
        }


@tool
async def show_cart_tool(config: RunnableConfig, action: str = "view") -> Dict[str, Any]:
    """
    Retrieve and display the user's shopping cart.
    
    ═══════════════════════════════════════════════════════════════════
    PURPOSE
    ═══════════════════════════════════════════════════════════════════
    This tool signals the frontend to display the user's shopping cart
    component with all items, quantities, and pricing information.
    
    ═══════════════════════════════════════════════════════════════════
    WHEN TO USE
    ═══════════════════════════════════════════════════════════════════
    Use this tool when:
    • User asks to see their cart: "show my cart", "voir mon panier"
    • User wants to review items: "what's in my cart?", "qu'est-ce qu'il y a dans mon panier?"
    • User wants to checkout: "I want to checkout", "je veux payer"
    
    ═══════════════════════════════════════════════════════════════════
    INPUT FORMAT
    ═══════════════════════════════════════════════════════════════════
    Args:
        action (str): Type of cart action to perform
                     Options: "view" | "checkout"
                     - "view": Simply display the cart
                     - "checkout": Display cart and prepare for payment flow
                     Default: "view"
    
    ═══════════════════════════════════════════════════════════════════
    OUTPUT FORMAT
    ═══════════════════════════════════════════════════════════════════
    Returns:
        Dict[str, Any]: {
            "showCart": true,           # Signals UI to display cart
            "action": "view",            # The action performed
            "message": "Displaying cart (action: view)",
            "items": [...]               # Actual items in cart
        }
    """
    try:
        user_id = config.get("configurable", {}).get("thread_id", "default")
        items = await cart_service.get_cart(user_id)
        
        return {
            "showCart": True,
            "action": action,
            "message": f"Displaying cart (action: {action})",
            "items": items
        }
    except Exception as e:
        return {
            "showCart": False,
            "action": action,
            "message": f"Error retrieving cart: {str(e)}"
        }


@tool
async def add_to_cart_tool(
    config: RunnableConfig, 
    product_id: str, 
    name: str,
    price: float,
    currency: str = "EUR",
    quantity: int = 1,
    image_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enregistre un produit dans le panier persistant de l'utilisateur.
    
    ═══════════════════════════════════════════════════════════════════
    PURPOSE
    ═══════════════════════════════════════════════════════════════════
    Cet outil sauvegarde les choix de l'utilisateur afin qu'ils soient
    accessibles sur mobile et web.
    
    ═══════════════════════════════════════════════════════════════════
    WHEN TO USE
    ═══════════════════════════════════════════════════════════════════
    Utilisez cet outil dès que l'utilisateur confirme vouloir acheter un
    produit spécifique (ex: "ajoute ça au panier", "je prends celui-là").
    
    ═══════════════════════════════════════════════════════════════════
    INPUT FORMAT
    ═══════════════════════════════════════════════════════════════════
    IMPORTANT: Récupérez ces informations depuis les résultats de product_search_tool.
    Args:
        product_id (str): Identifiant unique (ex: "prod_123")
        name (str): Nom complet du produit
        price (float): Montant du prix
        currency (str): Devise (Défaut: "EUR")
        quantity (int): Quantité à ajouter
        image_url (str, optional): URL de l'image principale
    """
    try:
        user_id = config.get("configurable", {}).get("thread_id", "default")
        
        product_data = {
            "id": product_id,
            "name": name,
            "price": price,
            "currency": currency,
            "image_url": image_url
        }
        
        success = await cart_service.add_to_cart(user_id, product_data, quantity)
        
        if success:
            return {
                "success": True,
                "message": f"Product {name} (quantity: {quantity}) added to cart",
                "product_id": product_id,
                "quantity": quantity
            }
        else:
            return {
                "success": False,
                "message": "Could not add product to cart database",
                "product_id": product_id
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error adding to cart: {str(e)}",
            "product_id": product_id,
            "quantity": quantity
        }


@tool
async def collect_user_info_tool(config: RunnableConfig, field: str, value: str) -> Dict[str, Any]:
    """
    Collect and validate user information required for checkout.
    
    ═══════════════════════════════════════════════════════════════════
    Args:
        field (str): "first_name" | "phone" | "email"
        value (str): The value to collect
    """
    try:
        user_id = config.get("configurable", {}).get("thread_id", "default")
        
        # Validation basique
        if field == "first_name" and len(value) < 2:
            return {"success": False, "message": "First name too short"}
        if field == "phone" and len(value) < 8:
            return {"success": False, "message": "Phone number too short"}
        
        # Sauvegarde persistante
        await user_service.save_user_info(user_id, field, value)
        
        return {
            "success": True,
            "field": field,
            "value": value,
            "message": f"Information collected: {field} = {value}"
        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


@tool
async def process_payment_tool(config: RunnableConfig, first_name: str, phone: str) -> Dict[str, Any]:
    """
    Process payment and complete the order.
    """
    try:
        user_id = config.get("configurable", {}).get("thread_id", "default")
        
        # 1. Sauvegarder les dernières infos
        await user_service.save_user_info(user_id, "first_name", first_name)
        await user_service.save_user_info(user_id, "phone", phone)
        
        # 2. Récupérer le panier pour la confirmation (facultatif mais pro)
        cart_items = await cart_service.get_cart(user_id)
        if not cart_items:
            return {"success": False, "message": "Le panier est vide."}

        # 3. Vider le panier après paiement réussi
        await cart_service.clear_cart(user_id)
        
        return {
            "success": True,
            "message": f"Paiement confirmé pour {first_name}",
            "payment_id": f"PAY_{first_name.upper()}_{int(time.time())}",
            "status": "completed"
        }
    except Exception as e:
        return {"success": False, "message": f"Erreur paiement: {str(e)}"}



# Liste de tous les outils pour l'agent
TOOLS = [
    product_search_tool,
    show_cart_tool,
    add_to_cart_tool,
    collect_user_info_tool,
    process_payment_tool
]
