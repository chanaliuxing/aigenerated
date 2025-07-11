import logging

class PromptEngine:
    """Minimal prompt engine that aggregates input data."""
    def __init__(self):
        self.initialized = False
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        self.initialized = True

    async def build_prompt(self, message, context, phase, slots, conversation):
        return {
            'message': message,
            'context': context,
            'phase': phase,
            'slots': slots,
            'conversation': conversation,
        }
