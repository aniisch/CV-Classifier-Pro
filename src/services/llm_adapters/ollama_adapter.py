"""
Ollama Adapter - Pour utiliser des LLMs locaux via Ollama.
https://ollama.ai
"""

import httpx
from typing import Dict, Any, Optional
from .base_adapter import BaseLLMAdapter, LLMResponse


class OllamaAdapter(BaseLLMAdapter):
    """
    Adapter pour Ollama - LLMs locaux.
    Gratuit, prive, ne necessite pas de cle API.
    """

    def __init__(
        self,
        model: str = "llama3.2",
        ollama_url: str = "http://localhost:11434",
        **kwargs
    ):
        """
        Initialise l'adapter Ollama.

        Args:
            model: Nom du modele (ex: 'llama3.2', 'mistral', 'codellama')
            ollama_url: URL du serveur Ollama
        """
        super().__init__(api_key="", model=model, **kwargs)
        self.ollama_url = ollama_url.rstrip('/')
        self.timeout = kwargs.get('timeout', 120.0)  # Timeout plus long pour les modeles locaux

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def analyze_cv(
        self,
        cv_content: str,
        job_offer_content: str,
        additional_context: Optional[str] = None
    ) -> LLMResponse:
        """Analyse un CV via Ollama."""
        prompt = self.build_analysis_prompt(cv_content, job_offer_content, additional_context)
        system_prompt = self.build_system_prompt()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "stream": False,
                        "options": {
                            "temperature": 0.3,  # Plus deterministe pour l'analyse
                            "num_predict": 2000  # Limite de tokens en sortie
                        }
                    }
                )

                if response.status_code != 200:
                    raise Exception(f"Erreur Ollama: {response.status_code} - {response.text}")

                data = response.json()
                content = data.get("message", {}).get("content", "")

                return LLMResponse(
                    content=content,
                    model=self.model,
                    provider=self.provider_name,
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                    },
                    raw_response=data
                )

        except httpx.ConnectError:
            raise Exception(
                f"Impossible de se connecter a Ollama sur {self.ollama_url}. "
                "Verifiez que Ollama est lance (ollama serve)."
            )
        except httpx.TimeoutException:
            raise Exception(
                f"Timeout lors de l'appel a Ollama. "
                f"Le modele {self.model} met peut-etre trop de temps a repondre."
            )
        except Exception as e:
            raise Exception(f"Erreur Ollama: {str(e)}")

    async def test_connection(self) -> Dict[str, Any]:
        """Teste la connexion a Ollama et liste les modeles disponibles."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Test de base - ping
                response = await client.get(f"{self.ollama_url}/api/tags")

                if response.status_code != 200:
                    return {
                        "status": "error",
                        "message": f"Ollama repond avec le code {response.status_code}"
                    }

                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name", "").split(":")[0] for m in models]

                # Verifier si le modele configure est disponible
                model_available = any(
                    self.model in name or name in self.model
                    for name in model_names
                )

                return {
                    "status": "ok",
                    "provider": self.provider_name,
                    "available_models": model_names,
                    "configured_model": self.model,
                    "model_available": model_available,
                    "message": "Connexion reussie" if model_available else f"Modele {self.model} non trouve. Lancez: ollama pull {self.model}"
                }

        except httpx.ConnectError:
            return {
                "status": "error",
                "message": f"Impossible de se connecter a Ollama sur {self.ollama_url}. Lancez 'ollama serve'."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur: {str(e)}"
            }

    async def list_models(self) -> list:
        """Liste les modeles disponibles sur Ollama."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            pass
        return []

    async def pull_model(self, model_name: str) -> bool:
        """Telecharge un modele (peut prendre du temps)."""
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:  # 10 min timeout
                response = await client.post(
                    f"{self.ollama_url}/api/pull",
                    json={"name": model_name, "stream": False}
                )
                return response.status_code == 200
        except Exception:
            return False
