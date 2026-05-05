# Contributing to Dawnstar ReadAloud

Thank you for your interest in contributing to Dawnstar ReadAloud! This guide provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Architecture Overview](#architecture-overview)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Welcome contributors of all skill levels

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Dawnstar-ReadAloud.git
   cd Dawnstar-ReadAloud
   ```
3. **Set up the development environment** (see below)

## Development Setup

### Prerequisites

- Python 3.12 or higher
- pip and virtualenv
- System dependencies:
  ```bash
  # Ubuntu/Debian
  sudo apt install mpg123 xclip poppler-utils

  # Fedora
  sudo dnf install mpg123 xclip poppler
  ```

### Install Dependencies

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install with development dependencies
pip install -e ".[dev]"
```

### Verify Setup

```bash
# Run tests
pytest tests/ -v

# Run linter
ruff check core/ ttsd/ tests/

# Run type checker
mypy core/ ttsd/
```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feat/add-french-voice` - New features
- `fix/cache-eviction-bug` - Bug fixes
- `docs/update-readme` - Documentation
- `refactor/extract-url-validation` - Code refactoring
- `test/add-security-tests` - Test additions

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
feat: add French language support

- Add fr-FR voice configuration
- Update language detection
- Add tests for French TTS
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Build/config changes

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_security.py -v

# Run with coverage
pytest tests/ --cov=core --cov=ttsd --cov-report=html

# Run specific test category
pytest tests/ -v -k "security"
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use descriptive test function names: `test_<feature>_<scenario>_<expected>`
- Include docstrings explaining what the test verifies

Example:
```python
def test_path_traversal_blocks_absolute_path():
    """Should block absolute paths outside allowed directories."""
    config = TTSConfig()
    
    with pytest.raises(SecurityError) as exc_info:
        from_source("/etc/passwd", config)
    
    assert "Access denied" in str(exc_info.value)
```

### Test Categories

- **Unit tests**: Test individual functions/classes
- **Integration tests**: Test component interactions
- **Security tests**: Test security-critical code paths
- **Regression tests**: Test bug fixes don't reoccur

## Submitting Changes

### Pull Request Process

1. **Push your changes** to your fork:
   ```bash
   git push origin feat/your-feature-name
   ```

2. **Open a Pull Request** on GitHub:
   - Base branch: `main`
   - Title: Follow commit message format
   - Description: Explain what and why

3. **PR Description Template**:
   ```markdown
   ## Description
   Brief description of changes.

   ## Motivation
   Why these changes are needed.

   ## Testing
   - [ ] Tests pass locally
   - [ ] New tests added (if applicable)
   - [ ] Manual testing performed

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] No new warnings
   ```

4. **Address review feedback**:
   - Respond to comments
   - Make requested changes
   - Push updates to same branch

## Code Style

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use double quotes for strings

### Type Hints

```python
# Good
def process_text(text: str, max_length: int = 50000) -> str:
    """Process text and return cleaned version."""
    ...

# Bad - missing types
def process_text(text, max_length=50000):
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def generate_audio(text: str, timeout: int = 60) -> bytes:
    """Generate audio for text using TTS engine.

    Args:
        text: Text to convert to speech.
        timeout: Generation timeout in seconds.

    Returns:
        Audio data as bytes.

    Raises:
        TimeoutError: If generation exceeds timeout.
        RuntimeError: If TTS engine fails.
    """
```

### Error Handling

- Catch specific exceptions, not bare `except:`
- Use custom exceptions from `core/exceptions.py`
- Log errors with context

```python
# Good
try:
    audio = backend.generate_audio(text)
except subprocess.TimeoutExpired as e:
    Logger.log(f"Backend timeout: {e}", config)
    return None

# Bad
try:
    audio = backend.generate_audio(text)
except:
    return None
```

## Architecture Overview

### Project Structure

```
dawnstar-readaloud/
├── core/               # Core TTS modules
│   ├── cli.py          # Command-line interface
│   ├── config.py       # Runtime configuration
│   ├── constants.py    # Application constants
│   ├── engine.py       # TTS backends
│   ├── exceptions.py   # Custom exceptions
│   ├── extractor.py    # Content extraction
│   ├── platform.py     # Platform detection
│   └── ...
├── ttsd/               # Optional daemon
│   ├── daemon.py       # Daemon logic
│   └── ipc.py          # IPC communication
├── tests/              # Test suite
└── config.py           # App configuration
```

### Key Components

**TTSEngine** (`core/engine.py`):
- Manages TTS backends (Edge TTS, gTTS, eSpeak)
- Handles caching and fallback
- Shared event loop for async operations

**ContentExtractor** (`core/extractor.py`):
- Facade for all input sources
- Text cleaning and chunking
- File/URL/clipboard support

**AudioPlayer** (`core/player.py`):
- Auto-detects audio player
- Supports mpg123, paplay, vlc, ffplay

### Adding New Features

**New TTS Backend**:
1. Create class inheriting from `TTSBackend`
2. Implement `is_available()` and `generate_audio()`
3. Add to `TTSEngine.BACKEND_CLASSES`

**New Language**:
1. Add to `LANG_CONFIG` in `core/constants.py`
2. Add alias if needed in `LANG_ALIASES`
3. Update validation in `config.py`

**New CLI Command**:
1. Add argument to `_parse_args()` in `core/cli.py`
2. Add handler method `handle_*()`
3. Add dispatch in `run()`

## Getting Help

- **Issues**: Open a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check `README.md`, `USER_MANUAL.md`, `CLAUDE.md`

## Recognition

Contributors will be acknowledged in:
- README.md contributors section
- Release notes for significant contributions

---

Thank you for contributing to Dawnstar ReadAloud!
