"""
WebSocket client for WeChat Automation Service
"""

import asyncio
import json
import logging
import websockets
from typing import Dict, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger('wechat_automation.websocket')

class WebSocketClient:
    """WebSocket client for communication with orchestrator"""
    
    def __init__(self):
        self.websocket = None
        self.url = None
        self.connected = False
        self.reconnecting = False
        self.on_message: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        self.on_connect: Optional[Callable] = None
        self.message_queue = []
        self.last_ping = None
        self.ping_interval = 30  # seconds
        
    async def initialize(self):
        """Initialize WebSocket client"""
        try:
            # Start ping task
            asyncio.create_task(self._ping_loop())
            logger.info("WebSocket client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket client: {e}")
            raise
    
    async def connect(self, url: str):
        """Connect to WebSocket server"""
        self.url = url
        
        try:
            logger.info(f"Connecting to WebSocket: {url}")
            self.websocket = await websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            self.connected = True
            logger.info("WebSocket connected successfully")
            
            # Start message handler
            asyncio.create_task(self._message_handler())
            
            # Send any queued messages
            await self._send_queued_messages()
            
            # Call connect callback
            if self.on_connect:
                await self.on_connect()
                
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            self.connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.websocket and self.connected:
            try:
                await self.websocket.close()
                logger.info("WebSocket disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting WebSocket: {e}")
            finally:
                self.connected = False
                self.websocket = None
    
    async def send_message(self, message: Dict[str, Any]):
        """Send message to WebSocket server"""
        if not self.connected or not self.websocket:
            # Queue message for later sending
            self.message_queue.append(message)
            logger.warning("WebSocket not connected, message queued")
            return
        
        try:
            message_str = json.dumps(message)
            await self.websocket.send(message_str)
            logger.debug(f"Sent message: {message.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            # Queue message for retry
            self.message_queue.append(message)
            raise
    
    async def _message_handler(self):
        """Handle incoming messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    logger.debug(f"Received message: {data.get('type', 'unknown')}")
                    
                    # Handle ping/pong
                    if data.get('type') == 'ping':
                        await self.send_message({'type': 'pong'})
                        continue
                    elif data.get('type') == 'pong':
                        self.last_ping = datetime.now()
                        continue
                    
                    # Call message handler
                    if self.on_message:
                        await self.on_message(data)
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.connected = False
            
            # Call disconnect handler
            if self.on_disconnect:
                await self.on_disconnect()
                
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            self.connected = False
    
    async def _send_queued_messages(self):
        """Send queued messages"""
        if not self.message_queue:
            return
        
        logger.info(f"Sending {len(self.message_queue)} queued messages")
        
        for message in self.message_queue.copy():
            try:
                await self.send_message(message)
                self.message_queue.remove(message)
            except Exception as e:
                logger.error(f"Failed to send queued message: {e}")
                break
    
    async def _ping_loop(self):
        """Send periodic ping messages"""
        while True:
            try:
                await asyncio.sleep(self.ping_interval)
                
                if self.connected and self.websocket:
                    await self.send_message({'type': 'ping'})
                    
            except Exception as e:
                logger.error(f"Error in ping loop: {e}")
    
    async def reconnect(self, max_attempts: int = 5, delay: int = 5):
        """Reconnect to WebSocket server"""
        if self.reconnecting:
            return
        
        self.reconnecting = True
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"Reconnection attempt {attempt + 1}/{max_attempts}")
                await asyncio.sleep(delay)
                
                await self.connect(self.url)
                logger.info("Reconnected successfully")
                self.reconnecting = False
                return True
                
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")
        
        logger.error("Failed to reconnect after all attempts")
        self.reconnecting = False
        return False
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.connected and self.websocket is not None
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            'url': self.url,
            'connected': self.connected,
            'reconnecting': self.reconnecting,
            'queued_messages': len(self.message_queue),
            'last_ping': self.last_ping.isoformat() if self.last_ping else None
        }
