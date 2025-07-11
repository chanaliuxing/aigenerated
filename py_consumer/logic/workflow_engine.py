"""Simplified workflow engine for Python consumer service.
This placeholder tracks conversation workflow states so the
consumer can update progress after each LLM request.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Minimal workflow engine storing per-conversation state."""

    def __init__(self):
        # Mapping of conversation_id -> workflow data
        self._states: Dict[str, Dict[str, Any]] = {}
        self.initialized = False

    async def initialize(self):
        """Initialize workflow engine."""
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
        return state

    def get_state(self, conversation_id: str) -> Dict[str, Any]:
        """Return stored state for a conversation."""
        return self._states.get(conversation_id, {})
