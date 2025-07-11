"""Simplified workflow engine for Python consumer service.
This placeholder tracks conversation workflow states so the
consumer can update progress after each LLM request.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Minimal workflow engine storing per-conversation state."""

    def __init__(self) -> None:
        # Mapping of conversation_id -> workflow data
        self._states: Dict[str, Dict[str, Any]] = {}
        self.initialized = False
        self._state_file = Path(__file__).parent.parent / 'workflow_state.json'

    async def initialize(self):
        """Initialize workflow engine."""
        if self.initialized:
            return
        if self._state_file.exists():
            try:
                self._states = json.loads(self._state_file.read_text())
            except Exception:  # pragma: no cover - corrupt file
                self._states = {}
        self.initialized = True
        logger.info("Workflow engine initialized")

    async def update_workflow_state(self, conversation_id: str, response: Dict[str, Any]):
        """Update stored workflow state for a conversation.

        Parameters
        ----------
        conversation_id: str
            Identifier of the conversation being updated.
        response: Dict[str, Any]
            Response returned from the LLM handler containing
            next_phase and slots information.
        """
        if not self.initialized:
            await self.initialize()

        state = self._states.setdefault(conversation_id, {})
        state['last_response'] = response
        state['current_phase'] = response.get('next_phase', state.get('current_phase'))
        logger.debug("Workflow state updated for %s: %s", conversation_id, state)
        try:
            self._state_file.write_text(json.dumps(self._states, indent=2))
        except Exception as exc:  # pragma: no cover - disk issues
            logger.error("Failed to persist workflow state: %s", exc)
        return state

    def get_state(self, conversation_id: str) -> Dict[str, Any]:
        """Return stored state for a conversation."""
        return self._states.get(conversation_id, {})
