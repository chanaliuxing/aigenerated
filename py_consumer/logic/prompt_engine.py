"""Prompt building utilities."""

from __future__ import annotations

import logging
from typing import Dict, Any, List

from utils.database import DatabaseManager


class PromptEngine:
    """Constructs prompts for the AI providers."""

    def __init__(self) -> None:
        self.initialized = False
        self.logger = logging.getLogger(__name__)
        self.db = DatabaseManager()

    async def initialize(self) -> None:
        if self.initialized:
            return
        self.initialized = True
        self.logger.info("Prompt engine initialized")

    async def build_prompt(
        self,
        message: str,
        context: List[Dict[str, Any]],
        phase: str,
        slots: Dict[str, Any],
        conversation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build a chat completion payload for a provider."""

        if not self.initialized:
            await self.initialize()

        template = await self.db.get_prompt_template(phase)
        system_prompt = template['template_content'] if template else ''

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})

        for msg in context:
            messages.append({
                'role': 'user' if msg['sender_type'] == 'user' else 'assistant',
                'content': msg['content'],
            })

        messages.append({'role': 'user', 'content': message})

        return {
            'messages': messages,
            'phase': phase,
            'slots': slots,
            'conversation': conversation,
        }
