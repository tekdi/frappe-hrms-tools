"""
LLM Provider Factory
Handles selection and instantiation of LLM providers
"""
from typing import Optional
import logging
from app.core.config import get_settings
from app.llm_providers.base import BaseLLMProvider, LLMProviderError
from app.llm_providers.openai_provider import OpenAIProvider
from app.llm_providers.anthropic_provider import AnthropicProvider
from app.llm_providers.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating and managing LLM providers"""

    def __init__(self):
        self.settings = get_settings()
        self._providers = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize all available providers based on configuration"""

        # Initialize OpenAI
        if self.settings.OPENAI_API_KEY:
            try:
                self._providers['openai'] = OpenAIProvider(
                    api_key=self.settings.OPENAI_API_KEY,
                    model=self.settings.OPENAI_MODEL,
                    temperature=self.settings.OPENAI_TEMPERATURE,
                    max_tokens=self.settings.OPENAI_MAX_TOKENS
                )
                logger.info("OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI provider: {e}")

        # Initialize Anthropic
        if self.settings.ANTHROPIC_API_KEY:
            try:
                self._providers['anthropic'] = AnthropicProvider(
                    api_key=self.settings.ANTHROPIC_API_KEY,
                    model=self.settings.ANTHROPIC_MODEL,
                    temperature=self.settings.ANTHROPIC_TEMPERATURE,
                    max_tokens=self.settings.ANTHROPIC_MAX_TOKENS
                )
                logger.info("Anthropic provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic provider: {e}")

        # Initialize Gemini
        if self.settings.GEMINI_API_KEY:
            try:
                self._providers['gemini'] = GeminiProvider(
                    api_key=self.settings.GEMINI_API_KEY,
                    model=self.settings.GEMINI_MODEL,
                    temperature=self.settings.GEMINI_TEMPERATURE,
                    max_tokens=self.settings.GEMINI_MAX_TOKENS
                )
                logger.info("Gemini provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini provider: {e}")

        if not self._providers:
            logger.warning("No LLM providers initialized! Check your API key configuration.")

    def get_provider(self, provider_name: Optional[str] = None) -> BaseLLMProvider:
        """
        Get an LLM provider by name or automatically select an available one

        Args:
            provider_name: Name of the provider (openai, anthropic, gemini, or auto)
                          If None or 'auto', selects first available provider

        Returns:
            Initialized LLM provider

        Raises:
            LLMProviderError: If no provider is available or requested provider not found
        """
        # Use default if not specified
        if not provider_name or provider_name == 'auto':
            provider_name = self.settings.DEFAULT_LLM_PROVIDER

        # If still 'auto', pick first available
        if provider_name == 'auto':
            if not self._providers:
                raise LLMProviderError(
                    provider="auto",
                    message="No LLM providers are configured. Please set API keys in environment variables."
                )

            # Return first available provider
            provider_name = next(iter(self._providers.keys()))
            logger.info(f"Auto-selected provider: {provider_name}")

        # Get specific provider
        if provider_name not in self._providers:
            available = list(self._providers.keys())
            raise LLMProviderError(
                provider=provider_name,
                message=f"Provider '{provider_name}' not available. Available providers: {available}"
            )

        provider = self._providers[provider_name]

        # Verify provider is available
        if not provider.is_available():
            raise LLMProviderError(
                provider=provider_name,
                message=f"Provider '{provider_name}' is not properly configured"
            )

        logger.info(f"Using LLM provider: {provider_name}")
        return provider

    def get_available_providers(self) -> dict:
        """
        Get status of all providers

        Returns:
            Dict mapping provider names to availability status
        """
        status = {}

        # Check OpenAI
        if 'openai' in self._providers:
            status['openai'] = 'available' if self._providers['openai'].is_available() else 'configured_but_unavailable'
        else:
            status['openai'] = 'not_configured'

        # Check Anthropic
        if 'anthropic' in self._providers:
            status['anthropic'] = 'available' if self._providers['anthropic'].is_available() else 'configured_but_unavailable'
        else:
            status['anthropic'] = 'not_configured'

        # Check Gemini
        if 'gemini' in self._providers:
            status['gemini'] = 'available' if self._providers['gemini'].is_available() else 'configured_but_unavailable'
        else:
            status['gemini'] = 'not_configured'

        return status

    def has_any_provider(self) -> bool:
        """Check if at least one provider is available"""
        return len(self._providers) > 0


# Global factory instance
_factory_instance: Optional[LLMFactory] = None


def get_llm_factory() -> LLMFactory:
    """Get or create the global LLM factory instance"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = LLMFactory()
    return _factory_instance
