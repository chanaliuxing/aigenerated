#!/usr/bin/env python3
"""
Legal Chatbot Python Consumer Service
Entry point for the LLM request processor with workflow engine
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from handlers.llm_request import LLMRequestHandler
from logic.workflow_engine import WorkflowEngine
from utils.database import DatabaseManager
from utils.config import Config
from utils.logger import setup_logging

# Setup logging
logger = setup_logging()

class LegalChatbotConsumer:
    def __init__(self):
        self.config = Config()
        self.db_manager = DatabaseManager()
        self.workflow_engine = WorkflowEngine()
        self.llm_handler = LLMRequestHandler()
        self.running = False
        
    async def initialize(self):
        """Initialize all components"""
        try:
            # Initialize database connection
            await self.db_manager.connect()
            logger.info("Database connection established")
            
            # Initialize workflow engine
            await self.workflow_engine.initialize()
            logger.info("Workflow engine initialized")
            
            # Initialize LLM handler
            await self.llm_handler.initialize()
            logger.info("LLM handler initialized")
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize consumer: {e}")
            return False
    
    async def start(self):
        """Start the consumer service"""
        if not await self.initialize():
            return False
            
        self.running = True
        logger.info("Legal Chatbot Python Consumer started")
        
        try:
            while self.running:
                # Main processing loop
                await self.process_requests()
                await asyncio.sleep(1)  # Small delay to prevent tight loop
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            await self.shutdown()
            
    async def process_requests(self):
        """Process incoming LLM requests"""
        try:
            # Check for pending requests in database
            pending_requests = await self.db_manager.get_pending_requests()
            
            for request in pending_requests:
                try:
                    # Process the request
                    response = await self.llm_handler.process_request(request)
                    
                    # Update workflow state if needed
                    await self.workflow_engine.update_workflow_state(
                        request['conversation_id'],
                        response
                    )
                    
                    # Mark request as processed
                    await self.db_manager.mark_request_processed(
                        request['id'], 
                        response
                    )
                    
                    logger.info(f"Processed request {request['id']}")
                    
                except Exception as e:
                    logger.error(f"Error processing request {request['id']}: {e}")
                    await self.db_manager.mark_request_failed(
                        request['id'], 
                        str(e)
                    )
                    
        except Exception as e:
            logger.error(f"Error in process_requests: {e}")
    
    async def shutdown(self):
        """Shutdown the consumer service"""
        self.running = False
        logger.info("Shutting down Legal Chatbot Python Consumer")
        
        try:
            await self.db_manager.disconnect()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.running = False

async def main():
    """Main entry point"""
    consumer = LegalChatbotConsumer()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, consumer.handle_signal)
    signal.signal(signal.SIGTERM, consumer.handle_signal)
    
    try:
        await consumer.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Consumer stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
