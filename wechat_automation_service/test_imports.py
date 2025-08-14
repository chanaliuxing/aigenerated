#!/usr/bin/env python3
"""
Test script to verify WeChat automation service imports
"""

import os
import sys

import pytest

# Add the service directory to path
service_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, service_dir)


def test_imports():
    """Verify module imports succeed"""
    pytest.importorskip("websockets")
    from config import Config  # noqa: F401
    from logger import setup_logging  # noqa: F401
    from websocket_client import WebSocketClient  # noqa: F401
    from engine import WorkflowEngine  # noqa: F401
    from basic_actions import BasicActions  # noqa: F401
    from gui.system_tray import SystemTrayApp  # noqa: F401


def test_service_initialization():
    """Ensure main service initializes with required components"""
    pytest.importorskip("websockets")
    from main import WeChatAutomationService

    service = WeChatAutomationService()
    assert hasattr(service, "config")
    assert hasattr(service, "workflow_engine")
    assert hasattr(service, "websocket_client")


def main():  # pragma: no cover - manual execution helper
    """Run tests manually"""
    print("WeChat Automation Service - Import Test")
    print("=" * 50)
    test_imports()
    test_service_initialization()
    print("All tests passed! The service should be able to start.")
    print("Note: PyQt5 warnings are expected if PyQt5 is not installed.")
    print("The service will use a dummy system tray implementation.")


if __name__ == "__main__":  # pragma: no cover - manual run only
    main()
