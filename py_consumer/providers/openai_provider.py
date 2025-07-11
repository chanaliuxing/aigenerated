"""OpenAI provider implementation used by the Python consumer service."""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Dict, Any, List

try:  # OpenAI SDK may not be installed in minimal environments
    import openai
except Exception:  # pragma: no cover - optional dependency
    openai = None


class OpenAIProvider:
    """Wrapper around the OpenAI chat completion API."""

    def __init__(self, config) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.initialized = False
        self.api_key = None
        self.model = None

    async def initialize(self) -> None:
        """Initialize provider configuration."""
        if self.initialized:
            return
        self.api_key = self.config.get('ai_providers.openai.api_key')
        self.model = self.config.get('ai_providers.openai.model', 'gpt-4-turbo-preview')
        if openai is not None:
            openai.api_key = self.api_key
        self.initialized = True
        self.logger.info("OpenAI provider initialized")

    async def generate_response(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a response using the OpenAI API."""
        if not self.initialized:
            await self.initialize()

        messages: List[Dict[str, str]] = prompt_data.get('messages', [])
        if not messages and 'message' in prompt_data:
            messages = [{'role': 'user', 'content': prompt_data['message']}]

        if openai is None:
            # Fallback deterministic response if the SDK is unavailable
            text = " ".join(m['content'] for m in messages)
            return {
                'content': f"OpenAI response to: {text}",
                'tokens_used': len(text.split()),
                'processing_time': 0.0,
            }

        start = perf_counter()
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                max_tokens=self.config.get('ai_providers.openai.max_tokens', 2000),
                temperature=self.config.get('ai_providers.openai.temperature', 0.7),
            )
            elapsed = perf_counter() - start
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            return {
                'content': content,
                'tokens_used': tokens_used,
                'processing_time': elapsed,
            }
        except Exception as exc:  # pragma: no cover - external dependency
            self.logger.error("OpenAI API error: %s", exc)
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Return basic health information."""
        return {'healthy': bool(self.api_key)}
