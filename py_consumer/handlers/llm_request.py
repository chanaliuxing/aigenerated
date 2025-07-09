"""
LLM Request Handler for Legal Chatbot Python Consumer
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from utils.config import Config
from utils.database import DatabaseManager
from utils.logger import get_logger
from logic.phase_utils import PhaseManager
from logic.slot_utils import SlotExtractor
from logic.prompt_engine import PromptEngine
from providers.openai_provider import OpenAIProvider
from providers.deepseek_provider import DeepSeekProvider

logger = get_logger(__name__)

class LLMRequestHandler:
    """Main handler for LLM requests with workflow support"""
    
    def __init__(self):
        self.config = Config()
        self.db_manager = DatabaseManager()
        self.phase_manager = PhaseManager()
        self.slot_extractor = SlotExtractor()
        self.prompt_engine = PromptEngine()
        self.ai_providers = {}
        self.initialized = False
    
    async def initialize(self):
        """Initialize the LLM request handler"""
        try:
            # Initialize AI providers
            self.ai_providers['openai'] = OpenAIProvider(self.config)
            self.ai_providers['deepseek'] = DeepSeekProvider(self.config)
            
            # Initialize components
            await self.phase_manager.initialize()
            await self.slot_extractor.initialize()
            await self.prompt_engine.initialize()
            
            self.initialized = True
            logger.info("LLM request handler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize LLM request handler: {e}")
            raise
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an LLM request
        
        Args:
            request: Request dictionary containing message, conversation_id, etc.
            
        Returns:
            Response dictionary with content, metadata, and next_phase
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            conversation_id = request['conversation_id']
            message = request['message']
            current_phase = request.get('current_phase', 'INFO_COLLECTION')
            
            logger.info(f"Processing request for conversation {conversation_id}, phase: {current_phase}")
            
            # Get conversation context
            context = await self.db_manager.get_conversation_context(conversation_id)
            
            # Get conversation details
            conversation = await self.db_manager.get_conversation_details(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Extract slots from message
            slots = await self.slot_extractor.extract_slots(message, current_phase)
            
            # Build prompt using prompt engine
            prompt_data = await self.prompt_engine.build_prompt(
                message=message,
                context=context,
                phase=current_phase,
                slots=slots,
                conversation=conversation
            )
            
            # Determine AI provider
            provider_name = self.config.get('app.default_ai_provider', 'openai')
            provider = self.ai_providers.get(provider_name)
            
            if not provider:
                raise ValueError(f"AI provider {provider_name} not available")
            
            # Generate AI response
            ai_response = await provider.generate_response(prompt_data)
            
            # Determine next phase
            next_phase = await self.phase_manager.determine_next_phase(
                current_phase=current_phase,
                message=message,
                ai_response=ai_response['content'],
                slots=slots,
                context=context
            )
            
            # Update conversation phase if changed
            if next_phase != current_phase:
                await self.db_manager.update_conversation_phase(conversation_id, next_phase)
            
            # Save AI response
            response_metadata = {
                'provider': provider_name,
                'phase': current_phase,
                'next_phase': next_phase,
                'slots': slots,
                'tokens_used': ai_response.get('tokens_used', 0),
                'processing_time': ai_response.get('processing_time', 0)
            }
            
            await self.db_manager.save_ai_response(
                conversation_id=conversation_id,
                content=ai_response['content'],
                metadata=response_metadata
            )
            
            logger.info(f"Request processed successfully for conversation {conversation_id}")
            
            return {
                'content': ai_response['content'],
                'metadata': response_metadata,
                'next_phase': next_phase,
                'slots': slots
            }
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            raise
    
    async def process_batch_requests(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple requests concurrently"""
        max_concurrent = self.config.get('processing.max_concurrent_requests', 10)
        
        async def process_single(request):
            try:
                return await self.process_request(request)
            except Exception as e:
                logger.error(f"Error processing request {request.get('id', 'unknown')}: {e}")
                return {
                    'error': str(e),
                    'request_id': request.get('id')
                }
        
        # Process requests with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(request):
            async with semaphore:
                return await process_single(request)
        
        tasks = [process_with_semaphore(request) for request in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    async def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get a summary of the conversation"""
        try:
            conversation = await self.db_manager.get_conversation_details(conversation_id)
            context = await self.db_manager.get_conversation_context(conversation_id, limit=50)
            
            if not conversation or not context:
                return {}
            
            # Extract key information
            user_messages = [msg for msg in context if msg['sender_type'] == 'user']
            ai_messages = [msg for msg in context if msg['sender_type'] == 'assistant']
            
            # Get extracted slots from all messages
            all_slots = {}
            for msg in user_messages:
                slots = await self.slot_extractor.extract_slots(msg['content'], conversation['current_phase'])
                all_slots.update(slots)
            
            return {
                'conversation_id': conversation_id,
                'current_phase': conversation['current_phase'],
                'status': conversation['status'],
                'total_messages': len(context),
                'user_messages': len(user_messages),
                'ai_messages': len(ai_messages),
                'extracted_slots': all_slots,
                'last_activity': context[-1]['created_at'] if context else None,
                'contact_name': conversation.get('contact_name'),
                'contact_email': conversation.get('contact_email')
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the LLM request handler"""
        try:
            health_status = {
                'handler_initialized': self.initialized,
                'database_healthy': await self.db_manager.health_check(),
                'ai_providers': {}
            }
            
            # Check AI providers
            for name, provider in self.ai_providers.items():
                try:
                    health_status['ai_providers'][name] = await provider.health_check()
                except Exception as e:
                    health_status['ai_providers'][name] = {'healthy': False, 'error': str(e)}
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {'healthy': False, 'error': str(e)}
