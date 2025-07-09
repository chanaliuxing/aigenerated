"""
Database manager for Legal Chatbot Python Consumer
"""

import asyncio
import asyncpg
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """Async database manager for PostgreSQL"""
    
    def __init__(self):
        self.config = Config()
        self.db_config = self.config.get_database_config()
        self.pool = None
        self.connected = False
    
    async def connect(self):
        """Establish database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                max_size=self.db_config['max_connections'],
                min_size=2
            )
            self.connected = True
            logger.info("Database connection pool established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            self.connected = False
            logger.info("Database connection pool closed")
    
    async def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get pending LLM requests from the database"""
        try:
            async with self.pool.acquire() as conn:
                # For now, we'll simulate pending requests by checking for new messages
                # In a real implementation, you might have a separate requests table
                query = """
                    SELECT 
                        m.id,
                        m.conversation_id,
                        m.content as message,
                        m.metadata,
                        m.created_at,
                        c.current_phase,
                        c.contact_id,
                        c.user_id
                    FROM legalbot.messages m
                    JOIN legalbot.conversations c ON m.conversation_id = c.id
                    WHERE m.sender_type = 'user' 
                    AND m.id NOT IN (
                        SELECT DISTINCT conversation_id 
                        FROM legalbot.messages 
                        WHERE sender_type = 'assistant' 
                        AND created_at > m.created_at
                    )
                    AND m.created_at > NOW() - INTERVAL '1 hour'
                    ORDER BY m.created_at ASC
                    LIMIT 10
                """
                
                rows = await conn.fetch(query)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting pending requests: {e}")
            return []
    
    async def get_conversation_context(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation context for a given conversation"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT 
                        id,
                        sender_type,
                        content,
                        metadata,
                        created_at
                    FROM legalbot.messages
                    WHERE conversation_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """
                
                rows = await conn.fetch(query, conversation_id, limit)
                return [dict(row) for row in reversed(rows)]
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return []
    
    async def get_conversation_details(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation details"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT 
                        c.*,
                        ct.name as contact_name,
                        ct.email as contact_email
                    FROM legalbot.conversations c
                    LEFT JOIN legalbot.contacts ct ON c.contact_id = ct.id
                    WHERE c.id = $1
                """
                
                row = await conn.fetchrow(query, conversation_id)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting conversation details: {e}")
            return None
    
    async def save_ai_response(self, conversation_id: str, content: str, metadata: Dict[str, Any]):
        """Save AI response to the database"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    INSERT INTO legalbot.messages (conversation_id, sender_type, content, metadata)
                    VALUES ($1, 'assistant', $2, $3)
                    RETURNING id
                """
                
                result = await conn.fetchrow(query, conversation_id, content, json.dumps(metadata))
                logger.info(f"AI response saved with ID: {result['id']}")
                return result['id']
        except Exception as e:
            logger.error(f"Error saving AI response: {e}")
            raise
    
    async def update_conversation_phase(self, conversation_id: str, phase: str):
        """Update conversation phase"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    UPDATE legalbot.conversations 
                    SET current_phase = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                """
                
                await conn.execute(query, phase, conversation_id)
                logger.info(f"Conversation {conversation_id} phase updated to {phase}")
        except Exception as e:
            logger.error(f"Error updating conversation phase: {e}")
            raise
    
    async def get_prompt_template(self, phase: str) -> Optional[Dict[str, Any]]:
        """Get prompt template for a specific phase"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT 
                        id,
                        template_name,
                        template_content,
                        variables
                    FROM legalbot.prompt_templates
                    WHERE phase = $1 AND active = true
                    ORDER BY version DESC
                    LIMIT 1
                """
                
                row = await conn.fetchrow(query, phase)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting prompt template: {e}")
            return None
    
    async def get_branch_flow_rules(self, from_phase: str) -> List[Dict[str, Any]]:
        """Get branch flow rules for phase transitions"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT 
                        to_phase,
                        condition_type,
                        condition_data,
                        priority
                    FROM legalbot.branch_flow
                    WHERE from_phase = $1 AND active = true
                    ORDER BY priority DESC
                """
                
                rows = await conn.fetch(query, from_phase)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting branch flow rules: {e}")
            return []
    
    async def mark_request_processed(self, request_id: str, response: Dict[str, Any]):
        """Mark a request as processed (placeholder implementation)"""
        # In a real implementation, you might update a requests table
        logger.info(f"Request {request_id} marked as processed")
    
    async def mark_request_failed(self, request_id: str, error: str):
        """Mark a request as failed (placeholder implementation)"""
        # In a real implementation, you might update a requests table
        logger.error(f"Request {request_id} marked as failed: {error}")
    
    async def get_knowledge_base_entries(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get knowledge base entries for RAG (placeholder implementation)"""
        try:
            async with self.pool.acquire() as conn:
                # Simple text search - in production, use vector similarity
                search_query = """
                    SELECT 
                        id,
                        title,
                        content,
                        document_type,
                        category,
                        metadata
                    FROM legalbot.knowledge_base
                    WHERE active = true
                    AND (title ILIKE $1 OR content ILIKE $1)
                    ORDER BY title
                    LIMIT $2
                """
                
                rows = await conn.fetch(search_query, f"%{query}%", limit)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting knowledge base entries: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("SELECT 1 as health")
                return result['health'] == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
