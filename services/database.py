import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect_db(cls):
        """Initialise la connexion à MongoDB"""
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            logger.warning("⚠️ MONGODB_URI non trouvée dans .env. Utilisation de la mémoire temporaire.")
            return

        try:
            cls.client = AsyncIOMotorClient(mongo_uri)
            cls.db = cls.client.get_database("Qualiwo")
            # Vérifier la connexion
            await cls.client.admin.command('ping')
            logger.info("✅ Connecté à MongoDB")
        except Exception as e:
            logger.error(f"❌ Erreur de connexion à MongoDB : {e}")
            cls.client = None
            cls.db = None

    @classmethod
    async def close_db(cls):
        """Ferme la connexion à MongoDB"""
        if cls.client:
            cls.client.close()
            logger.info("🔒 Connexion MongoDB fermée")

    @classmethod
    def get_db(cls):
        return cls.db

# Instance globale pour le service
db = Database()
