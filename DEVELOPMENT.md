# Development Setup - Linting & Pre-push Hooks

## 🚀 Overview

## ✅ What's Configured

### **Pre-commit Hooks** (basic file checks only)
- ✅ **Basic File Checks** - Trailing whitespace, end-of-file fixes, YAML validation
- ✅ **Fast Feedback** - Quick checks on every commit

### **Pre-push Hooks** (main quality gates)
- ✅ **Tests Must Pass** - All unit tests run before push
- ✅ **Linting Enforcement** - Ruff checks code quality (NO auto-fix)
- ✅ **Format Checking** - Ruff, isort, and black verify formatting (NO auto-format)
- ❌ **MyPy Disabled** - Too many type issues in current codebase

### **Key Behavior**
🔒 **BLOCKS PUSHES** if any check fails
🔒 **NO AUTO-FIXES** during pre-push (prevents surprise changes)
🔒 **LOCAL COMMITS ALLOWED** - You can commit WIP code locally
🔒 **REMOTE PROTECTED** - Only clean code reaches shared repository

## 🛠️ Available Commands

### Manual Linting & Formatting

```bash
# Check only (like pre-commit behavior)
uv run python scripts/lint.py

# Auto-fix issues (safe to run)
uv run python scripts/lint.py --fix
```

### Individual Tools

```bash
# Run tests
uv run python -m pytest tests/unit -q --tb=short

# Linting only
uv run ruff check src/ tests/ examples/

# Formatting only
uv run ruff format src/ tests/ examples/
uv run black src/ tests/ examples/
uv run isort src/ tests/ examples/
```

### Pre-commit Management

```bash
# Install hooks (already done)
uv run pre-commit install

# Run hooks on all files
uv run pre-commit run --all-files

# Update hook versions
uv run pre-commit autoupdate
```

## 🚫 What Blocks Pushes

**Pre-push checks (blocks git push):**
1. **Test Failures** - Any failing unit test
2. **Linting Issues** - Code quality problems (unused imports, missing annotations, etc.)
3. **Formatting Issues** - Code that would be reformatted by tools

**Pre-commit checks (quick, allows commit with warning):**
1. **File Issues** - Trailing whitespace, missing newlines, large files, etc.

## ✨ Example Workflow

```bash
# Make changes to code
vim src/pantainos/something.py

# Commit locally (WIP commits are fine!)
git add .
git commit -m "WIP: working on new feature"

# Keep working and committing locally
git commit -m "WIP: almost done"

# When ready to push, check everything
uv run python scripts/lint.py --fix

# Push to remote (will be blocked if issues exist)
git push origin main

# If blocked, fix issues and try again
uv run python scripts/lint.py --fix
git add .
git commit -m "Fix linting issues"
git push origin main
```

## 🎯 Benefits

- **Flexible Local Development** - Commit WIP code locally without restrictions
- **Protected Remote** - Only clean code reaches the shared repository
- **Zero Bad Code in Production** - Pre-push hooks prevent quality issues
- **Consistent Formatting** - All pushed code follows same style
- **Working Tests** - Every push has passing tests
- **No Surprises** - Hooks don't auto-fix during push
- **Fast Feedback** - Issues caught before push, not in CI

## 📝 Development Dependencies

All linting tools are installed as dev dependencies:

```bash
uv sync --group=dev
```

Includes:
- `ruff` - Fast Python linter & formatter
- `black` - Code formatter
- `isort` - Import sorter
- `mypy` - Type checker (available but not used in pre-commit)
- `pre-commit` - Git hook framework
- `pytest` - Testing framework
