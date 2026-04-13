from collections import defaultdict
from typing import Any
 
# Dictionnaire global : username → liste d'entrées d'historique
_history: dict[str, list[dict[str, Any]]] = defaultdict(list)
 
 
def add_to_history(username: str, entry: dict[str, Any]) -> None:
    """Ajoute une entrée dans l'historique de l'utilisateur."""
    _history[username].append(entry)
 
 
def get_history(username: str) -> list[dict[str, Any]]:
    """Retourne l'historique de l'utilisateur (liste vide si inconnu)."""
    return list(_history[username])
 
 
def clear_history() -> None:
    """Vide tout l'historique (utile pour les tests)."""
    _history.clear()
 