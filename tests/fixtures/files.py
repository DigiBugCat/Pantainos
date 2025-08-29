"""
File manipulation utilities for integration and E2E tests
"""

import contextlib
import os
import tempfile
import time
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_python_file() -> Generator[Path, None, None]:
    """Create a temporary Python file for reload testing"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
        # Write initial content
        tmp_file.write(
            '''"""
Test module for reload testing
"""

def test_function():
    """Test function"""
    return "initial_value"

TEST_VARIABLE = "initial"
'''
        )
        tmp_file.flush()
        file_path = Path(tmp_file.name)

    try:
        yield file_path
    finally:
        # Cleanup
        with contextlib.suppress(FileNotFoundError):
            file_path.unlink()


@pytest.fixture
def temp_module_dir() -> Generator[Path, None, None]:
    """Create a temporary module directory structure"""
    with tempfile.TemporaryDirectory() as temp_dir:
        module_path = Path(temp_dir) / "test_module"
        module_path.mkdir()

        # Create __init__.py
        init_file = module_path / "__init__.py"
        init_file.write_text('"""Test module"""')

        # Create main module file
        main_file = module_path / "main.py"
        main_file.write_text(
            '''"""
Test module main file
"""

def get_value():
    return "original_value"
'''
        )

        yield module_path


class FileModifier:
    """Utility class for modifying files during tests"""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.original_content: str | None = None
        self.backup_content: str | None = None

    def backup(self) -> None:
        """Backup the current file content"""
        if self.file_path.exists():
            self.backup_content = self.file_path.read_text()

    def restore(self) -> None:
        """Restore the backed up content"""
        if self.backup_content is not None:
            self.file_path.write_text(self.backup_content)

    def modify(
        self, content: str | None = None, replacements: dict[str, str] | None = None, append: str | None = None
    ) -> None:
        """Modify the file content

        Args:
            content: Replace entire content with this
            replacements: Dict of old -> new replacements
            append: Append this content to the file
        """
        if not self.file_path.exists():
            if content:
                self.file_path.write_text(content)
            return

        current_content = self.file_path.read_text()

        if content:
            # Replace entire content
            new_content = content
        elif replacements:
            # Apply replacements
            new_content = current_content
            for old, new in replacements.items():
                new_content = new_content.replace(old, new)
        elif append:
            # Append content
            new_content = current_content + append
        else:
            return

        self.file_path.write_text(new_content)

        # Force file system to recognize the change
        os.sync()
        time.sleep(0.1)  # Small delay to ensure file system notices

    def touch(self) -> None:
        """Touch the file to update its modification time"""
        self.file_path.touch()
        time.sleep(0.1)

    def delete(self) -> None:
        """Delete the file"""
        if self.file_path.exists():
            self.file_path.unlink()

    def create_if_not_exists(self, content: str = "") -> None:
        """Create the file if it doesn't exist"""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.file_path.write_text(content)


@pytest.fixture
def file_modifier() -> Generator[type[FileModifier], None, None]:
    """Fixture that provides the FileModifier class"""
    yield FileModifier


def create_test_python_module(module_dir: Path, module_name: str, content: str = "") -> Path:
    """Create a test Python module in the given directory

    Args:
        module_dir: Directory to create the module in
        module_name: Name of the module (without .py extension)
        content: Content for the module file

    Returns:
        Path to the created module file
    """
    module_file = module_dir / f"{module_name}.py"
    module_file.parent.mkdir(parents=True, exist_ok=True)

    if not content:
        content = f'''"""
Test module: {module_name}
"""

def test_function():
    """Test function for {module_name}"""
    return "{module_name}_value"

MODULE_NAME = "{module_name}"
'''

    module_file.write_text(content)
    return module_file


def wait_for_file_change(file_path: Path, timeout: float = 5.0) -> bool:
    """Wait for a file to be modified

    Args:
        file_path: Path to the file to watch
        timeout: Maximum time to wait in seconds

    Returns:
        True if file was modified, False if timeout
    """
    if not file_path.exists():
        return False

    initial_mtime = file_path.stat().st_mtime
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            current_mtime = file_path.stat().st_mtime
            if current_mtime > initial_mtime:
                return True
        except FileNotFoundError:
            return False

        time.sleep(0.1)

    return False


def create_watchable_file(directory: Path, filename: str = "test_file.py") -> Path:
    """Create a file that can be used for watching tests

    Args:
        directory: Directory to create the file in
        filename: Name of the file to create

    Returns:
        Path to the created file
    """
    file_path = directory / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)

    content = f'''"""
Watchable test file: {filename}
Created for testing file watching functionality
"""

import time

def get_timestamp():
    """Return current timestamp"""
    return time.time()

def get_content():
    """Return file content identifier"""
    return "{filename}"

# Test variable
TEST_VAR = "original"
'''

    file_path.write_text(content)
    return file_path
