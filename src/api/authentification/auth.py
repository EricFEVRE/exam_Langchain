import secrets
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

app = FastAPI(title="Assistant Python — API d'authentification")

# ── Stockage en mémoire ───────────────────────────────────────────────────────
# { username: hashed_password }
fake_users_db: dict[str, str] = {}

# { token: username }
_tokens: dict[str, str] = {}

# ── Schémas ───────────────────────────────────────────────────────────────────

class UserCredentials(BaseModel):
    username: str
    password: str


class User(BaseModel):
    username: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    """Hash minimaliste pour un contexte de démo (ne pas utiliser en prod)."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def _create_token(username: str) -> str:
    token = secrets.token_hex(32)
    _tokens[token] = username
    return token


# ── Dépendance d'authentification ─────────────────────────────────────────────

_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> User:
    token = credentials.credentials
    username = _tokens.get(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré.",
        )
    return User(username=username)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/signup", response_model=User)
def signup(credentials: UserCredentials):
    """Crée un nouvel utilisateur. Rejette les doublons."""
    if credentials.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce nom d'utilisateur est déjà pris.",
        )
    fake_users_db[credentials.username] = _hash(credentials.password)
    return User(username=credentials.username)


@app.post("/login")
def login(credentials: UserCredentials):
    """Vérifie les identifiants et retourne un token Bearer."""
    stored = fake_users_db.get(credentials.username)
    if stored is None or stored != _hash(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects.",
        )
    token = _create_token(credentials.username)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me", response_model=User)
def me(current_user: User = Depends(get_current_user)):
    """Retourne l'utilisateur associé au token Bearer."""
    return current_user