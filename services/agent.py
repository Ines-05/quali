"""
Fichier principal de l'agent Qualiwo.
Sert de commutateur entre le mode 'Rotation' (local) et 'Direct OpenAI' (production).
"""

import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Déterminer le mode d'exécution
# On utilise Direct OpenAI si :
# 1. ENVIRONMENT == 'production'
# 2. VERCEL == '1' (déploiement Vercel)
# 3. AGENT_MODE == 'direct'
IS_PRODUCTION = (
    os.getenv("ENVIRONMENT") == "production" or 
    os.getenv("VERCEL") == "1" or 
    os.getenv("AGENT_MODE") == "direct"
)

if IS_PRODUCTION:
    logger.info("✨ Mode PRODUCTION détecté : Utilisation de l'agent Direct OpenAI (sans fallback)")
    try:
        from .agent_direct import agent_executor
    except ImportError as e:
        logger.error(f"Erreur d'importation de agent_direct: {e}")
        # Fallback de secours si le fichier manque
        from .agent_rotation import agent_executor
else:
    logger.info("🔄 Mode LOCAL détecté : Utilisation de l'agent avec Rotation et Fallback")
    from .agent_rotation import agent_executor

# Export des constantes nécessaires au reste de l'application si besoin
from .prompts import SYSTEM_PROMPT as prompt
