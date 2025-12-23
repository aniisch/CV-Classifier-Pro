"""
Base Adapter - Interface commune pour tous les LLM adapters.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Structure de reponse standardisee pour tous les LLMs."""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None  # tokens utilises
    raw_response: Optional[Any] = None  # reponse brute du provider


class BaseLLMAdapter(ABC):
    """
    Interface abstraite pour les adapters LLM.
    Tous les adapters doivent implementer ces methodes.
    """

    def __init__(self, api_key: str = "", model: str = "", **kwargs):
        """
        Initialise l'adapter.

        Args:
            api_key: Cle API (vide pour Ollama)
            model: Nom du modele a utiliser
            **kwargs: Arguments supplementaires specifiques au provider
        """
        self.api_key = api_key
        self.model = model
        self.config = kwargs

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Retourne le nom du provider (ex: 'ollama', 'openai', 'anthropic')."""
        pass

    @abstractmethod
    async def analyze_cv(
        self,
        cv_content: str,
        job_offer_content: str,
        additional_context: Optional[str] = None
    ) -> LLMResponse:
        """
        Analyse un CV par rapport a une offre d'emploi.

        Args:
            cv_content: Contenu textuel du CV
            job_offer_content: Contenu de l'offre d'emploi
            additional_context: Contexte supplementaire optionnel

        Returns:
            LLMResponse avec l'analyse detaillee
        """
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Teste la connexion au provider.

        Returns:
            Dict avec status ('ok' ou 'error') et message/details
        """
        pass

    def build_analysis_prompt(
        self,
        cv_content: str,
        job_offer_content: str,
        additional_context: Optional[str] = None
    ) -> str:
        """
        Construit le prompt d'analyse CV vs Offre.
        Methode commune a tous les adapters.
        """
        prompt = f"""Tu es un expert RH specialise dans l'analyse de CVs et le recrutement.
Ton role est d'evaluer objectivement la correspondance entre un CV et une offre d'emploi.

=== OFFRE D'EMPLOI ===
{job_offer_content}

=== CV DU CANDIDAT ===
{cv_content}

=== INSTRUCTIONS ===
Analyse ce CV par rapport a l'offre d'emploi et fournis:

1. **Score de correspondance** (0-100%)
   - Evalue la compatibilite globale entre le profil et le poste

2. **Points forts du candidat**
   - Liste les competences et experiences qui correspondent bien a l'offre
   - Mentionne les atouts distinctifs

3. **Points faibles / Lacunes**
   - Identifie les competences requises qui semblent manquer
   - Note les experiences absentes ou insuffisantes

4. **Analyse detaillee**
   - Experience: adequation avec le niveau demande
   - Competences techniques: correspondance avec les requirements
   - Formation: pertinence par rapport au poste
   - Soft skills: si mentionnes, evaluer leur adequation

5. **Recommandation finale**
   - RETENIR: Profil tres compatible, a convoquer en entretien
   - A REVOIR: Profil interessant mais necessite clarification
   - REJETER: Profil insuffisamment compatible

Reponds de maniere structuree et objective."""

        if additional_context:
            prompt += f"\n\n=== CONTEXTE SUPPLEMENTAIRE ===\n{additional_context}"

        return prompt

    def build_system_prompt(self) -> str:
        """Retourne le system prompt pour l'analyse."""
        return """Tu es un assistant RH expert en analyse de CVs.
Tu evalues objectivement les candidatures par rapport aux offres d'emploi.
Tu fournis des analyses detaillees, structurees et actionables.
Tu es impartial et bases tes evaluations sur les faits presentes dans les documents."""
