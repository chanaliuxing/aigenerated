#!/usr/bin/env python3
"""
Test script to verify WeChat automation service imports
"""

import sys
import os

# Add the service directory to path
service_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, service_dir)

def test_imports():
    """Test all imports"""
    print("Testing imports...")
    
    try:
        # Test basic imports
        from config import Config
        print("✓ Config imported successfully")
        
        from logger import setup_logging
        print("✓ Logger imported successfully")
        
        from websocket_client import WebSocketClient
        print("✓ WebSocketClient imported successfully")
        
        from engine import WorkflowEngine
        print("✓ WorkflowEngine imported successfully")
        
        from basic_actions import BasicActions
        print("✓ BasicActions imported successfully")
        
        from gui.system_tray import SystemTrayApp
        print("✓ SystemTrayApp imported successfully")
        
        print("\nAll imports successful!")
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_service_initialization():
    """Test service initialization"""
    print("\nTesting service initialization...")
    
    try:
        # Import the main service class
        from main import WeChatAutomationService
        
        # Create service instance
        service = WeChatAutomationService()
        print("✓ Service instance created successfully")
        
        # Test basic attributes
        assert hasattr(service, 'config'), "Service should have config attribute"
        assert hasattr(service, 'workflow_engine'), "Service should have workflow_engine attribute"
        assert hasattr(service, 'websocket_client'), "Service should have websocket_client attribute"
        
        print("✓ Service has all required attributes")
        
        print("\nService initialization test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Service initialization error: {e}")
        return False

def main():
    """Main test function"""
    print("WeChat Automation Service - Import Test")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        sys.exit(1)
    
    # Test service initialization
    if not test_service_initialization():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("All tests passed! The service should be able to start.")
    print("Note: PyQt5 warnings are expected if PyQt5 is not installed.")
    print("The service will use a dummy system tray implementation.")

if __name__ == "__main__":
    main()
