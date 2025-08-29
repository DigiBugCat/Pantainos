"""
Process management utilities for integration and E2E tests
"""

import asyncio
import os
import signal
import subprocess
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import psutil
import pytest


class StarStreamerProcess:
    """Manage a StarStreamer process for testing"""

    def __init__(
        self,
        cwd: Path | None = None,
        reload: bool = False,
        port: int = 8899,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        self.cwd = cwd or Path.cwd()
        self.reload = reload
        self.port = port
        self.timeout = timeout
        self.kwargs = kwargs
        self.process: subprocess.Popen[bytes] | None = None
        self.stdout_lines: list[str] = []
        self.stderr_lines: list[str] = []

    async def start(self) -> None:
        """Start the StarStreamer process"""
        cmd = [
            "uv",
            "run",
            "python",
            "src/main.py",
            "--web-port",
            str(self.port),
        ]

        if self.reload:
            cmd.append("--reload")

        # Add any additional arguments
        for key, value in self.kwargs.items():
            if isinstance(value, bool) and value:
                cmd.append(f"--{key.replace('_', '-')}")
            elif not isinstance(value, bool):
                cmd.extend([f"--{key.replace('_', '-')}", str(value)])

        # Set up environment with test configuration
        test_env = dict(os.environ)
        test_env["CONFIG_FILE"] = "tests/fixtures/test_config.yaml"

        self.process = subprocess.Popen(  # - Test utilities need subprocess
            cmd,
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            env=test_env,
        )

        # Wait for startup
        await self.wait_for_startup()

    async def wait_for_startup(self) -> None:
        """Wait for the process to start and be ready"""
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            if self.process is None:
                raise RuntimeError("Process not started")

            # Check if process is still running
            if self.process.poll() is not None:
                # Process has terminated, read output for debugging
                stdout, stderr = self.process.communicate()
                raise RuntimeError(
                    f"Process terminated during startup. "
                    f"Return code: {self.process.returncode}\n"
                    f"Stdout: {stdout}\n"
                    f"Stderr: {stderr}"
                )

            # Read available output
            self._read_output_nonblocking()

            # Check for startup indicators in the output
            if self._is_ready():
                return

            await asyncio.sleep(0.1)

        raise TimeoutError(f"Process did not start within {self.timeout} seconds")

    def _read_output_nonblocking(self) -> None:
        """Read available output without blocking"""
        if self.process is None:
            return

        # Read stdout using polling
        if self.process.stdout:
            try:
                import fcntl
                import select

                # Set non-blocking mode
                fd = self.process.stdout.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

                # Check if data is available
                ready, _, _ = select.select([self.process.stdout], [], [], 0)
                if ready:
                    try:
                        data = self.process.stdout.read()
                        if data:
                            lines = data.strip().split("\n")
                            self.stdout_lines.extend([line.strip() for line in lines if line.strip()])
                    except BlockingIOError:
                        pass
            except (ImportError, OSError):
                # Fallback for systems without fcntl/select
                pass

        # Read stderr using polling
        if self.process.stderr:
            try:
                import fcntl
                import select

                # Set non-blocking mode
                fd = self.process.stderr.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

                # Check if data is available
                ready, _, _ = select.select([self.process.stderr], [], [], 0)
                if ready:
                    try:
                        data = self.process.stderr.read()
                        if data:
                            lines = data.strip().split("\n")
                            self.stderr_lines.extend([line.strip() for line in lines if line.strip()])
                    except BlockingIOError:
                        pass
            except (ImportError, OSError):
                # Fallback for systems without fcntl/select
                pass

    def _is_ready(self) -> bool:
        """Check if the process is ready based on output"""
        # Look for startup indicators
        for line in self.stdout_lines + self.stderr_lines:
            if "Uvicorn running on" in line or "Application startup complete" in line:
                return True
        return False

    def send_signal(self, sig: signal.Signals) -> None:
        """Send a signal to the process"""
        if self.process and self.process.poll() is None:
            self.process.send_signal(sig)

    async def stop(self) -> None:
        """Stop the process gracefully"""
        if self.process is None:
            return

        if self.process.poll() is None:
            # Try graceful shutdown first
            self.process.terminate()

            try:
                async with asyncio.timeout(10.0):
                    await self._wait_for_process()
            except TimeoutError:
                # Force kill if graceful shutdown failed
                self.process.kill()
                await self._wait_for_process()

    async def _wait_for_process(self) -> None:
        """Wait for the process to terminate"""
        if self.process is None:
            return

        # Use asyncio to wait for process completion more efficiently
        await asyncio.get_event_loop().run_in_executor(None, self.process.wait)

    def get_output(self) -> tuple[list[str], list[str]]:
        """Get the current stdout and stderr output"""
        self._read_output_nonblocking()
        return self.stdout_lines.copy(), self.stderr_lines.copy()

    def get_pid(self) -> int | None:
        """Get the process ID"""
        return self.process.pid if self.process else None

    def is_running(self) -> bool:
        """Check if the process is running"""
        return self.process is not None and self.process.poll() is None

    async def restart(self) -> None:
        """Restart the process"""
        await self.stop()
        await self.start()


@pytest.fixture
async def starstreamer_process() -> AsyncIterator[StarStreamerProcess]:
    """Fixture that provides a StarStreamer process for testing"""
    process = StarStreamerProcess()
    try:
        await process.start()
        yield process
    finally:
        await process.stop()


@pytest.fixture
async def starstreamer_process_with_reload() -> AsyncIterator[StarStreamerProcess]:
    """Fixture that provides a StarStreamer process with reload enabled"""
    process = StarStreamerProcess(reload=True)
    try:
        await process.start()
        yield process
    finally:
        await process.stop()


def kill_processes_by_name(name: str) -> None:
    """Kill all processes with the given name"""
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if name in proc.info["name"] or any(name in arg for arg in (proc.info["cmdline"] or [])):
                proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


def kill_processes_on_port(port: int) -> None:
    """Kill all processes listening on the given port"""
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.pid:
            try:
                proc = psutil.Process(conn.pid)
                proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass


@pytest.fixture(autouse=True)
def cleanup_processes():
    """Automatically cleanup test processes after each test"""
    yield
    # Cleanup any remaining test processes
    kill_processes_by_name("starstreamer")
    kill_processes_on_port(8899)  # Default test port


def wait_for_port_available(port: int, timeout: float = 10.0) -> bool:
    """Wait for a port to become available

    Args:
        port: Port number to check
        timeout: Maximum time to wait

    Returns:
        True if port becomes available, False if timeout
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Check if port is in use
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                time.sleep(0.1)
                break
        else:
            # Port is available
            return True

    return False


def wait_for_port_in_use(port: int, timeout: float = 10.0) -> bool:
    """Wait for a port to be in use

    Args:
        port: Port number to check
        timeout: Maximum time to wait

    Returns:
        True if port becomes in use, False if timeout
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Check if port is in use
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                return True
        time.sleep(0.1)

    return False
