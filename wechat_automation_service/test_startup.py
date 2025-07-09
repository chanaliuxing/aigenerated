#!/usr/bin/env python3
"""
Manual test to verify service startup
"""

import sys
import os
import asyncio

# Add the service directory to path
service_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, service_dir)

async def test_service_startup():
    """Test service startup without running main loop"""
    from main import WeChatAutomationService
    from logger import setup_logging
    
    logger = setup_logging()
    logger.info("Starting service startup test")
    
    try:
        # Create service instance
        service = WeChatAutomationService()
        logger.info("Service instance created")
        
        # Test initialization without connecting to orchestrator
        logger.info("Testing component initialization...")
        
        # Test workflow engine initialization
        await service.workflow_engine.initialize()
        logger.info("Workflow engine initialized successfully")
        
        # Test WebSocket client initialization
        await service.websocket_client.initialize()
        logger.info("WebSocket client initialized successfully")
        
        # Test basic actions initialization
        await service.workflow_engine.basic_actions.initialize()
        logger.info("Basic actions initialized successfully")
        
        logger.info("All components initialized successfully!")
        
        # Test some basic functionality
        capabilities = service.workflow_engine.get_capabilities()
        logger.info(f"Available capabilities: {capabilities}")
        
        active_workflows = await service.workflow_engine.get_active_workflows()
        logger.info(f"Active workflows: {len(active_workflows)}")
        
        logger.info("Service startup test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Service startup test failed: {e}")
        return False

def main():
    """Main test function"""
    print("WeChat Automation Service - Startup Test")
    print("=" * 50)
    
    result = asyncio.run(test_service_startup())
    
    if result:
        print("\n" + "=" * 50)
        print("Startup test passed! The service can initialize properly.")
        print("Note: This test does not connect to the orchestrator.")
    else:
        print("\n" + "=" * 50)
        print("Startup test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
