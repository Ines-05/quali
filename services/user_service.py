from typing import Dict, Any, Optional
from .database import Database
import time
import logging

logger = logging.getLogger(__name__)

# Fallback en mémoire
_in_memory_users: Dict[str, Dict[str, Any]] = {}

class UserService:
    @staticmethod
    async def save_user_info(user_id: str, field: str, value: str) -> bool:
        """Enregistre une information utilisateur (nom, téléphone, etc.)"""
        db = Database.get_db()
        
        if db is not None:
            try:
                await db.user.update_one(
                    {"user_id": user_id},
                    {"$set": {field: value, "updated_at": time.time()}, "$setOnInsert": {"created_at": time.time()}},
                    upsert=True
                )
                return True
            except Exception as e:
                logger.error(f"Erreur save_user_info MongoDB: {e}")

        # Fallback mémoire
        if user_id not in _in_memory_users:
            _in_memory_users[user_id] = {}
        
        _in_memory_users[user_id][field] = value
        return True

    @staticmethod
    async def get_user(user_id: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un utilisateur"""
        db = Database.get_db()
        if db is not None:
            try:
                return await db.user.find_one({"user_id": user_id})
            except Exception as e:
                logger.error(f"Erreur get_user MongoDB: {e}")
        
        return _in_memory_users.get(user_id)

user_service = UserService()
