# Changelog

All notable changes to this project will be documented in this file.

## [0.2.3] - 2025-08-30

### 🏗️ Architecture Refactoring
- **Modularized application.py**: Broke down 452-line monolith into focused modules (reduced to 246 lines)
  - `src/pantainos/core/asgi.py`: ASGI lifespan and web routes (135 lines)
  - `src/pantainos/db/initializer.py`: Database setup and repository DI (86 lines)
  - `src/pantainos/utils/runner.py`: Uvicorn integration with reload (101 lines)
  - `src/pantainos/core/lifecycle.py`: Component startup/shutdown (106 lines)

### 🐛 Bug Fixes
- **Fixed reload functionality**: Added `factory=True` parameter for uvicorn reload mode to prevent TypeError
- **Fixed import string detection**: Improved auto-detection of import strings for hot reload support

### ✨ Features
- **ASGI-first design**: Proper FastAPI integration with lifespan management
- **Hot reload support**: Smart import string detection for development workflow
- **Separation of concerns**: Each module handles specific responsibilities
- **Dependency injection**: Clean repository registration with DI container

### 🧪 Test Coverage
- **Added comprehensive test suites** for all new modules:
  - `tests/unit/core/test_asgi.py`: ASGI manager tests (10 tests)
  - `tests/unit/core/test_lifecycle.py`: Lifecycle management tests
  - `tests/unit/db/test_initializer.py`: Database initialization tests
  - `tests/unit/utils/test_runner.py`: Application runner tests
- **Improved ASGI coverage**: From 54% to comprehensive coverage

### 🔧 Development
- **CI/CD workflow**: Added GitHub Actions workflow for automated testing
- **Better error messages**: Improved uvicorn error handling and messaging
- **Testability**: All new modules have comprehensive unit tests with proper mocking

### ✅ Backward Compatibility
- **No breaking changes**: Existing Pantainos applications continue to work without modification
- **Maintained API**: All public interfaces remain unchanged

## [0.2.1] - 2025-08-30

### 🐛 Bug Fixes
- **Fixed GenericEvent event_type bug**: GenericEvent instances now maintain independent event_type values instead of sharing a class variable
- **Fixed debug logging colors**: Debug messages now appear in cyan instead of red for better visual distinction

### ✨ Features
- **Pre-push hooks**: Added comprehensive pre-push hooks that prevent bad code from reaching remote repository
  - Tests must pass before push
  - Linting checks (no auto-fix)
  - Format verification (no auto-format)
  - Allows flexible local commits while protecting remote

### 🛠️ Development
- **Linting script**: Added `scripts/lint.py` for manual linting with optional auto-fix
- **Development documentation**: Added DEVELOPMENT.md with complete setup instructions
- **Pre-commit/push configuration**: Configured hooks for code quality enforcement
- **Test coverage**: Added comprehensive tests for event models including regression tests

### 📦 Dependencies
- Added development dependencies:
  - `pre-commit>=4.3.0`
  - `isort>=6.0.1`
  - `mypy>=1.17.1`

### 📝 Documentation
- Updated README with clearer project description
- Added DEVELOPMENT.md for developer setup
- Improved code comments and docstrings

## [0.2.0] - 2025-08-29

### 🏗️ Architecture Changes
- **Major refactoring**: Reorganized codebase into cleaner module structure
- **Scheduler module**: Moved scheduler from core to dedicated module with typed models
- **Events module**: Created dedicated events module with conditions and models
- **Dependency injection**: Added comprehensive dependency injection system
- **Plugin manager**: Implemented plugin manager with lifecycle management

### 🔐 New Features
- **Authentication system**: Added AuthRepository for OAuth & API key management (32 tests)
- **Secure storage**: Implemented SecureStorageRepository for encrypted data (38 tests)
- **User management**: Added UserRepository for user management & platform linking (48 tests)
- **Plugin registry**: Enhanced plugin lifecycle management (22 tests)
- **Typed scheduler models**: Added proper Pydantic models for tasks & events (32 tests)

### 🧪 Test Suite Overhaul
- **Test reorganization**: Removed implementation tests, kept only functional unit tests
- **Path restructuring**: Reorganized all test paths to match source structure exactly
- **Pydantic v2 compatibility**: Fixed all Pydantic v2 compatibility issues
- **Test coverage**: Increased from 310 to 377 passing tests
- **Linting configuration**: Configured linting rules for test-specific patterns

### 🗑️ Removed
- Removed complex example applications to focus on core library
- Removed unused observability and twitch plugin examples
- Removed dashboard demos in favor of simpler examples

### 📦 Dependencies & Configuration
- Updated to Python 3.11+ with modern type hints
- Configured comprehensive linting with Ruff
- Added development dependencies for testing and quality

## [0.1.0] - 2025-08-29

### 🎉 Initial Release
- **Event-driven architecture**: Type-safe event bus with condition system
- **Plugin system**: Plugin architecture with lifecycle management and dependency injection
- **Database integration**: Repository pattern with event and variable storage
- **Scheduler**: Support for intervals, cron expressions, and database watch conditions
- **Web dashboard**: Event explorer and dashboard capabilities
- **Test suite**: Comprehensive test coverage (310 tests)
