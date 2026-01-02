"""
Version "Rotation" de l'agent Qualiwo.
Utilise plusieurs clés API pour Gemini et OpenAI pour éviter les limites de quota en local.
"""

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, SystemMessage
from typing import Annotated, Sequence, TypedDict
from langgraph.graph.message import add_messages
from .tools import TOOLS
import os
import random
from dotenv import load_dotenv
import logging

load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

def get_rotated_llm_with_tools():
    """
    Initialise des modèles avec rotation de clés et bind les outils.
    Récupère les clés Mistral, Google et OpenAI depuis l'environnement.
    """
    
    # 1. Collecter toutes les clés disponibles
    mistral_keys = []
    google_keys = []
    openai_keys = []
    
    # Clés standards
    if os.getenv("MISTRAL_API_KEY"): mistral_keys.append(os.getenv("MISTRAL_API_KEY"))
    if os.getenv("GOOGLE_API_KEY"): google_keys.append(os.getenv("GOOGLE_API_KEY"))
    if os.getenv("GEMINI_API_KEY"): google_keys.append(os.getenv("GEMINI_API_KEY"))
    if os.getenv("OPENAI_API_KEY"): openai_keys.append(os.getenv("OPENAI_API_KEY"))
    
    # Clés indexées
    for i in range(1, 6):
        m_key = os.getenv(f"MISTRAL_API_KEY_{i}")
        g_key = os.getenv(f"GOOGLE_API_KEY_{i}")
        o_key = os.getenv(f"OPENAI_API_KEY_{i}")
        if m_key: mistral_keys.append(m_key)
        if g_key: google_keys.append(g_key)
        if o_key: openai_keys.append(o_key)

    # Déduplication
    mistral_keys = list(set(mistral_keys))
    google_keys = list(set(google_keys))
    openai_keys = list(set(openai_keys))

    llm_instances = []

    # 2. Créer les instances Mistral (PRIORITAIRE)
    for key in mistral_keys:
        try:
            llm = ChatMistralAI(
                model="mistral-small-latest",
                api_key=key,
                temperature=0.7,
                timeout=60,
                max_retries=3
            )
            llm_instances.append(llm.bind_tools(TOOLS))
        except Exception as e:
            logger.warning(f"Impossible d'initialiser Mistral avec une clé : {e}")

    # 3. Créer les instances Gemini (SECONDAIRE)
    for key in google_keys:
        try:
            llm = ChatGoogleGenerativeAI(
                model="models/gemini-2.0-flash",
                google_api_key=key,
                temperature=0.7,
                timeout=60,
                max_retries=3
            )
            llm_instances.append(llm.bind_tools(TOOLS))
        except Exception as e:
            logger.warning(f"Impossible d'initialiser Gemini avec une clé : {e}")

    # 4. Créer les instances OpenAI (BACKUP)
    for key in openai_keys:
        try:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=key,
                temperature=0.7
            )
            llm_instances.append(llm.bind_tools(TOOLS))
        except Exception as e:
            logger.warning(f"Impossible d'initialiser OpenAI avec une clé : {e}")

    if not llm_instances:
        logger.error("❌ Aucune clé API valide trouvée pour la rotation.")
        return None

    # Le premier LLM est le principal, les autres sont des fallbacks
    primary_llm = llm_instances[0]
    fallbacks = llm_instances[1:]
    
    if fallbacks:
        logger.info(f"🚀 Rotation configurée avec {len(llm_instances)} instances (Mistral -> Gemini -> OpenAI)")
        return primary_llm.with_fallbacks(fallbacks)
    else:
        logger.info("🚀 Une seule clé trouvée, utilisation directe.")
        return primary_llm

llm_with_tools = get_rotated_llm_with_tools()

if llm_with_tools is None:
    raise RuntimeError("Échec de l'initialisation de l'agent avec rotation.")

from .prompts import SYSTEM_PROMPT

def create_qualiwo_agent_rotation():
    """
    Crée l'agent React avec rotation de clés manuellement pour éviter le bug de bind_tools sur Fallbacks
    """
    
    # Définition du noeud de l'agent
    def agent_node(state: AgentState):
        messages = list(state['messages'])
        
        # Ajouter le prompt système si c'est le premier message ou s'il n'est pas présent
        if not messages or not isinstance(messages[0], SystemMessage):
            messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))
            
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # Définition de la condition de continuation
    def should_continue(state: AgentState):
        messages = state['messages']
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    # Construction du graphe
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(TOOLS))
    
    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    
    workflow.add_edge("tools", "agent")
    
    return workflow.compile(checkpointer=MemorySaver())

agent_executor = create_qualiwo_agent_rotation()
