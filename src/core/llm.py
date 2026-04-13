import os
 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
 
load_dotenv()
 
def get_llm() -> ChatOpenAI:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("La variable d'environnement GEMINI_API_KEY est manquante.")

    model_name = "gemini-2.5-flash"
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0,
    )
 

def get_llm2() -> ChatOpenAI:
    """Retourne le modèle LLM configuré depuis les variables d'environnement."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("La variable d'environnement OPENAI_API_KEY est manquante.")
 
    # CHAT_MODEL peut valoir "openAI:GPT-5-mini" → on extrait la partie après ":"
    raw_model = os.getenv("CHAT_MODEL", "openAI:gpt-4o-mini")
    model_name = raw_model.split(":")[-1]  # ex. "gpt-4o-mini"
 
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        temperature=0,
    )