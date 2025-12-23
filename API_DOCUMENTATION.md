# QualiAPI Documentation

Cette documentation décrit les points d'entrée (endpoints) de l'API QualiAPI, conçue pour alimenter l'assistant de shopping Qualiwo sur le web et le mobile.

## Base URL
Local : `http://localhost:8000`
Production : `[URL_VERCEL_OU_AUTRE]`

---

## 1. Chat Principal
Endpoint central pour l'interaction conversationnelle avec l'agent IA.

### Endpoint
*   **URL** : `/chat`
*   **Méthode** : `POST`
*   **Content-Type** : `application/json`

### Request Body
| Champ | Type | Obligatoire | Description |
| :--- | :--- | :--- | :--- |
| `message` | `string` | Oui | Le message envoyé par l'utilisateur. |
| `session_id` | `string` | Non | ID unique pour maintenir le contexte de la conversation (mémoire). |
| `conversation_history` | `array` | Non | Liste des messages précédents (Optionnel si `session_id` est utilisé pour la mémoire serveur). |

**Structure de `conversation_history` (objet Message) :**
```json
{
  "role": "user" | "assistant",
  "content": "Texte du message"
}
```

**Exemple de Requête :**
```json
{
  "message": "Je cherche une robe rouge",
  "session_id": "user-123-abc"
}
```

### Response Body
| Champ | Type | Description |
| :--- | :--- | :--- |
| `message` | `string` | La réponse textuelle propre de l'assistant à afficher à l'utilisateur. |
| `session_id` | `string` | Rappel de l'ID de session utilisé. |
| `ui_action` | `object` | Instructions pour le frontend sur quel composant afficher. |

**Structure de `ui_action` :**
```json
{
  "type": "NONE" | "RENDER_PRODUCTS" | "RENDER_CART" | "REQUEST_INFO" | "RENDER_PAYMENT",
  "data": any | null
}
```

### Détails des types d'actions (`ui_action.type`)

#### 1. `NONE`
Afficher simplement le texte reçu dans `message`.

#### 2. `RENDER_PRODUCTS`
L'utilisateur a fait une recherche. `data` contient une liste de produits.
*   **data** : `Array<Product>`
```json
{
  "message": "Voici ce que j'ai trouvé :",
  "ui_action": {
    "type": "RENDER_PRODUCTS",
    "data": [
      {
        "id": "prod_1",
        "name": "Robe d'été",
        "price": { "amount": 45, "currency": "EUR" },
        "brand": "Massimo Dutti",
        "categories": ["Vêtements"],
        "type": "product",
        "meta": { "source": "Qualiwo" }
        // ... autres champs optionnels (images, short_description, etc.)
      }
    ]
  }
}
```

#### 3. `RENDER_CART`
Afficher le résumé du panier ou initier le checkout.
*   **data** : `{ "showCart": true, "message": "...", "action": "view" | "checkout" }`

#### 4. `RENDER_PAYMENT`
Le paiement a été initié ou complété.
*   **data** : `{ "success": true, "status": "completed", "payment_id": "..." }`

#### 5. `REQUEST_INFO`
L'agent demande une information manquante (ex: téléphone pour le paiement).
*   **data** : `{ "field": "phone", "value": "..." }`

---

---

## 2. Chat Streaming
Point d'entrée pour recevoir la réponse de l'agent en temps réel via Server-Sent Events (SSE). Utile pour améliorer la réactivité perçue par l'utilisateur.

### Endpoint
*   **URL** : `/chat/stream`
*   **Méthode** : `POST`
*   **Content-Type** : `application/json`
*   **Accept** : `text/event-stream`

### Request Body
Identique au point d'entrée `/chat`.

### Response (SSE)
Le serveur renvoie un flux d'événements (stream) au format `data: { ... }\n\n`.

#### Types d'événements :

| Type | Description |
| :--- | :--- |
| `content` | Un fragment de texte du message de l'assistant. |
| `tool_start` | Indique que l'agent commence l'exécution d'un outil (ex: `product_search_tool`). |
| `error` | Envoyé en cas d'erreur durant la génération. |
| `[DONE]` | Signal de fin de stream (indique que la connexion peut être fermée). |

**Exemple de flux :**
```text
data: {"type": "content", "value": "Bonjour ! "}

data: {"type": "tool_start", "tool": "product_search_tool"}

data: {"type": "content", "value": "Je cherche les meilleurs articles pour vous..."}

data: [DONE]
```

---

## 3. Health Check
Vérifier l'état de santé de l'API.

### Endpoint
*   **URL** : `/health`
*   **Méthode** : `GET`

### Response Body
```json
{
  "status": "healthy",
  "service": "QualiAPI",
  "agent_loaded": true
}
```

---

## 4. Modèles de Données

### Objet Product
| Champ | Type | Description |
| :--- | :--- | :--- |
| `id` | `string` | Identifiant unique du produit. |
| `name` | `string` | Nom complet du produit. |
| `brand` | `string` | Marque (ex: "Orca", "Massimo Dutti"). |
| `price` | `object` | Contient `amount` (number) et `currency` (string). |
| `categories` | `array` | Liste des catégories. |
| `images` | `array` | Liste d'URLs vers les images du produit. |
| `type` | `string` | Toujours "product". |
| `meta` | `object` | Métadonnées additionnelles (ex: source). |
