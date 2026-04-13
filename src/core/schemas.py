from pydantic import BaseModel, Field
from typing import List
 
 
class CodeAnalysisResult(BaseModel):
    """Résultat structuré de l'analyse d'un code Python."""
 
    is_optimal: bool = Field(
        description="True si le code est jugé optimal, False sinon."
    )
    issues: List[str] = Field(
        default_factory=list,
        description="Liste des problèmes identifiés dans le code.",
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Liste des suggestions d'amélioration.",
    )
 
 
class GeneratedTestResult(BaseModel):
    """Résultat structuré d'un test unitaire généré."""
 
    unit_test: str = Field(
        description="Le test unitaire pytest généré sous forme de string Python."
    )
 
 
class TestExplanationResult(BaseModel):
    """Résultat structuré de l'explication d'un test unitaire."""
 
    explanation: str = Field(
        description="Explication pédagogique et détaillée du test unitaire."
    )
 