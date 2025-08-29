"""
Tests for Pantainos.run() method
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_application_has_run_method():
    """Test that Pantainos has run method"""
    from pantainos.application import Pantainos

    app = Pantainos()

    # Should have run method
    assert hasattr(app, "run")
    assert callable(app.run)


@pytest.mark.asyncio
async def test_run_starts_application_properly():
    """Test that run() properly starts and stops the application"""
    from pantainos.application import Pantainos

    app = Pantainos()
    app.start = AsyncMock()
    app.stop = AsyncMock()

    # Create a task that will stop after a short delay
    async def stop_after_delay():
        await asyncio.sleep(0.1)
        raise KeyboardInterrupt

    # Run the app with a timeout
    with patch("asyncio.Event.wait", side_effect=stop_after_delay):
        await app.run()

    # Should have called start and stop
    app.start.assert_called_once()
    app.stop.assert_called_once()
