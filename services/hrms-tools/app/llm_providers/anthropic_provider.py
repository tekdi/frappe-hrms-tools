"""
Anthropic Claude LLM Provider Implementation
"""
from typing import Optional
import logging
from anthropic import AsyncAnthropic, AnthropicError
from .base import BaseLLMProvider, LLMResponse, LLMProviderError

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022",
                 temperature: float = 0.3, max_tokens: int = 4000):
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = AsyncAnthropic(api_key=api_key) if api_key else None

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """
        Generate response using Anthropic API

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with generated content

        Raises:
            LLMProviderError: If API call fails
        """
        if not self.client:
            raise LLMProviderError(
                provider="anthropic",
                message="Anthropic client not initialized. Check API key."
            )

        try:
            logger.info(f"Calling Anthropic API with model: {self.model}")

            # Build request parameters
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            # Add system prompt if provided
            if system_prompt:
                kwargs["system"] = system_prompt

            response = await self.client.messages.create(**kwargs)

            # Extract text content from response
            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text

            # Calculate tokens used
            tokens_used = None
            if hasattr(response, 'usage'):
                tokens_used = response.usage.input_tokens + response.usage.output_tokens

            logger.info(f"Anthropic response received. Tokens used: {tokens_used}")

            return LLMResponse(
                content=content,
                model=response.model,
                tokens_used=tokens_used,
                finish_reason=response.stop_reason,
                raw_response=response.model_dump()
            )

        except AnthropicError as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise LLMProviderError(
                provider="anthropic",
                message=f"Anthropic API call failed: {str(e)}",
                original_error=e
            )
        except Exception as e:
            logger.error(f"Unexpected error in Anthropic provider: {str(e)}")
            raise LLMProviderError(
                provider="anthropic",
                message=f"Unexpected error: {str(e)}",
                original_error=e
            )

    def is_available(self) -> bool:
        """Check if Anthropic provider is available"""
        return self.validate_api_key() and self.client is not None

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "anthropic"
