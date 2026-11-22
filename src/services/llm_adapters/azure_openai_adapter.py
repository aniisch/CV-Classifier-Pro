"""
Azure OpenAI Adapter - Modeles GPT deployes dans Microsoft Foundry (Azure OpenAI).
https://learn.microsoft.com/azure/ai-foundry/openai/
"""

import asyncio
import os
from typing import Any, Dict, Optional

import httpx

from .base_adapter import BaseLLMAdapter, LLMResponse


class AzureOpenAIAdapter(BaseLLMAdapter):
    """
    Adapter pour Azure OpenAI via l'API v1 (/openai/v1/chat/completions).
    Le champ `model` correspond au NOM DU DEPLOIEMENT Azure.
    """

    MAX_RETRIES = 5
    MAX_WAIT_SECONDS = 60.0
    RETRY_STATUS = (429, 500, 503)
    LEGACY_PREFIXES = ("gpt-4", "gpt-35", "gpt-3.5")

    def __init__(
        self,
        api_key: str = "",
        model: str = "",
        endpoint: str = "",
        **kwargs
    ):
        """
        Initialise l'adapter Azure OpenAI.

        Args:
            api_key: Cle de la ressource Azure (sinon AZURE_OPENAI_API_KEY)
            model: Nom du deploiement Azure
            endpoint: Endpoint de la ressource (sinon AZURE_OPENAI_ENDPOINT)
        """
        super().__init__(api_key=api_key, model=model, **kwargs)
        self.api_key = api_key or os.environ.get("AZURE_OPENAI_API_KEY", "")
        self.endpoint = self._normalize_endpoint(
            endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT", "")
        )
        self.timeout = kwargs.get("timeout", 300.0)
        self.transport = kwargs.get("transport")  # injection pour les tests
        self.sleep = kwargs.get("sleep", asyncio.sleep)

    @staticmethod
    def _normalize_endpoint(endpoint: str) -> str:
        """Retire le '/' final et un eventuel suffixe '/openai' ou '/openai/v1'."""
        endpoint = (endpoint or "").strip().rstrip("/")
        for suffix in ("/openai/v1", "/openai"):
            if endpoint.lower().endswith(suffix):
                endpoint = endpoint[: -len(suffix)]
                break
        return endpoint.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "azure_openai"

    @property
    def is_reasoning_model(self) -> bool:
        """True pour les modeles a raisonnement (AZURE_OPENAI_REASONING=0|1 force le mode)."""
        forced = os.environ.get("AZURE_OPENAI_REASONING", "").strip()
        if forced in ("0", "1"):
            return forced == "1"
        return not self.model.lower().startswith(self.LEGACY_PREFIXES)

    def _build_body(self, messages: list, max_completion_tokens: Optional[int] = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {"model": self.model, "messages": messages}
        if self.is_reasoning_model:
            body["max_completion_tokens"] = max_completion_tokens or 16000
            body["reasoning_effort"] = os.environ.get("AZURE_OPENAI_REASONING_EFFORT", "medium")
        else:
            body["temperature"] = 0.2
            if max_completion_tokens:
                body["max_completion_tokens"] = max_completion_tokens
        return body

    def _check_config(self) -> None:
        if not self.api_key:
            raise Exception("Cle API Azure OpenAI non configuree")
        if not self.endpoint:
            raise Exception("Endpoint Azure OpenAI non configure")
        if not self.model:
            raise Exception("Nom du deploiement Azure OpenAI non configure")

    @staticmethod
    def _backoff(attempt: int) -> float:
        return min(2.0 ** attempt, AzureOpenAIAdapter.MAX_WAIT_SECONDS)

    def _retry_wait(self, response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("retry-after")
        try:
            if retry_after is not None:
                return min(max(float(retry_after), 0.0), self.MAX_WAIT_SECONDS)
        except ValueError:
            pass
        return self._backoff(attempt)

    async def _post_chat(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Appelle chat/completions avec retries et retourne le JSON de reponse."""
        self._check_config()
        url = f"{self.endpoint}/openai/v1/chat/completions"
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        last_error = "Erreur inconnue"

        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
            for attempt in range(self.MAX_RETRIES):
                is_last = attempt == self.MAX_RETRIES - 1
                try:
                    response = await client.post(url, headers=headers, json=body)
                except httpx.TimeoutException:
                    last_error = "Timeout lors de l'appel a Azure OpenAI"
                    if not is_last:
                        await self.sleep(self._backoff(attempt))
                    continue
                except httpx.ConnectError:
                    last_error = "Impossible de se connecter a Azure OpenAI. Verifiez l'endpoint et votre connexion."
                    if not is_last:
                        await self.sleep(self._backoff(attempt))
                    continue

                if response.status_code == 200:
                    return response.json()
                if response.status_code == 401:
                    raise Exception("Cle API Azure OpenAI invalide ou expiree")
                if response.status_code == 404:
                    raise Exception(
                        f"Deploiement introuvable: '{self.model}'. "
                        "Verifiez le nom du deploiement et l'endpoint."
                    )
                if response.status_code in self.RETRY_STATUS:
                    last_error = f"Azure OpenAI indisponible ou limite atteinte (HTTP {response.status_code})"
                    if not is_last:
                        await self.sleep(self._retry_wait(response, attempt))
                    continue
                raise Exception(f"Erreur Azure OpenAI: {self._error_message(response)}")

        raise Exception(f"{last_error} apres {self.MAX_RETRIES} tentatives")

    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        try:
            error = response.json().get("error", {})
            return error.get("message") or response.text
        except Exception:
            return response.text

    async def analyze_cv(
        self,
        cv_content: str,
        job_offer_content: str,
        additional_context: Optional[str] = None
    ) -> LLMResponse:
        """Analyse un CV via Azure OpenAI."""
        prompt = self.build_analysis_prompt(cv_content, job_offer_content, additional_context)
        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": prompt},
        ]
        data = await self._post_chat(self._build_body(messages))

        choices = data.get("choices") or []
        content = (choices[0].get("message", {}).get("content") if choices else None) or ""
        if not content.strip():
            raise Exception(
                "Reponse vide d'Azure OpenAI (le raisonnement a probablement consomme tous les tokens). "
                "Essayez de baisser AZURE_OPENAI_REASONING_EFFORT (ex: 'low')."
            )

        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider_name,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            raw_response=data,
        )

    async def test_connection(self) -> Dict[str, Any]:
        """Teste la connexion avec un petit appel chat."""
        try:
            messages = [{"role": "user", "content": "Réponds juste: ok"}]
            await self._post_chat(self._build_body(messages, max_completion_tokens=200))
            return {
                "status": "ok",
                "provider": self.provider_name,
                "message": "Connexion reussie",
                "configured_model": self.model,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
