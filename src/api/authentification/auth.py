import secrets
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
import jwt
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))


app = FastAPI(title="Assistant Python — API d'authentification")

# ── Stockage en mémoire ───────────────────────────────────────────────────────
# { username: hashed_password }
fake_users_db: dict[str, str] = {}

# ── création token JWT ───────────────────────────────────────────────────────
def _create_token(username: str) -> str:
    """Génère un JWT signé pour l'utilisateur."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Le 'payload' contient les données de l'utilisateur
    to_encode = {
        "sub": username,  # 'sub' est le standard pour le sujet (l'user)
        "exp": expire     # 'exp' est le standard pour l'expiration
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ── Schémas ───────────────────────────────────────────────────────────────────

class UserCredentials(BaseModel):
    username: str
    password: str


class User(BaseModel):
    username: str


# ── passeword management ───────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    """Hash minimaliste pour un contexte de démo (ne pas utiliser en prod)."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


# ── Dépendance d'authentification ─────────────────────────────────────────────

_bearer = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> User:
    token = credentials.credentials
    try:
        # On décode et vérifie la signature du token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        return User(username=username)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")


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