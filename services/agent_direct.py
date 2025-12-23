"""
Version "Direct OpenAI" de l'agent Qualiwo.
Utilisée en production pour éviter les timeouts liés aux rotations de clés/fallbacks.
"""

from langchain_openai import ChatOpenAI
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

# Initialiser le LLM OpenAI directement
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    logger.error("❌ OPENAI_API_KEY manquante dans l'environnement")
    raise RuntimeError("OPENAI_API_KEY est requise pour le mode Direct OpenAI.")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=openai_api_key,
    temperature=0.7
)

logger.info("🚀 Agent Direct OpenAI configuré (Production)")

from .prompts import SYSTEM_PROMPT

def create_qualiwo_agent_direct():
    """
    Crée l'agent React avec OpenAI direct
    """
    agent = create_react_agent(
        model=llm,
        tools=TOOLS,
        prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver()
    )
    return agent

agent_executor = create_qualiwo_agent_direct()
