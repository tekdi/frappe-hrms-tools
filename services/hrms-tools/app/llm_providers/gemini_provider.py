"""
Google Gemini LLM Provider Implementation
"""
from typing import Optional
import logging
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from .base import BaseLLMProvider, LLMResponse, LLMProviderError

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider implementation"""

    def __init__(self, api_key: str, model: str = "gemini-1.5-pro",
                 temperature: float = 0.3, max_tokens: int = 4000):
        super().__init__(api_key, model, temperature, max_tokens)

        if api_key:
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(
                model_name=model,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )
        else:
            self.client = None

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """
        Generate response using Google Gemini API

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
                provider="gemini",
                message="Gemini client not initialized. Check API key."
            )

        try:
            logger.info(f"Calling Gemini API with model: {self.model}")

            # Combine system prompt and user prompt if system prompt exists
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Generate response
            # Note: Gemini's Python SDK doesn't have native async support yet
            # Using sync call - in production, consider running in thread pool
            response = self.client.generate_content(
                full_prompt,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                }
            )

            # Extract content
            content = response.text if response.text else ""

            # Get token counts if available
            tokens_used = None
            if hasattr(response, 'usage_metadata'):
                tokens_used = (
                    response.usage_metadata.prompt_token_count +
                    response.usage_metadata.candidates_token_count
                )

            # Get finish reason
            finish_reason = None
            if response.candidates and len(response.candidates) > 0:
                finish_reason = str(response.candidates[0].finish_reason)

            logger.info(f"Gemini response received. Tokens used: {tokens_used}")

            return LLMResponse(
                content=content,
                model=self.model,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
                raw_response={
                    "text": content,
                    "usage": tokens_used,
                    "finish_reason": finish_reason
                }
            )

        except google_exceptions.GoogleAPIError as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise LLMProviderError(
                provider="gemini",
                message=f"Gemini API call failed: {str(e)}",
                original_error=e
            )
        except Exception as e:
            logger.error(f"Unexpected error in Gemini provider: {str(e)}")
            raise LLMProviderError(
                provider="gemini",
                message=f"Unexpected error: {str(e)}",
                original_error=e
            )

    def is_available(self) -> bool:
        """Check if Gemini provider is available"""
        return self.validate_api_key() and self.client is not None

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "gemini"
