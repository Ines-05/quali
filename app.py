"""
Application FastAPI principale pour Qualiwo
Déploiement compatible Vercel
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Any, Union
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, ToolMessage
from services.agent import agent_executor
from services.tools import TOOLS
from services.database import db
from contextlib import asynccontextmanager
import json

load_dotenv()

# ============================================================================
# Événements de démarrage/arrêt (Lifespan)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application"""
    # Démarrage
    await db.connect_db()
    print("✓ QualiAPI démarrée")
    print("✓ Agent LangGraph initialisé")
    print("✓ Outils disponibles :")
    for tool in TOOLS:
        print(f"  - {tool.name}")
    
    yield
    
    # Arrêt
    await db.close_db()
    print("✓ QualiAPI arrêtée")


# Initialiser l'application FastAPI
app = FastAPI(
    title="QualiAPI - Qualiwo Shopping Assistant",
    description="API conversationnelle avec agent IA pour l'e-commerce Qualiwo",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS (à restreindre en production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware pour mesurer la latence
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    print(f"⏱️ Latence pour {request.url.path}: {process_time:.4f}s")
    return response

# ============================================================================
# Modèles Pydantic
# ============================================================================

class Message(BaseModel):
    """Modèle pour un message dans la conversation"""
    role: str  # "user" ou "assistant"
    content: str


class ChatRequest(BaseModel):
    """Requête pour l'endpoint /chat"""
    message: str
    session_id: Optional[str] = None
    conversation_history: Optional[List[Message]] = None


class UIAction(BaseModel):
    """Actions UI que le frontend peut exécuter"""
    type: str  # "NONE", "RENDER_PRODUCTS", "RENDER_CART", "REQUEST_INFO"
    data: Optional[Any] = None


class ChatResponse(BaseModel):
    """Réponse de l'agent"""
    message: str
    ui_action: UIAction
    session_id: Optional[str] = None


# ============================================================================
# Routes
# ============================================================================

@app.get("/")
async def root():
    """Route de bienvenue"""
    return {
        "message": "Bienvenue sur QualiAPI - Qualiwo Shopping Assistant",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Vérification de santé de l'API"""
    return {
        "status": "healthy",
        "service": "QualiAPI",
        "agent_loaded": agent_executor is not None
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Endpoint conversationnel principal
    
    L'agent reçoit le message de l'utilisateur, analyse son intention,
    appelle les outils nécessaires, et retourne une réponse avec
    instructions d'affichage UI.
    
    Args:
        request: ChatRequest contenant le message et l'historique de conversation
    
    Returns:
        ChatResponse avec le message de l'agent et les actions UI
    
    Raises:
        HTTPException: Si une erreur se produit lors du traitement
    """
    try:
        # Validation du message
        if not request.message or len(request.message.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Le message ne peut pas être vide"
            )
        
        # Construire le contexte de conversation
        # TODO: Gérer l'historique de conversation pour le contexte
        conversation_context = ""
        if request.conversation_history:
            for msg in request.conversation_history[-10:]:  # Derniers 10 messages
                conversation_context += f"{msg.role}: {msg.content}\n"
        
        # Exécuter l'agent LangGraph
        # Préparer les messages pour LangGraph
        
        messages = [HumanMessage(content=request.message)]
        
        # Configuration pour la mémoire (thread_id basé sur session_id)
        config = {"configurable": {"thread_id": request.session_id or "default"}}
        
        # Exécuter l'agent
        start_agent = time.time()
        result = await agent_executor.ainvoke({"messages": messages}, config=config)
        agent_duration = time.time() - start_agent
        print(f"🤖 Agent execution took: {agent_duration:.4f}s")
        
        # Extraire la réponse du dernier message AI
        agent_output = ""
        if result["messages"]:
            last_message = result["messages"][-1]
            agent_output = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        # Détecter les actions UI basées sur les outils appelés dans les messages
        ui_action_type = "NONE"
        ui_data = None

        # --- LOGIQUE DE PARSING JSON ---
        # Le prompt demande à l'agent de répondre en JSON. On tente de l'extraire pour le frontend.
        try:
            # Nettoyage des éventuels blocs de code markdown
            cleaned_output = agent_output.strip()
            if cleaned_output.startswith("```json"):
                cleaned_output = cleaned_output[7:].split("```")[0].strip()
            elif cleaned_output.startswith("```"):
                cleaned_output = cleaned_output[3:].split("```")[0].strip()
            
            # Parser le JSON
            parsed_json = json.loads(cleaned_output)
            
            if isinstance(parsed_json, dict):
                # Extraire le message propre
                if "message" in parsed_json:
                    agent_output = parsed_json["message"]
                
                # Extraire l'action UI si présente
                if "ui_action" in parsed_json and parsed_json["ui_action"] != "NONE":
                    ui_action_type = parsed_json["ui_action"]
                
                # Extraire les données si présentes
                if "data" in parsed_json and parsed_json["data"]:
                    ui_data = parsed_json["data"]
        except Exception as e:
            # Si ce n'est pas du JSON, on garde l'agent_output tel quel
            # Cela arrive si l'agent ne suit pas parfaitement le format
            pass
        
        # --- LOGIQUE DE DÉTECTION PAR OUTILS ---
        # On complète/écrase avec les infos issues des appels d'outils réels
        # (plus fiable pour les données comme les listes de produits)
        
        # Mapping pour relier les réponses d'outils aux appels
        tool_calls_map = {}
        
        # 1. Identifier les appels d'outils et définir le type d'action
        for message in result["messages"]:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_id = tool_call.get('id')
                    tool_name = tool_call.get('name', '')
                    if tool_id:
                        tool_calls_map[tool_id] = tool_name
                    
                    if tool_name == "product_search_tool":
                        ui_action_type = "RENDER_PRODUCTS"
                    elif tool_name == "show_cart_tool":
                        ui_action_type = "RENDER_CART"
                    elif tool_name == "collect_user_info_tool":
                        ui_action_type = "REQUEST_INFO"
                    elif tool_name == "process_payment_tool":
                        ui_action_type = "RENDER_PAYMENT"

        # 2. Récupérer les données des ToolMessages
        for message in result["messages"]:
            if isinstance(message, ToolMessage):
                tool_name = tool_calls_map.get(message.tool_call_id)
                
                if tool_name == "product_search_tool":
                    try:
                        content = message.content
                        data = content
                        if isinstance(content, str):
                            try:
                                data = json.loads(content)
                            except:
                                pass
                        
                        if isinstance(data, dict) and "items" in data:
                            ui_data = data["items"]
                    except Exception as e:
                        print(f"Erreur parsing product_search_tool: {e}")
                        
                elif tool_name == "show_cart_tool":
                    try:
                        content = message.content
                        data = content
                        if isinstance(content, str):
                            try:
                                data = json.loads(content)
                            except:
                                pass
                        ui_data = data
                    except Exception as e:
                        print(f"Erreur parsing show_cart_tool: {e}")

                elif tool_name == "process_payment_tool":
                    try:
                        content = message.content
                        data = content
                        if isinstance(content, str):
                            try:
                                data = json.loads(content)
                            except:
                                pass
                        ui_data = data
                    except Exception as e:
                        print(f"Erreur parsing process_payment_tool: {e}")
        
        # Construire la réponse
        response = ChatResponse(
            message=agent_output,
            ui_action=UIAction(type=ui_action_type, data=ui_data),
            session_id=request.session_id
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement du message : {str(e)}"
        )


from fastapi.responses import StreamingResponse
import asyncio

@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Endpoint pour le streaming de réponses via Server-Sent Events (SSE)
    """
    if not request.message or len(request.message.strip()) == 0:
        raise HTTPException(status_code=400, detail="Le message ne peut pas être vide")

    messages = [HumanMessage(content=request.message)]
    config = {"configurable": {"thread_id": request.session_id or "default"}}

    async def event_generator():
        try:
            # On utilise astream pour récupérer les chunks en temps réel
            # Note: Avec create_react_agent, on reçoit des updates d'état
            async for event in agent_executor.astream_events(
                {"messages": messages}, 
                config=config,
                version="v2"
            ):
                kind = event["event"]
                
                # On stream les tokens générés par le LLM (content)
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield f"data: {json.dumps({'type': 'content', 'value': content})}\n\n"
                
                # On peut aussi streamer les débuts d'appels d'outils pour l'UX
                elif kind == "on_tool_start":
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': event['name']})}\n\n"
                    
                elif kind == "on_tool_end":
                    # On pourrait envoyer les résultats partiels ici
                    pass

            yield "data: [DONE]\n\n"
        except Exception as e:
            error_msg = f"Erreur streaming: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'value': error_msg})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler personnalisé pour les exceptions HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handler pour les exceptions générales"""
    return JSONResponse(
        status_code=500,
        content={"error": "Erreur interne du serveur", "status_code": 500}
    )


# ============================================================================
# Pour Vercel - Export du handler ASGI
# ============================================================================
# Vercel cherche automatiquement l'instance FastAPI nommée 'app'
# C'est ce qui est utilisé pour gérer les requêtes sur Vercel

if __name__ == "__main__":
    import uvicorn
    
    # Pour développement local
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
