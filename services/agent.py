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

# Utilisation forcée de l'agent Direct (Mistral) quel que soit l'environnement
logger.info("✨ Utilisation de l'agent Direct Mistral (agent_direct.py)")
try:
    from .agent_direct import agent_executor
except ImportError as e:
    logger.error(f"Erreur d'importation de agent_direct: {e}")
    raise e

# Export des constantes nécessaires au reste de l'application si besoin
from .prompts import SYSTEM_PROMPT as prompt
