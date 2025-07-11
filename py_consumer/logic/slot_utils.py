import re
import logging
from typing import Dict, Any


class SlotExtractor:
    """Simple slot extractor using regex patterns."""

    EMAIL_RE = re.compile(r"[\w.-]+@[\w.-]+")
    PHONE_RE = re.compile(r"(\+?\d[\d\s-]{7,}\d)")
    DATE_RE = re.compile(r"\b(\d{4}-\d{1,2}-\d{1,2})\b")

    def __init__(self) -> None:
        self.initialized = False
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        self.initialized = True
        self.logger.info("Slot extractor initialized")

    async def extract_slots(self, message: str, current_phase: str) -> Dict[str, Any]:
        """Extract basic slots from a user message."""
        slots: Dict[str, Any] = {}

        email_match = self.EMAIL_RE.search(message)
        if email_match:
            slots['email'] = email_match.group(0)

        phone_match = self.PHONE_RE.search(message)
        if phone_match:
            slots['phone'] = phone_match.group(0)

        date_match = self.DATE_RE.search(message)
        if date_match:
            slots.setdefault('dates', []).append(date_match.group(1))

        return slots
