"""
OpenAI Adapter - Pour utiliser les modeles GPT via l'API OpenAI.
https://platform.openai.com
"""

import httpx
from typing import Dict, Any, Optional
from .base_adapter import BaseLLMAdapter, LLMResponse


class OpenAIAdapter(BaseLLMAdapter):
    """
    Adapter pour OpenAI - GPT-4, GPT-3.5, etc.
    Necessite une cle API payante.
    """

    OPENAI_API_URL = "https://api.openai.com/v1"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        **kwargs
    ):
        """
        Initialise l'adapter OpenAI.

        Args:
            api_key: Cle API OpenAI (commence par 'sk-')
            model: Nom du modele (ex: 'gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo')
        """
        super().__init__(api_key=api_key, model=model, **kwargs)
        self.timeout = kwargs.get('timeout', 60.0)

    @property
    def provider_name(self) -> str:
        return "openai"

    async def analyze_cv(
        self,
        cv_content: str,
        job_offer_content: str,
        additional_context: Optional[str] = None
    ) -> LLMResponse:
        """Analyse un CV via OpenAI."""
        if not self.api_key:
            raise Exception("Cle API OpenAI non configuree")

        prompt = self.build_analysis_prompt(cv_content, job_offer_content, additional_context)
        system_prompt = self.build_system_prompt()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.OPENAI_API_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000
                    }
                )

                if response.status_code == 401:
                    raise Exception("Cle API OpenAI invalide ou expiree")
                elif response.status_code == 429:
                    raise Exception("Limite de requetes OpenAI atteinte. Reessayez plus tard.")
                elif response.status_code != 200:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                    raise Exception(f"Erreur OpenAI: {error_msg}")

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

                return LLMResponse(
                    content=content,
                    model=self.model,
                    provider=self.provider_name,
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0)
                    },
                    raw_response=data
                )

        except httpx.ConnectError:
            raise Exception("Impossible de se connecter a l'API OpenAI. Verifiez votre connexion internet.")
        except httpx.TimeoutException:
            raise Exception("Timeout lors de l'appel a OpenAI. Reessayez.")
        except Exception as e:
            if "Erreur OpenAI" in str(e) or "Cle API" in str(e):
                raise
            raise Exception(f"Erreur OpenAI: {str(e)}")

    async def test_connection(self) -> Dict[str, Any]:
        """Teste la connexion a OpenAI."""
        if not self.api_key:
            return {
                "status": "error",
                "message": "Cle API OpenAI non configuree"
            }

        if not self.api_key.startswith("sk-"):
            return {
                "status": "error",
                "message": "Format de cle API invalide (doit commencer par 'sk-')"
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test avec l'endpoint models
                response = await client.get(
                    f"{self.OPENAI_API_URL}/models",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )

                if response.status_code == 401:
                    return {
                        "status": "error",
                        "message": "Cle API invalide ou expiree"
                    }
                elif response.status_code == 200:
                    data = response.json()
                    # Filtrer pour les modeles GPT
                    gpt_models = [
                        m["id"] for m in data.get("data", [])
                        if "gpt" in m["id"].lower()
                    ]
                    return {
                        "status": "ok",
                        "provider": self.provider_name,
                        "message": "Connexion reussie",
                        "configured_model": self.model,
                        "available_models": sorted(gpt_models)[:10]  # Top 10
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Erreur API: {response.status_code}"
                    }

        except httpx.ConnectError:
            return {
                "status": "error",
                "message": "Impossible de se connecter a l'API OpenAI"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur: {str(e)}"
            }
