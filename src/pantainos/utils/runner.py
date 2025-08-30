"""
Application runner utilities for Pantainos.

This module provides uvicorn integration and import string auto-detection
for running Pantainos applications with hot reload support.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pantainos.application import Pantainos


class ApplicationRunner:
    """
    Manages application running with uvicorn integration.

    Provides run functionality with auto-detection of import strings
    for reload mode support.
    """

    def __init__(self, app: Pantainos) -> None:
        """Initialize runner with Pantainos app instance."""
        self.app = app

    def run(self, **kwargs: Any) -> None:
        """Run the application using uvicorn."""
        try:
            import uvicorn
        except ImportError as e:
            raise RuntimeError("uvicorn not available. Install with: pip install uvicorn") from e

        # Block workers mode
        workers = kwargs.get("workers")
        if workers and workers > 1:
            raise RuntimeError("Multiple workers feature is unsupported")

        # Handle reload mode by auto-detecting import string
        if kwargs.get("reload"):
            import_string = self._get_import_string()
            if import_string:
                uvicorn.run(import_string, **kwargs)
                return
            # Fallback to error message if auto-detection fails
            raise RuntimeError(
                "Could not auto-detect import string for reload mode. Use uvicorn directly:\n"
                "import uvicorn\n"
                'uvicorn.run("module.path:app", reload=True, ...)'
            )

        uvicorn.run(self.app(), **kwargs)

    def _get_import_string(self) -> str | None:
        """Auto-detect the import string for reload mode by inspecting the call stack."""
        # Walk up the stack to find the calling module
        for frame_info in inspect.stack():
            frame = frame_info.frame
            filename = frame_info.filename

            # Skip internal frames
            if "pantainos" in filename or "uvicorn" in filename:
                continue

            # Look for our app instance in the frame's globals
            for name, obj in frame.f_globals.items():
                if obj is self.app:
                    # Convert file path to module path
                    module_name = self._filename_to_module(filename)
                    if module_name:
                        return f"{module_name}:{name}"

        return None

    def _filename_to_module(self, filename: str) -> str | None:
        """Convert a filename to a module import string."""
        # Remove .py extension
        if not filename.endswith(".py"):
            return None

        # Get current working directory to make relative paths
        cwd = Path.cwd()
        file_path = Path(filename)

        # Make path relative to current directory
        try:
            rel_path = file_path.relative_to(cwd)
        except ValueError:
            # Paths on different drives (Windows) or other issues
            return None

        # Remove .py extension and convert to module name
        module_path = rel_path.with_suffix("")

        # Convert path parts to module name
        module_name = ".".join(module_path.parts)

        return module_name if module_name else None
