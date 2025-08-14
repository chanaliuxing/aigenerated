#!/usr/bin/env python3
"""
Manual test to verify service startup
"""

import asyncio
import os
import sys

import pytest

# Add the service directory to path
service_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, service_dir)


def test_service_startup():
    """Ensure service components initialize correctly"""
    pytest.importorskip("websockets")
    from main import WeChatAutomationService
    from logger import setup_logging

    async def run_check():
        service = WeChatAutomationService()
        await service.workflow_engine.initialize()
        await service.websocket_client.initialize()
        await service.workflow_engine.basic_actions.initialize()

        capabilities = service.workflow_engine.get_capabilities()
        assert isinstance(capabilities, dict)
        active_workflows = await service.workflow_engine.get_active_workflows()
        assert isinstance(active_workflows, list)

    asyncio.run(run_check())


def main():  # pragma: no cover - manual execution helper
    """Run the startup test manually"""
    print("WeChat Automation Service - Startup Test")
    print("=" * 50)
    test_service_startup()
    print("Startup test passed! The service can initialize properly.")
    print("Note: This test does not connect to the orchestrator.")


if __name__ == "__main__":  # pragma: no cover - manual run only
    main()
