# QualiAPI - Agent IA Conversationnel

API FastAPI pour la logique conversationnelle et agentique de Qualiwo, utilisant LangChain et un agent React.

## Architecture

```
Qualiapi/
├── app.py               # Application FastAPI principale (entrypoint Vercel)
├── services/
│   ├── agent.py         # Configuration et initialisation de l'agent React
│   └── tools.py         # Outils (tools) disponibles pour l'agent
├── requirements.txt     # Dépendances Python
├── vercel.json          # Configuration déploiement Vercel
├── .env.example         # Variables d'environnement
└── README.md            # Ce fichier
```

## Fonctionnalités

- **Agent React LangChain** : Agent autonome capable d'analyser les intentions utilisateur et d'appeler les outils appropriés
- **Système de Fallback LLM** : 
  - **Primaire** : Google Gemini 2.5-flash-lite (ou version disponible la plus proche)
  - **Fallback** : OpenAI GPT-4o-mini (si Gemini échoue)
- **Outils Disponibles** :
  - `product_search_tool` : Recherche de produits
  - `show_cart_tool` : Affichage du panier
  - `add_to_cart_tool` : Ajout au panier
  - `collect_user_info_tool` : Collecte d'informations utilisateur
  - `process_payment_tool` : Traitement du paiement
  - `clarify_intent_tool` : Clarification des intentions vagues
- **Support Multilingue** : Français et Anglais
- **Streaming de Réponses** : Support du streaming pour les interfaces temps réel (en développement)

## Installation

### Prérequis
- Python 3.9+
- pip ou conda

### Setup

1. **Cloner et configurer** :
   ```bash
   cd Qualiapi
   python -m venv venv
   source venv/bin/activate  # Ou venv\Scripts\activate sur Windows
   ```

2. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurer les variables d'environnement** :
   ```bash
   cp .env.example .env
   # Éditer .env avec vos clés API
   ```

### Variables d'Environnement Requises

```
# Google Gemini API Key (priorité - modèle principal)
GOOGLE_API_KEY=sk-...

# OpenAI API Key (fallback)
OPENAI_API_KEY=sk-...

# URLs des APIs externes
QUALIWO_SEARCH_API_URL=https://qualiwo-search-api.vercel.app
CORS_ORIGINS=*
PORT=8000
```

## Exécution Locale

```bash
python app.py
```

L'API sera disponible sur `http://localhost:8000`

Accéder à la documentation interactive :
- Swagger UI : `http://localhost:8000/docs`
- ReDoc : `http://localhost:8000/redoc`

## Endpoints

### `GET /`
Bienvenue et informations de l'API

### `GET /health`
Vérification de santé

### `POST /chat`
**Endpoint conversationnel principal**

**Requête** :
```json
{
  "message": "Je veux un iPhone",
  "session_id": "optional_session_id",
  "conversation_history": [
    {"role": "user", "content": "Bonjour"},
    {"role": "assistant", "content": "Bonjour!"}
  ]
}
```

**Réponse** :
```json
{
  "message": "Voici les iPhones disponibles...",
  "ui_action": {
    "type": "RENDER_PRODUCTS",
    "data": {"products": [...]}
  },
  "session_id": "optional_session_id"
}
```

### `POST /chat/stream`
Endpoint streaming (en développement)

## Déploiement sur Vercel

### Configuration
L'application utilise la structure recommandée par Vercel pour FastAPI :
- Entrypoint : `app.py` (contient l'instance FastAPI `app`)
- Configuration : `vercel.json`

### Déploiement

1. **Pousser vers Git** :
   ```bash
   git add .
   git commit -m "Deploy QualiAPI"
   git push
   ```

2. **Déployer sur Vercel** :
   ```bash
   vercel --prod
   ```

3. **Configurer les variables d'environnement** dans Vercel Dashboard :
   - `OPENAI_API_KEY`
   - `QUALIWO_SEARCH_API_URL`
   - `INES_SEMANTIC_API_URL`

### Points Importants
- Vercel cherche automatiquement `app.py` comme entrypoint
- Les variables d'environnement doivent être configurées dans le dashboard Vercel
- Timeouts : Vercel a un timeout de 60s pour les requêtes (à considérer pour les opérations longues)

## Développement

### Ajouter un Nouvel Outil

Dans `tools.py`, ajouter une fonction décorée avec `@tool` :

```python
@tool
def new_tool(param1: str) -> Dict[str, Any]:
    """Description du tool"""
    # Implémentation
    return {"result": "..."}
```

Puis ajouter le tool à la liste `TOOLS` en fin du fichier.

### Modifier le Prompt Système

Éditer la variable `SYSTEM_PROMPT` dans `agent.py` pour changer le comportement de l'agent.

### Diagnostiquer les Modèles LLM

Utilisez le script de diagnostic pour vérifier l'état des modèles :

```bash
python diagnose_llm.py
```

Ce script teste automatiquement :
- La présence des clés API
- La connectivité de chaque modèle
- Le modèle effectivement chargé

## Architecture des Outils

### Recherche de Produits : API vs Logique Locale

**Décision actuelle : Appel API externe**

Le `product_search_tool` fait un appel vers l'API Qualiwo Search (`https://qualiwo-search-api.vercel.app/api/search`).

**Raisonnement :**
- ✅ **Séparation des préoccupations** : Logique de recherche isolée et réutilisable
- ✅ **Évolutivité** : Possibilité de mettre à jour l'algorithme de recherche sans redéployer l'agent
- ✅ **Performance** : L'API peut être optimisée indépendamment (cache, indexation, etc.)
- ✅ **Testabilité** : Logique de recherche testable séparément
- ⚠️ **Dépendance réseau** : Risque de panne si l'API est indisponible

**Alternative future : Logique locale**
Une fonction `local_product_search()` est préparée dans `tools.py` pour montrer comment implémenter une recherche locale si nécessaire.

**Migration future :**
```python
# Dans product_search_tool, remplacer :
response = httpx.get(url, ...)
# Par :
result = local_product_search(query, limit)
```

## Système de Fallback LLM

L'application utilise un système de fallback intelligent pour les modèles LLM :

### Priorité des Modèles
1. **Google Gemini 2.5-flash-lite** (ou version disponible la plus proche)
   - Avantages : Rapide, économique, bonnes performances générales
   - Utilisé si `GOOGLE_API_KEY` est configurée et fonctionnelle

2. **OpenAI GPT-4o-mini** (fallback)
   - Utilisé si Gemini n'est pas disponible ou échoue
   - Garantit la continuité du service

### Logique de Fallback
- Au démarrage de l'application, le système teste automatiquement Gemini
- Si Gemini fonctionne : utilisation de Gemini
- Si Gemini échoue : basculement automatique vers OpenAI
- Logging détaillé pour tracer les changements de modèle
- Test de connectivité à chaque initialisation

### Configuration
Configurez les deux clés API pour une redondance maximale :
```bash
GOOGLE_API_KEY=votre_clé_google
OPENAI_API_KEY=votre_clé_openai
```

## Logging et Débogage

L'agent s'exécute en mode `verbose=True` par défaut, ce qui affiche les étapes d'exécution.

Pour désactiver, éditer `agent.py` :
```python
agent_executor = AgentExecutor(
    ...
    verbose=False,  # Changer à False
    ...
)
```

## Prochaines Étapes

- [ ] Implémenter le streaming de réponses
- [ ] Ajouter la persistance en base de données
- [ ] Intégrer avec LangGraph pour des workflows plus complexes
- [ ] Ajouter la gestion de sessions utilisateur
- [ ] Implémenter le système de paiement réel
- [ ] Ajouter des tests unitaires

## Support

Pour toute question ou problème, consulter `../README_WORKFLOW.md` pour la logique métier.
