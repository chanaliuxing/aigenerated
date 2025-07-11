import re
import logging

class SlotExtractor:
    """Simple slot extractor using regex patterns."""
    def __init__(self):
        self.initialized = False
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        self.initialized = True

    async def extract_slots(self, message: str, current_phase: str):
        slots = {}
        email = re.search(r'[\w.-]+@[\w.-]+', message)
        if email:
            slots['email'] = email.group(0)
        phone = re.search(r'(\+?\d[\d\s-]{7,}\d)', message)
        if phone:
            slots['phone'] = phone.group(0)
        return slots
