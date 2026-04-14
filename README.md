# Examen LangChain : Assistant de Tests Unitaires Python

## points particuliers sur la solution retenue

### token JWT
la dépendance d'authentification entre l'API principale et l'API d'authentification se fait grâce à un token JWT, cela implique d'avoir dans .env un JWT_SECRET_KEY que l'on peut généré avec python -c "import secrets; print(secrets.token_urlsafe(32))"

### modèle
Le modèle choisi est openAI:gpt-5-nano ou openAI:gpt-5-nmini

### appli Strealit avec monitoring Langsmith
La connection à l'API REST de Langsmith est la partie la plus délicate, pour que cela fonctionne il faut :
1- une clé de type service qui commence par lsv2_sk et bien configurée sur le bon workspace
2- récupérer l'ID du projet, on la trouve dans l'URL lorsque l'on navigue dans Tracing sur l'interface LangSmith, c'est ce qui est juste après /projects/p/ dans "/projects/p/dc3aabe0-9b3e-466f-b62a-789b29f55f64"
3- optionnel, récupérer l'ORG_ID c'est ce qui est juste après https://smith.langchain.com/o/ dans cette même URL

## construction des chaines
Pour le chat, au lieu de le construire avec un agent langchain comme dans le cours, j'ai choisi de construire un graph LangGraph qui grâce à MessagesState gère nativement la mémoire avec checkpointer sans appel explicite (j'ai suivi les cours de LangChain academy en complément de ce cours)

## Structure du projet

```txt
exam_Langchain/
├── .env
├── .python-version
├── pyproject.toml
├── Makefile
├── docker-compose.yml
├── README.md
└── src/
    ├── api/
    │   ├── authentification/
    │   │   ├── Dockerfile.auth
    │   │   ├── requirements.txt
    │   │   └── auth.py
    │   └── assistant/
    │       ├── Dockerfile.main
    │       ├── requirements.txt
    │       └── main.py
    ├── core/
    │   ├── llm.py
    │   ├── chains.py
    │   └── schemas.py
    ├── ├
    ├── prompts/
    │   └── prompts.py
    ├── Dockerfile.streamlit
    ├── requirements.txt
    ├── app.py
    └── pages
        └── 2_langsmith.py

```

# Déploiement Docker — Guide

## Architecture des conteneurs

Le projet repose sur **4 services Docker** orchestrés par `docker-compose.yml` et un réseau bridge interne (`app_network`) :

| Service     | Dockerfile           | Port exposé | Rôle                                      |
|-------------|----------------------|-------------|-------------------------------------------|
| `auth`      | `Dockerfile.auth`    | `8001`      | API d'authentification (signup / login)   |
| `main`      | `Dockerfile.main`    | `8000`      | API principale (analyze, generate, chat…) |
| `streamlit` | `Dockerfile.streamlit` | `8501`    | Interface utilisateur (optionnelle)       |
| `tests`     | `Dockerfile.test`    | —           | Conteneur de tests d'intégration          |

---

## Configuration préalable

Créez un fichier `.env` à la racine du projet :

```env
OPENAI_API_KEY=sk-...
CHAT_MODEL=openai:gpt-4o-mini
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=**********
LANGCHAIN_PROJECT=exam_langchain
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_ORG_ID=******   # only for backup in langsmith monitoring in streamlit (should work without)
LANGCHAIN_PROJECT_ID=*****    # needed for langsmith monitoring in streamlit example : dc3aabe0-9b3e-466f-b62a-789b29f55f64
JWT_SECRET_KEY=*****   # example w_bt9weF-eg7EiNBmTQq8SWr3v-Df5JGVk36va2XK24
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=300
```

> **Ne commitez jamais ce fichier.** Ajoutez `.env` à votre `.gitignore`.

---

## Commandes Makefile

| Commande        | Effet                                                          |
|-----------------|----------------------------------------------------------------|
| `make`          | Build + lancement complet (auth, main, streamlit)             |
| `make up`       | Démarre les 3 services sans rebuild                           |
| `make down`     | Arrête et supprime les conteneurs                             |
| `make build`    | Build les images sans les démarrer                            |
| `make rebuild`  | Arrêt + rebuild + relance complète                            |
| `make logs`     | Affiche les logs en continu (50 dernières lignes)             |
| `make tests`    | Lance les tests d'intégration dans le conteneur `tests`       |

---

## Détail des Dockerfiles

### `Dockerfile.auth`
- Image de base : `python:3.12-slim`
- Installe `src/api/authentification/requirements.txt`
- Copie uniquement `auth.py`
- Lance : `uvicorn auth:app --host 0.0.0.0 --port 8001`

### `Dockerfile.main`
- Image de base : `python:3.12-slim`
- Installe `src/api/assistant/requirements.txt`
- Copie les modules partagés : `src/core/`, `src/memory/`, `src/prompts/`
- Copie `main.py` (entrypoint)
- Lance : `uvicorn main:app --host 0.0.0.0 --port 8000`

### `Dockerfile.streamlit`
- Image de base : `python:3.12-slim`
- Installe `src/requirements.txt`
- Copie `src/app.py`
- Lance : `streamlit run app.py --server.port=8501 --server.address=0.0.0.0`

### `Dockerfile.test`
- Image de base : `python:3.12-slim`
- Installe uniquement `pytest` et `requests`
- Copie `test_container_integration.py`
- Lance : `pytest test_container_integration.py -v`
- S'exécute **après** `auth` et `main` via `depends_on`

---

## Endpoints disponibles

### API Auth — `http://localhost:8001`

| Méthode | Route     | Description              |
|---------|-----------|--------------------------|
| POST    | `/signup` | Créer un utilisateur     |
| POST    | `/login`  | Connexion → JWT token    |

### API Main — `http://localhost:8000`

Tous les endpoints ci-dessous nécessitent un header :
```
Authorization: Bearer <token>
```

| Méthode | Route             | Description                                         |
|---------|-------------------|-----------------------------------------------------|
| POST    | `/analyze`        | Analyse un code Python                              |
| POST    | `/generate_test`  | Génère un test pytest pour une fonction             |
| POST    | `/explain_test`   | Explique un test de façon pédagogique               |
| POST    | `/full_pipeline`  | Enchaîne analyze → generate → explain               |
| POST    | `/chat`           | Conversation libre avec mémoire                     |
| GET     | `/history`        | Historique des échanges de l'utilisateur courant    |

### Interface Streamlit — `http://localhost:8501`

Interface graphique optionnelle permettant d'accéder à toutes les fonctionnalités ci-dessus.

---

## Lancement rapide

```bash
# 1. Cloner le projet
git clone <url-du-repo>
cd <nom-du-repo>

# 2. Configurer l'environnement
cp .env.example .env
# Éditez .env avec vos clés API

# 3. Lancer l'application complète
make

# 4. Lancer les tests d'intégration
make tests
```

---

## Dépannage

- **Port déjà utilisé** : vérifiez qu'aucun service local n'occupe les ports 8000, 8001 ou 8501.
- **Erreur d'auth dans `main`** : assurez-vous que le service `auth` est bien démarré (`make logs`).
- **Clé API manquante** : vérifiez que `.env` est bien présent à la racine et chargé via `env_file` dans `docker-compose.yml`.
- **Tests échoués** : exécutez `make logs` pour inspecter les erreurs de `auth` et `main` avant de relancer `make tests`.