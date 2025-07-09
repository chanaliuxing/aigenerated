"""
Phase management utilities for Legal Chatbot
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.config import Config
from utils.database import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)

class PhaseManager:
    """Manages conversation phases and transitions"""
    
    def __init__(self):
        self.config = Config()
        self.db_manager = DatabaseManager()
        self.workflow_config = self.config.get_workflow_config()
        self.initialized = False
    
    async def initialize(self):
        """Initialize the phase manager"""
        try:
            self.initialized = True
            logger.info("Phase manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize phase manager: {e}")
            raise
    
    async def determine_next_phase(self, current_phase: str, message: str, ai_response: str, 
                                 slots: Dict[str, Any], context: List[Dict[str, Any]]) -> str:
        """
        Determine the next phase based on current state and conditions
        
        Args:
            current_phase: Current conversation phase
            message: User message
            ai_response: AI response
            slots: Extracted slots
            context: Conversation context
            
        Returns:
            Next phase name
        """
        try:
            # Check for explicit phase transitions in AI response
            explicit_phase = self._extract_phase_from_response(ai_response)
            if explicit_phase:
                logger.info(f"Explicit phase transition found: {current_phase} -> {explicit_phase}")
                return explicit_phase
            
            # Get branch flow rules for current phase
            branch_rules = await self.db_manager.get_branch_flow_rules(current_phase)
            
            # Evaluate conditions for phase transitions
            for rule in branch_rules:
                if await self._evaluate_condition(rule, message, ai_response, slots, context):
                    logger.info(f"Condition met for phase transition: {current_phase} -> {rule['to_phase']}")
                    return rule['to_phase']
            
            # Check for automatic transitions based on time or message count
            if await self._should_auto_transition(current_phase, context):
                next_phase = await self._get_next_sequential_phase(current_phase)
                if next_phase:
                    logger.info(f"Auto transition: {current_phase} -> {next_phase}")
                    return next_phase
            
            # No transition conditions met, stay in current phase
            return current_phase
            
        except Exception as e:
            logger.error(f"Error determining next phase: {e}")
            return current_phase
    
    def _extract_phase_from_response(self, ai_response: str) -> Optional[str]:
        """Extract explicit phase transition from AI response"""
        # Look for phase transition markers in the response
        import re
        
        patterns = [
            r'\[NEXT_PHASE:([A-Z_]+)\]',
            r'<PHASE_TRANSITION>([A-Z_]+)</PHASE_TRANSITION>',
            r'TRANSITION_TO:([A-Z_]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, ai_response)
            if match:
                return match.group(1)
        
        return None
    
    async def _evaluate_condition(self, rule: Dict[str, Any], message: str, ai_response: str, 
                                slots: Dict[str, Any], context: List[Dict[str, Any]]) -> bool:
        """Evaluate a branch flow condition"""
        try:
            condition_type = rule['condition_type']
            condition_data = rule.get('condition_data', {})
            
            if condition_type == 'sufficient_info':
                return await self._check_sufficient_info(condition_data, slots, context)
            elif condition_type == 'analysis_complete':
                return await self._check_analysis_complete(condition_data, ai_response, slots)
            elif condition_type == 'client_interest':
                return await self._check_client_interest(condition_data, message, context)
            elif condition_type == 'message_count':
                return await self._check_message_count(condition_data, context)
            elif condition_type == 'time_elapsed':
                return await self._check_time_elapsed(condition_data, context)
            elif condition_type == 'keyword_match':
                return await self._check_keyword_match(condition_data, message)
            elif condition_type == 'slot_filled':
                return await self._check_slot_filled(condition_data, slots)
            else:
                logger.warning(f"Unknown condition type: {condition_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    async def _check_sufficient_info(self, condition_data: Dict[str, Any], 
                                   slots: Dict[str, Any], context: List[Dict[str, Any]]) -> bool:
        """Check if sufficient information has been collected"""
        min_messages = condition_data.get('min_messages', 3)
        required_fields = condition_data.get('required_fields', [])
        
        # Check message count
        user_messages = [msg for msg in context if msg['sender_type'] == 'user']
        if len(user_messages) < min_messages:
            return False
        
        # Check required fields
        for field in required_fields:
            if field not in slots or not slots[field]:
                return False
        
        return True
    
    async def _check_analysis_complete(self, condition_data: Dict[str, Any], 
                                     ai_response: str, slots: Dict[str, Any]) -> bool:
        """Check if case analysis is complete"""
        confidence_threshold = condition_data.get('confidence_threshold', 0.8)
        
        # Look for analysis indicators in AI response
        analysis_indicators = [
            'analysis complete',
            'assessment shows',
            'legal assessment',
            'case strength',
            'recommendation',
            'next steps'
        ]
        
        response_lower = ai_response.lower()
        indicator_count = sum(1 for indicator in analysis_indicators if indicator in response_lower)
        
        # Simple confidence calculation based on indicators
        confidence = min(indicator_count / len(analysis_indicators), 1.0)
        
        return confidence >= confidence_threshold
    
    async def _check_client_interest(self, condition_data: Dict[str, Any], 
                                   message: str, context: List[Dict[str, Any]]) -> bool:
        """Check if client shows interest in proceeding"""
        interest_indicators = condition_data.get('interest_indicators', [
            'pricing', 'cost', 'fee', 'timeline', 'next steps', 'proceed', 'continue', 'hire'
        ])
        
        message_lower = message.lower()
        
        # Check for interest indicators
        for indicator in interest_indicators:
            if indicator in message_lower:
                return True
        
        return False
    
    async def _check_message_count(self, condition_data: Dict[str, Any], 
                                 context: List[Dict[str, Any]]) -> bool:
        """Check if message count threshold is met"""
        min_count = condition_data.get('min_count', 5)
        max_count = condition_data.get('max_count', 50)
        
        user_messages = [msg for msg in context if msg['sender_type'] == 'user']
        message_count = len(user_messages)
        
        return min_count <= message_count <= max_count
    
    async def _check_time_elapsed(self, condition_data: Dict[str, Any], 
                                context: List[Dict[str, Any]]) -> bool:
        """Check if enough time has elapsed"""
        min_minutes = condition_data.get('min_minutes', 10)
        
        if not context:
            return False
        
        first_message = context[0]
        last_message = context[-1]
        
        # Calculate time difference
        time_diff = last_message['created_at'] - first_message['created_at']
        elapsed_minutes = time_diff.total_seconds() / 60
        
        return elapsed_minutes >= min_minutes
    
    async def _check_keyword_match(self, condition_data: Dict[str, Any], message: str) -> bool:
        """Check if message contains specific keywords"""
        keywords = condition_data.get('keywords', [])
        message_lower = message.lower()
        
        for keyword in keywords:
            if keyword.lower() in message_lower:
                return True
        
        return False
    
    async def _check_slot_filled(self, condition_data: Dict[str, Any], 
                               slots: Dict[str, Any]) -> bool:
        """Check if specific slots are filled"""
        required_slots = condition_data.get('required_slots', [])
        
        for slot_name in required_slots:
            if slot_name not in slots or not slots[slot_name]:
                return False
        
        return True
    
    async def _should_auto_transition(self, current_phase: str, context: List[Dict[str, Any]]) -> bool:
        """Check if automatic transition should occur"""
        if not self.workflow_config.get('auto_transition', True):
            return False
        
        # Check timeout
        timeout_minutes = self.workflow_config.get('phase_timeout', 30)
        if context:
            last_message = context[-1]
            elapsed = (datetime.now() - last_message['created_at']).total_seconds() / 60
            if elapsed > timeout_minutes:
                return True
        
        return False
    
    async def _get_next_sequential_phase(self, current_phase: str) -> Optional[str]:
        """Get the next sequential phase in the workflow"""
        phase_sequence = [
            'INFO_COLLECTION',
            'CASE_ANALYSIS',
            'PRODUCT_RECOMMENDATION',
            'SALES_CONVERSION'
        ]
        
        try:
            current_index = phase_sequence.index(current_phase)
            if current_index < len(phase_sequence) - 1:
                return phase_sequence[current_index + 1]
        except ValueError:
            pass
        
        return None
    
    async def get_phase_info(self, phase_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific phase"""
        try:
            async with self.db_manager.pool.acquire() as conn:
                query = """
                    SELECT name, display_name, description, order_index
                    FROM legalbot.phases
                    WHERE name = $1 AND active = true
                """
                
                row = await conn.fetchrow(query, phase_name)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting phase info: {e}")
            return None
    
    async def get_all_phases(self) -> List[Dict[str, Any]]:
        """Get all available phases"""
        try:
            async with self.db_manager.pool.acquire() as conn:
                query = """
                    SELECT name, display_name, description, order_index
                    FROM legalbot.phases
                    WHERE active = true
                    ORDER BY order_index
                """
                
                rows = await conn.fetch(query)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all phases: {e}")
            return []
