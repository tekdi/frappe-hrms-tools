"""
Base abstract class for LLM providers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized response from LLM providers"""
    content: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    All providers must implement these methods to ensure consistent interface.
    """

    def __init__(self, api_key: str, model: str, temperature: float = 0.3, max_tokens: int = 4000):
        """
        Initialize LLM provider

        Args:
            api_key: API key for the provider
            model: Model identifier
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """
        Generate a response from the LLM

        Args:
            prompt: User prompt/message
            system_prompt: Optional system prompt for context

        Returns:
            LLMResponse object with standardized fields

        Raises:
            LLMProviderError: If the API call fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is properly configured and available

        Returns:
            True if provider can be used, False otherwise
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of the provider

        Returns:
            Provider name (e.g., "openai", "anthropic", "gemini")
        """
        pass

    def validate_api_key(self) -> bool:
        """
        Validate that API key is set

        Returns:
            True if API key is valid, False otherwise
        """
        return bool(self.api_key and len(self.api_key) > 0)


class LLMProviderError(Exception):
    """Exception raised when LLM provider encounters an error"""

    def __init__(self, provider: str, message: str, original_error: Optional[Exception] = None):
        self.provider = provider
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{provider}] {message}")
