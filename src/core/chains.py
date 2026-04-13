from langchain_core.runnables import Runnable
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from src.core.llm import get_llm
from src.core.schemas import CodeAnalysisResult, GeneratedTestResult, TestExplanationResult
from src.prompts.prompts import (
    chat_prompt,
    code_analysis_prompt,
    test_explanation_prompt,
    test_generation_prompt,
)


# ── Chaîne d'analyse de code ─────────────────────────────────────────────────

def get_analysis_chain() -> Runnable:
    """
    Chaîne : prompt d'analyse → LLM avec sortie structurée (CodeAnalysisResult).
    Entrée attendue : {"code": str}
    """
    llm = get_llm()
    return code_analysis_prompt | llm.with_structured_output(CodeAnalysisResult)


# ── Chaîne de génération de tests ────────────────────────────────────────────

def get_test_chain() -> Runnable:
    """
    Chaîne : prompt de génération → LLM avec sortie structurée (GeneratedTestResult).
    Entrée attendue : {"code": str}
    """
    llm = get_llm()
    return test_generation_prompt | llm.with_structured_output(GeneratedTestResult)


# ── Chaîne d'explication de tests ────────────────────────────────────────────

def get_explain_test_chain() -> Runnable:
    """
    Chaîne : prompt d'explication → LLM avec sortie structurée (TestExplanationResult).
    Entrée attendue : {"test": str}
    """
    llm = get_llm()
    return test_explanation_prompt | llm.with_structured_output(TestExplanationResult)


# ── Agent de chat avec mémoire (LangGraph) ────────────────────────────────────

def _build_chat_agent() -> StateGraph:
    """
    Construit un graphe LangGraph pour le chat conversationnel avec mémoire persistante.
    La mémoire est gérée via MemorySaver et un thread_id passé dans la config.
    """
    llm = get_llm()

    def call_model(state: MessagesState):
        response = (chat_prompt | llm).invoke(state)
        return {"messages": [response]}

    graph = StateGraph(state_schema=MessagesState)
    graph.add_edge(START, "model")
    graph.add_node("model", call_model)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# Instance unique de l'agent de chat (partagée entre les requêtes)
_chat_agent = None


def get_chat_agent():
    """Retourne l'agent de chat (singleton)."""
    global _chat_agent
    if _chat_agent is None:
        _chat_agent = _build_chat_agent()
    return _chat_agent