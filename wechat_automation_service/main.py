#!/usr/bin/env python3
"""
WeChat Automation Service
Main entry point for desktop automation client
"""

import sys
import asyncio
import signal
import logging
from pathlib import Path
from typing import Optional

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from engine import WorkflowEngine
from websocket_client import WebSocketClient
from config import Config
from logger import setup_logging
from gui.system_tray import SystemTrayApp

logger = setup_logging()

class WeChatAutomationService:
    """Main WeChat automation service"""
    
    def __init__(self):
        self.config = Config()
        self.workflow_engine = WorkflowEngine()
        self.websocket_client = WebSocketClient()
        self.system_tray = None
        self.running = False
        
    async def initialize(self):
        """Initialize all components"""
        try:
            # Initialize workflow engine
            await self.workflow_engine.initialize()
            logger.info("Workflow engine initialized")
            
            # Initialize WebSocket client
            await self.websocket_client.initialize()
            logger.info("WebSocket client initialized")
            
            # Connect to orchestrator
            await self.websocket_client.connect(
                self.config.get('orchestrator.url', 'ws://localhost:3000')
            )
            logger.info("Connected to orchestrator")
            
            # Set up message handlers
            self.websocket_client.on_message = self.handle_message
            self.websocket_client.on_disconnect = self.handle_disconnect
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize service: {e}")
            return False
    
    async def start(self):
        """Start the automation service"""
        if not await self.initialize():
            return False
            
        self.running = True
        logger.info("WeChat Automation Service started")
        
        try:
            # Start system tray in separate thread
            import threading
            tray_thread = threading.Thread(target=self._start_system_tray)
            tray_thread.daemon = True
            tray_thread.start()
            
            # Main service loop
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            await self.shutdown()
            
    def _start_system_tray(self):
        """Start system tray application"""
        try:
            from PyQt5.QtWidgets import QApplication
            import sys
            
            app = QApplication(sys.argv)
            self.system_tray = SystemTrayApp(self)
            self.system_tray.show()
            app.exec_()
        except Exception as e:
            logger.error(f"Error starting system tray: {e}")
    
    async def handle_message(self, message: dict):
        """Handle incoming messages from orchestrator"""
        try:
            message_type = message.get('type')
            
            if message_type == 'execute_workflow':
                await self.execute_workflow(message)
            elif message_type == 'stop_workflow':
                await self.stop_workflow(message)
            elif message_type == 'get_status':
                await self.send_status()
            elif message_type == 'ping':
                await self.websocket_client.send_message({'type': 'pong'})
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def execute_workflow(self, message: dict):
        """Execute a workflow"""
        try:
            workflow_id = message.get('workflow_id')
            workflow_data = message.get('workflow_data')
            context = message.get('context', {})
            
            logger.info(f"Executing workflow: {workflow_id}")
            
            # Execute workflow
            result = await self.workflow_engine.execute_workflow(
                workflow_data, 
                context
            )
            
            # Send result back to orchestrator
            await self.websocket_client.send_message({
                'type': 'workflow_result',
                'workflow_id': workflow_id,
                'result': result,
                'success': True
            })
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            await self.websocket_client.send_message({
                'type': 'workflow_result',
                'workflow_id': workflow_id,
                'error': str(e),
                'success': False
            })
    
    async def stop_workflow(self, message: dict):
        """Stop a running workflow"""
        try:
            workflow_id = message.get('workflow_id')
            logger.info(f"Stopping workflow: {workflow_id}")
            
            await self.workflow_engine.stop_workflow(workflow_id)
            
            await self.websocket_client.send_message({
                'type': 'workflow_stopped',
                'workflow_id': workflow_id,
                'success': True
            })
            
        except Exception as e:
            logger.error(f"Error stopping workflow: {e}")
            await self.websocket_client.send_message({
                'type': 'workflow_stopped',
                'workflow_id': workflow_id,
                'error': str(e),
                'success': False
            })
    
    async def send_status(self):
        """Send current status to orchestrator"""
        try:
            status = {
                'type': 'status',
                'machine_id': self.config.get('machine.id'),
                'status': 'online' if self.running else 'offline',
                'active_workflows': await self.workflow_engine.get_active_workflows(),
                'capabilities': self.workflow_engine.get_capabilities(),
                'last_activity': self.workflow_engine.get_last_activity()
            }
            
            await self.websocket_client.send_message(status)
            
        except Exception as e:
            logger.error(f"Error sending status: {e}")
    
    async def handle_disconnect(self):
        """Handle WebSocket disconnection"""
        logger.warning("Disconnected from orchestrator")
        
        # Try to reconnect
        for attempt in range(5):
            try:
                await asyncio.sleep(5)  # Wait before reconnecting
                await self.websocket_client.connect(
                    self.config.get('orchestrator.url', 'ws://localhost:3000')
                )
                logger.info("Reconnected to orchestrator")
                return
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")
        
        logger.error("Failed to reconnect after 5 attempts")
    
    async def shutdown(self):
        """Shutdown the service"""
        self.running = False
        logger.info("Shutting down WeChat Automation Service")
        
        try:
            # Stop all workflows
            await self.workflow_engine.stop_all_workflows()
            
            # Disconnect WebSocket
            await self.websocket_client.disconnect()
            
            # Close system tray
            if self.system_tray:
                self.system_tray.close()
                
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.running = False

async def main():
    """Main entry point"""
    service = WeChatAutomationService()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, service.handle_signal)
    signal.signal(signal.SIGTERM, service.handle_signal)
    
    try:
        await service.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
