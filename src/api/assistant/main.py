
import httpx
import os
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from src.core.chains import (
    get_analysis_chain,
    get_chat_agent,
    get_explain_test_chain,
    get_test_chain,
)
from src.memory import memory

# ── vérification de l'authentification───────────────────────────────────────────
# On définit le schéma localement pour que l'API sache à quoi ressemble un User
class User(BaseModel):
    username: str

_bearer = HTTPBearer()

AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8001") # Local par défaut, Docker sinon

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer)
) -> User:
    token = credentials.credentials
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{AUTH_URL}/me",
                headers={"Authorization": f"Bearer {token}"}
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Le service d'authentification est injoignable."
            )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré (vérifié par Auth-API)."
        )
    
    # Si OK, on transforme le JSON reçu en objet User
    data = response.json()
    return User(username=data["username"])


# ── API principale ─────────────────────────────────────────────────────────────
app = FastAPI(title="Assistant Python — API principale")


# ── Schémas de requête ────────────────────────────────────────────────────────

class CodeRequest(BaseModel):
    code: str


class ChatRequest(BaseModel):
    input: str


# ── /analyze ──────────────────────────────────────────────────────────────────

@app.post("/analyze")
def analyze(
    request: CodeRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyse un code Python et renvoie un résultat structuré."""
    try:
        result = get_analysis_chain().invoke({"code": request.code})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    data = result.model_dump()
    memory.add_to_history(current_user.username, {"type": "analyze", **data})
    return data


# ── /generate_test ────────────────────────────────────────────────────────────

@app.post("/generate_test")
def generate_test(
    request: CodeRequest,
    current_user: User = Depends(get_current_user),
):
    """Génère un test unitaire pytest pour le code fourni."""
    try:
        result = get_test_chain().invoke({"code": request.code})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    data = result.model_dump()
    memory.add_to_history(current_user.username, {"type": "generate_test", **data})
    return data


# ── /explain_test ─────────────────────────────────────────────────────────────

@app.post("/explain_test")
def explain_test(
    request: CodeRequest,
    current_user: User = Depends(get_current_user),
):
    """Explique de façon pédagogique un test unitaire Python."""
    try:
        result = get_explain_test_chain().invoke({"test": request.code})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    data = result.model_dump()
    memory.add_to_history(current_user.username, {"type": "explain_test", **data})
    return data


# ── /full_pipeline ────────────────────────────────────────────────────────────

@app.post("/full_pipeline")
def full_pipeline(
    request: CodeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Pipeline complet :
    1. Analyse le code.
    2. Si non optimal → s'arrête et renvoie l'analyse + message d'erreur.
    3. Sinon → génère un test unitaire.
    4. Puis explique ce test.
    """
    # Étape 1 — Analyse
    try:
        analysis = get_analysis_chain().invoke({"code": request.code})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse : {e}")

    analysis_data = analysis.model_dump()
    memory.add_to_history(
        current_user.username, {"type": "full_pipeline_analysis", **analysis_data}
    )

    # Étape 2 — Arrêt si code non optimal
    if not analysis.is_optimal:
        return {"error": "Code non optimal", "analysis": analysis_data}

    # Étape 3 — Génération du test
    try:
        test_result = get_test_chain().invoke({"code": request.code})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur génération test : {e}")

    test_data = test_result.model_dump()

    # Étape 4 — Explication du test
    try:
        explanation_result = get_explain_test_chain().invoke(
            {"test": test_result.unit_test}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur explication : {e}")

    explanation_data = explanation_result.model_dump()

    memory.add_to_history(
        current_user.username,
        {
            "type": "full_pipeline",
            "analysis": analysis_data,
            "test": test_data,
            "explanation": explanation_data,
        },
    )

    return {
        "analysis": analysis_data,
        "test": test_data,
        "explanation": explanation_data,
    }


# ── /chat ─────────────────────────────────────────────────────────────────────

@app.post("/chat")
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Conversation libre avec mémoire.
    Le thread_id est le username : chaque utilisateur a son propre historique LangGraph.
    """
    try:
        result = get_chat_agent().invoke(
            {"messages": [{"role": "user", "content": request.input}]},
            config={"configurable": {"thread_id": current_user.username}},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    response_text = result["messages"][-1].content

    # On enregistre le message user puis la réponse dans l'historique applicatif
    memory.add_to_history(
        current_user.username, {"content": request.input, "role": "user"}
    )
    memory.add_to_history(
        current_user.username, {"content": response_text, "role": "assistant"}
    )

    return {"response": response_text}


# ── /history ──────────────────────────────────────────────────────────────────

@app.get("/history")
def get_history(current_user: User = Depends(get_current_user)):
    """Retourne l'historique applicatif de l'utilisateur courant."""
    return {"history": memory.get_history(current_user.username)}