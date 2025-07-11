"""DeepSeek provider implementation for the Python consumer."""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Dict, Any, List

try:
    import aiohttp
except Exception:  # pragma: no cover - optional dependency
    aiohttp = None


class DeepSeekProvider:
    """Interface to the DeepSeek chat completion API."""

    def __init__(self, config) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.initialized = False
        self.api_key = None
        self.model = None

    async def initialize(self) -> None:
        if self.initialized:
            return
        self.api_key = self.config.get('ai_providers.deepseek.api_key')
        self.model = self.config.get('ai_providers.deepseek.model', 'deepseek-chat')
        self.initialized = True
        self.logger.info("DeepSeek provider initialized")

    async def generate_response(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()

        messages: List[Dict[str, str]] = prompt_data.get('messages', [])
        if not messages and 'message' in prompt_data:
            messages = [{'role': 'user', 'content': prompt_data['message']}]

        if aiohttp is None:
            text = " ".join(m['content'] for m in messages)
            return {
                'content': f"DeepSeek response to: {text}",
                'tokens_used': len(text.split()),
                'processing_time': 0.0,
            }

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': self.model,
            'messages': messages,
            'max_tokens': self.config.get('ai_providers.deepseek.max_tokens', 2000),
            'temperature': self.config.get('ai_providers.deepseek.temperature', 0.7),
            'stream': False,
        }

        start = perf_counter()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post('https://api.deepseek.com/v1/chat/completions', json=payload, headers=headers) as resp:
                    data = await resp.json()
            elapsed = perf_counter() - start
            content = data['choices'][0]['message']['content']
            tokens_used = data.get('usage', {}).get('total_tokens', 0)
            return {
                'content': content,
                'tokens_used': tokens_used,
                'processing_time': elapsed,
            }
        except Exception as exc:  # pragma: no cover - external dependency
            self.logger.error("DeepSeek API error: %s", exc)
            raise

    async def health_check(self) -> Dict[str, Any]:
        return {'healthy': bool(self.api_key)}
