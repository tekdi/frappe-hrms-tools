"""
OpenAI LLM Provider Implementation
"""
from typing import Optional
import logging
from openai import AsyncOpenAI, OpenAIError
from .base import BaseLLMProvider, LLMResponse, LLMProviderError

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider implementation"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview",
                 temperature: float = 0.3, max_tokens: int = 4000):
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """
        Generate response using OpenAI API

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
                provider="openai",
                message="OpenAI client not initialized. Check API key."
            )

        try:
            messages = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            logger.info(f"Calling OpenAI API with model: {self.model}")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}  # Request JSON output
            )

            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
            finish_reason = response.choices[0].finish_reason

            logger.info(f"OpenAI response received. Tokens used: {tokens_used}")

            return LLMResponse(
                content=content,
                model=response.model,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
                raw_response=response.model_dump()
            )

        except OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise LLMProviderError(
                provider="openai",
                message=f"OpenAI API call failed: {str(e)}",
                original_error=e
            )
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI provider: {str(e)}")
            raise LLMProviderError(
                provider="openai",
                message=f"Unexpected error: {str(e)}",
                original_error=e
            )

    def is_available(self) -> bool:
        """Check if OpenAI provider is available"""
        return self.validate_api_key() and self.client is not None

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "openai"
