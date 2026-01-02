"""
Version "Direct Mistral" de l'agent Qualiwo.
Utilisée en production pour éviter les timeouts liés aux rotations de clés/fallbacks.
"""

from langchain_mistralai import ChatMistralAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from .tools import TOOLS
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialiser le LLM Mistral directement
mistral_api_key = os.getenv("MISTRAL_API_KEY")

if not mistral_api_key:
    logger.error("❌ MISTRAL_API_KEY manquante dans l'environnement")
    raise RuntimeError("MISTRAL_API_KEY est requise pour le mode Direct Mistral.")

llm = ChatMistralAI(
    model="mistral-small-latest",
    api_key=mistral_api_key,
    temperature=0.7
)

logger.info("🚀 Agent Direct Mistral configuré (Production)")

from .prompts import SYSTEM_PROMPT

def create_qualiwo_agent_direct():
    """
    Crée l'agent React avec Mistral direct
    """
    agent = create_react_agent(
        model=llm,
        tools=TOOLS,
        prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver()
    )
    return agent

agent_executor = create_qualiwo_agent_direct()
