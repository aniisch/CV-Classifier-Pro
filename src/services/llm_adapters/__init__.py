"""
LLM Adapters Package
Fournit une interface unifiee pour differents providers LLM.
"""

from .base_adapter import BaseLLMAdapter
from .ollama_adapter import OllamaAdapter
from .openai_adapter import OpenAIAdapter
from .anthropic_adapter import AnthropicAdapter

__all__ = [
    'BaseLLMAdapter',
    'OllamaAdapter',
    'OpenAIAdapter',
    'AnthropicAdapter'
]
