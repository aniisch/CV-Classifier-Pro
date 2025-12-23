"""
Anthropic Adapter - Pour utiliser Claude via l'API Anthropic.
https://console.anthropic.com
"""

import httpx
from typing import Dict, Any, Optional
from .base_adapter import BaseLLMAdapter, LLMResponse


class AnthropicAdapter(BaseLLMAdapter):
    """
    Adapter pour Anthropic - Claude 3.5, Claude 3, etc.
    Necessite une cle API payante.
    """

    ANTHROPIC_API_URL = "https://api.anthropic.com/v1"
    ANTHROPIC_VERSION = "2023-06-01"

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        **kwargs
    ):
        """
        Initialise l'adapter Anthropic.

        Args:
            api_key: Cle API Anthropic (commence par 'sk-ant-')
            model: Nom du modele (ex: 'claude-sonnet-4-20250514', 'claude-3-5-sonnet-20241022')
        """
        super().__init__(api_key=api_key, model=model, **kwargs)
        self.timeout = kwargs.get('timeout', 60.0)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def analyze_cv(
        self,
        cv_content: str,
        job_offer_content: str,
        additional_context: Optional[str] = None
    ) -> LLMResponse:
        """Analyse un CV via Anthropic Claude."""
        if not self.api_key:
            raise Exception("Cle API Anthropic non configuree")

        prompt = self.build_analysis_prompt(cv_content, job_offer_content, additional_context)
        system_prompt = self.build_system_prompt()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.ANTHROPIC_API_URL}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": self.ANTHROPIC_VERSION,
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 2000,
                        "system": system_prompt,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3
                    }
                )

                if response.status_code == 401:
                    raise Exception("Cle API Anthropic invalide ou expiree")
                elif response.status_code == 429:
                    raise Exception("Limite de requetes Anthropic atteinte. Reessayez plus tard.")
                elif response.status_code == 400:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                    raise Exception(f"Erreur Anthropic: {error_msg}")
                elif response.status_code != 200:
                    raise Exception(f"Erreur Anthropic: {response.status_code} - {response.text}")

                data = response.json()

                # Extraire le contenu de la reponse
                content_blocks = data.get("content", [])
                content = ""
                for block in content_blocks:
                    if block.get("type") == "text":
                        content += block.get("text", "")

                usage = data.get("usage", {})

                return LLMResponse(
                    content=content,
                    model=self.model,
                    provider=self.provider_name,
                    usage={
                        "prompt_tokens": usage.get("input_tokens", 0),
                        "completion_tokens": usage.get("output_tokens", 0),
                        "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                    },
                    raw_response=data
                )

        except httpx.ConnectError:
            raise Exception("Impossible de se connecter a l'API Anthropic. Verifiez votre connexion internet.")
        except httpx.TimeoutException:
            raise Exception("Timeout lors de l'appel a Anthropic. Reessayez.")
        except Exception as e:
            if "Erreur Anthropic" in str(e) or "Cle API" in str(e):
                raise
            raise Exception(f"Erreur Anthropic: {str(e)}")

    async def test_connection(self) -> Dict[str, Any]:
        """Teste la connexion a Anthropic."""
        if not self.api_key:
            return {
                "status": "error",
                "message": "Cle API Anthropic non configuree"
            }

        if not self.api_key.startswith("sk-ant-"):
            return {
                "status": "error",
                "message": "Format de cle API invalide (doit commencer par 'sk-ant-')"
            }

        # Anthropic n'a pas d'endpoint pour lister les modeles
        # On fait un test simple avec un message court
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.ANTHROPIC_API_URL}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": self.ANTHROPIC_VERSION,
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 10,
                        "messages": [
                            {"role": "user", "content": "Reponds 'ok' uniquement."}
                        ]
                    }
                )

                if response.status_code == 401:
                    return {
                        "status": "error",
                        "message": "Cle API invalide ou expiree"
                    }
                elif response.status_code == 200:
                    return {
                        "status": "ok",
                        "provider": self.provider_name,
                        "message": "Connexion reussie",
                        "configured_model": self.model,
                        "available_models": [
                            "claude-sonnet-4-20250514",
                            "claude-3-5-sonnet-20241022",
                            "claude-3-haiku-20240307"
                        ]
                    }
                elif response.status_code == 400:
                    # Peut etre un probleme de modele
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "")
                    if "model" in error_msg.lower():
                        return {
                            "status": "error",
                            "message": f"Modele {self.model} non disponible"
                        }
                    return {
                        "status": "error",
                        "message": error_msg
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Erreur API: {response.status_code}"
                    }

        except httpx.ConnectError:
            return {
                "status": "error",
                "message": "Impossible de se connecter a l'API Anthropic"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur: {str(e)}"
            }
