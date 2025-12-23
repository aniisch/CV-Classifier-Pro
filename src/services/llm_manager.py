"""
LLM Manager - Orchestration des appels LLM.
Gere la selection du provider et l'execution des analyses.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from ..database.models import LLMSettings
from .llm_adapters import (
    BaseLLMAdapter,
    OllamaAdapter,
    OpenAIAdapter,
    AnthropicAdapter
)
from .llm_adapters.base_adapter import LLMResponse


class LLMManager:
    """
    Gestionnaire central pour les appels LLM.
    Selectionne automatiquement le bon adapter selon la configuration.
    """

    PROVIDERS = {
        "ollama": OllamaAdapter,
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter
    }

    def __init__(self, db: Session):
        """
        Initialise le manager avec la session DB.

        Args:
            db: Session SQLAlchemy pour recuperer les settings
        """
        self.db = db
        self._adapter: Optional[BaseLLMAdapter] = None
        self._settings: Optional[LLMSettings] = None

    def _load_settings(self) -> LLMSettings:
        """Charge les settings LLM depuis la DB."""
        settings = self.db.query(LLMSettings).first()
        if not settings:
            # Creer les settings par defaut
            settings = LLMSettings(
                id=1,
                provider="ollama",
                api_key="",
                model="llama3.2",
                ollama_url="http://localhost:11434"
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        return settings

    def _get_adapter(self) -> BaseLLMAdapter:
        """Retourne l'adapter configure."""
        if self._adapter is None:
            self._settings = self._load_settings()

            provider = self._settings.provider
            if provider not in self.PROVIDERS:
                raise ValueError(f"Provider inconnu: {provider}")

            adapter_class = self.PROVIDERS[provider]

            if provider == "ollama":
                self._adapter = adapter_class(
                    model=self._settings.model,
                    ollama_url=self._settings.ollama_url
                )
            else:
                self._adapter = adapter_class(
                    api_key=self._settings.api_key,
                    model=self._settings.model
                )

        return self._adapter

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
        adapter = self._get_adapter()
        return await adapter.analyze_cv(cv_content, job_offer_content, additional_context)

    async def analyze_multiple_cvs(
        self,
        cvs: List[Dict[str, str]],
        job_offer_content: str
    ) -> List[Dict[str, Any]]:
        """
        Analyse plusieurs CVs par rapport a une offre.

        Args:
            cvs: Liste de dicts avec 'filename' et 'content'
            job_offer_content: Contenu de l'offre d'emploi

        Returns:
            Liste de resultats avec filename, response et erreur eventuelle
        """
        results = []
        adapter = self._get_adapter()

        for cv in cvs:
            try:
                response = await adapter.analyze_cv(
                    cv_content=cv["content"],
                    job_offer_content=job_offer_content
                )
                results.append({
                    "filename": cv["filename"],
                    "success": True,
                    "response": response,
                    "error": None
                })
            except Exception as e:
                results.append({
                    "filename": cv["filename"],
                    "success": False,
                    "response": None,
                    "error": str(e)
                })

        return results

    async def test_connection(self) -> Dict[str, Any]:
        """Teste la connexion au LLM configure."""
        adapter = self._get_adapter()
        return await adapter.test_connection()

    def get_current_config(self) -> Dict[str, Any]:
        """Retourne la configuration actuelle."""
        settings = self._load_settings()
        return {
            "provider": settings.provider,
            "model": settings.model,
            "ollama_url": settings.ollama_url if settings.provider == "ollama" else None,
            "has_api_key": bool(settings.api_key) if settings.provider != "ollama" else True
        }

    @staticmethod
    def get_available_providers() -> List[Dict[str, Any]]:
        """Retourne la liste des providers disponibles."""
        return [
            {
                "id": "ollama",
                "name": "Ollama (Local)",
                "description": "LLMs locaux, gratuit, donnees privees",
                "requires_api_key": False,
                "default_model": "llama3.2",
                "models": ["llama3.2", "llama3.1", "mistral", "codellama", "phi3"]
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "description": "GPT-4, rapide et fiable",
                "requires_api_key": True,
                "default_model": "gpt-4o-mini",
                "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
            },
            {
                "id": "anthropic",
                "name": "Anthropic",
                "description": "Claude, excellent raisonnement",
                "requires_api_key": True,
                "default_model": "claude-sonnet-4-20250514",
                "models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
            }
        ]


def get_llm_manager(db: Session) -> LLMManager:
    """Factory function pour creer un LLMManager."""
    return LLMManager(db)
