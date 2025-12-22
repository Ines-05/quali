from typing import List, Dict, Any, Optional
from .database import Database
import time
import logging

logger = logging.getLogger(__name__)

# Fallback en mémoire si MongoDB n'est pas dispo
_in_memory_carts: Dict[str, List[Dict[str, Any]]] = {}

class CartService:
    @staticmethod
    async def get_cart(user_id: str) -> List[Dict[str, Any]]:
        """Récupère le panier d'un utilisateur par son session_id / user_id"""
        db = Database.get_db()
        if db is not None:
            try:
                cart = await db.carts.find_one({"user_id": user_id})
                if cart:
                    return cart.get("items", [])
            except Exception as e:
                logger.error(f"Erreur get_cart MongoDB: {e}")
        
        return _in_memory_carts.get(user_id, [])

    @staticmethod
    async def add_to_cart(user_id: str, product: Dict[str, Any], quantity: int = 1) -> bool:
        """Ajoute un produit au panier"""
        db = Database.get_db()
        
        # Préparer l'item
        item = {
            "id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "image": product.get("image_url") or (product.get("images", {}).get("main") if isinstance(product.get("images"), dict) else None),
            "quantity": quantity,
            "added_at": time.time()
        }

        if db is not None:
            try:
                # Chercher si le produit est déjà là
                existing_cart = await db.carts.find_one({"user_id": user_id})
                if existing_cart:
                    items = existing_cart.get("items", [])
                    # Mettre à jour la quantité si existe
                    found = False
                    for i in items:
                        if i["id"] == item["id"]:
                            i["quantity"] += quantity
                            found = True
                            break
                    
                    if not found:
                        items.append(item)
                    
                    await db.carts.update_one(
                        {"user_id": user_id},
                        {"$set": {"items": items, "updated_at": time.time()}}
                    )
                else:
                    await db.carts.insert_one({
                        "user_id": user_id,
                        "items": [item],
                        "created_at": time.time(),
                        "updated_at": time.time()
                    })
                return True
            except Exception as e:
                logger.error(f"Erreur add_to_cart MongoDB: {e}")

        # Fallback mémoire
        if user_id not in _in_memory_carts:
            _in_memory_carts[user_id] = []
        
        items = _in_memory_carts[user_id]
        for i in items:
            if i["id"] == item["id"]:
                i["quantity"] += quantity
                return True
        
        items.append(item)
        return True

    @staticmethod
    async def clear_cart(user_id: str) -> bool:
        """Vide le panier"""
        db = Database.get_db()
        if db is not None:
            try:
                await db.carts.delete_one({"user_id": user_id})
                return True
            except Exception as e:
                logger.error(f"Erreur clear_cart MongoDB: {e}")
        
        if user_id in _in_memory_carts:
            _in_memory_carts[user_id] = []
        return True

cart_service = CartService()
