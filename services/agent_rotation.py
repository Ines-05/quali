"""
Version "Rotation" de l'agent Qualiwo.
Utilise plusieurs clés API pour Gemini et OpenAI pour éviter les limites de quota en local.
"""

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from .tools import TOOLS
import os
import random
from dotenv import load_dotenv
import logging

load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_rotated_llm():
    """
    Initialise des modèles avec rotation de clés.
    Récupère les clés Google et OpenAI depuis l'environnement.
    Format attendu dans .env : 
    GOOGLE_API_KEY_1, GOOGLE_API_KEY_2...
    OPENAI_API_KEY_1, OPENAI_API_KEY_2...
    """
    
    # 1. Collecter toutes les clés disponibles
    google_keys = []
    openai_keys = []
    
    # Clés standards
    if os.getenv("GOOGLE_API_KEY"): google_keys.append(os.getenv("GOOGLE_API_KEY"))
    if os.getenv("OPENAI_API_KEY"): openai_keys.append(os.getenv("OPENAI_API_KEY"))
    
    # Clés indexées
    for i in range(1, 6):
        g_key = os.getenv(f"GOOGLE_API_KEY_{i}")
        o_key = os.getenv(f"OPENAI_API_KEY_{i}")
        if g_key: google_keys.append(g_key)
        if o_key: openai_keys.append(o_key)

    # Déduplication
    google_keys = list(set(google_keys))
    openai_keys = list(set(openai_keys))

    llm_instances = []

    # 2. Créer les instances Gemini
    for key in google_keys:
        try:
            llm_instances.append(ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=key,
                temperature=0.7
            ))
        except Exception as e:
            logger.warning(f"Impossible d'initialiser Gemini avec une clé : {e}")

    # 3. Créer les instances OpenAI
    for key in openai_keys:
        try:
            llm_instances.append(ChatOpenAI(
                model="gpt-4o-mini",
                api_key=key,
                temperature=0.7
            ))
        except Exception as e:
            logger.warning(f"Impossible d'initialiser OpenAI avec une clé : {e}")

    if not llm_instances:
        logger.error("❌ Aucune clé API valide trouvée pour la rotation.")
        return None

    # On mélange pour la rotation aléatoire au démarrage
    random.shuffle(llm_instances)
    
    # Le premier LLM est le principal, les autres sont des fallbacks
    primary_llm = llm_instances[0]
    fallbacks = llm_instances[1:]
    
    if fallbacks:
        logger.info(f"🚀 Rotation configurée avec {len(llm_instances)} instances (Gemini + OpenAI)")
        return primary_llm.with_fallbacks(fallbacks)
    else:
        logger.info("🚀 Une seule clé trouvée, utilisation directe.")
        return primary_llm

llm = get_rotated_llm()

if llm is None:
    raise RuntimeError("Échec de l'initialisation de l'agent avec rotation.")

from .prompts import SYSTEM_PROMPT

def create_qualiwo_agent_rotation():
    """
    Crée l'agent React avec rotation de clés
    """
    agent = create_react_agent(
        model=llm,
        tools=TOOLS,
        prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver()
    )
    return agent

agent_executor = create_qualiwo_agent_rotation()
