"""
Tests for ApplicationRunner
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from pantainos.utils.runner import ApplicationRunner


@pytest.fixture
def mock_app():
    """Create a mock Pantainos app instance."""
    app = MagicMock()
    app.return_value = MagicMock()  # Mock ASGI app
    return app


@pytest.fixture
def runner(mock_app):
    """Create ApplicationRunner with mock app."""
    return ApplicationRunner(mock_app)


def test_run_without_reload(runner, mock_app):
    """Test running application without reload mode."""
    mock_uvicorn = MagicMock()

    with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
        runner.run(host="localhost", port=8000)

    mock_uvicorn.run.assert_called_once_with(mock_app(), host="localhost", port=8000)


def test_run_with_workers_error(runner):
    """Test that multiple workers raises an error."""
    mock_uvicorn = MagicMock()

    with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
        with pytest.raises(RuntimeError, match="Multiple workers feature is unsupported"):
            runner.run(workers=2)


def test_run_uvicorn_not_available(runner):
    """Test error when uvicorn is not available."""
    # Remove uvicorn from sys.modules temporarily
    uvicorn_module = sys.modules.pop("uvicorn", None)

    try:
        # Mock the import to raise ImportError
        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: (
                (_ for _ in ()).throw(ImportError("No module named 'uvicorn'"))
                if name == "uvicorn"
                else __import__(name, *args, **kwargs)
            ),
        ):
            with pytest.raises(RuntimeError, match="uvicorn not available"):
                runner.run()
    finally:
        # Restore uvicorn module if it existed
        if uvicorn_module is not None:
            sys.modules["uvicorn"] = uvicorn_module


def test_run_with_reload_success(runner, mock_app):
    """Test running with reload mode when import string is detected."""
    mock_uvicorn = MagicMock()

    with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
        with patch.object(runner, "_get_import_string", return_value="test_module:app"):
            runner.run(reload=True, host="localhost")

    mock_uvicorn.run.assert_called_once_with("test_module:app", reload=True, host="localhost")


def test_run_with_reload_no_import_string(runner):
    """Test running with reload mode when import string cannot be detected."""
    mock_uvicorn = MagicMock()

    with patch.dict("sys.modules", {"uvicorn": mock_uvicorn}):
        with patch.object(runner, "_get_import_string", return_value=None):
            with pytest.raises(RuntimeError, match="Could not auto-detect import string"):
                runner.run(reload=True)


def test_filename_to_module_valid(runner):
    """Test converting valid filename to module name."""
    with patch("pantainos.utils.runner.Path") as mock_path_class:
        # Mock Path.cwd()
        mock_cwd = MagicMock()
        mock_path_class.cwd.return_value = mock_cwd

        # Mock Path(filename)
        mock_file_path = MagicMock()
        mock_path_class.return_value = mock_file_path

        # Mock the relative_to() chain
        mock_rel_path = MagicMock()
        mock_file_path.relative_to.return_value = mock_rel_path

        # Mock with_suffix() and parts
        mock_module_path = MagicMock()
        mock_rel_path.with_suffix.return_value = mock_module_path
        mock_module_path.parts = ("src", "pantainos", "app")

        result = runner._filename_to_module("/path/to/src/pantainos/app.py")

        assert result == "src.pantainos.app"


def test_filename_to_module_not_python(runner):
    """Test that non-Python files return None."""
    result = runner._filename_to_module("/path/to/file.txt")
    assert result is None


def test_filename_to_module_relative_error(runner):
    """Test handling of relative path errors."""
    with patch("pathlib.Path.cwd") as mock_cwd, patch("pathlib.Path") as mock_path_class:
        # Mock the Path constructor to return an object that raises ValueError on relative_to
        mock_path = MagicMock()
        mock_path_class.return_value = mock_path
        mock_path.relative_to.side_effect = ValueError("Different drives")

        result = runner._filename_to_module("/path/to/app.py")

        assert result is None


def test_get_import_string_not_found(runner):
    """Test _get_import_string when app instance is not found in any frame."""
    # This test is hard to mock properly due to inspect.stack() complexity
    # but we can at least ensure it returns None when no match found
    result = runner._get_import_string()
    assert result is None  # Should return None when not found in any frame


def test_filename_to_module_empty_result(runner):
    """Test that empty module name returns None."""
    with patch("pathlib.Path.cwd") as mock_cwd, patch("pathlib.Path") as mock_path_class:
        # Mock to return empty parts
        mock_path = MagicMock()
        mock_path_class.return_value = mock_path
        mock_path.relative_to.return_value.with_suffix.return_value.parts = ()

        result = runner._filename_to_module("/app.py")

        assert result is None
