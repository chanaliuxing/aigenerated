import logging

class DeepSeekProvider:
    """Simplified DeepSeek provider used for testing."""
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.initialized = False

    async def initialize(self):
        self.initialized = True

    async def generate_response(self, prompt_data):
        message = prompt_data.get('message', '')
        return {
            'content': f"DeepSeek response to: {message}",
            'tokens_used': len(message.split()),
            'processing_time': 0.0,
        }

    async def health_check(self):
        return {'healthy': True}
