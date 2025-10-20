# Contributing to md2cf

Thank you for your interest in contributing to md2cf! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git

### Setup Instructions

1. Fork the repository on GitHub

2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/md2cf.git
   cd md2cf
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   make install-dev
   # or
   pip install -e ".[dev]"
   ```

## Development Workflow

### Creating a Branch

Create a new branch for your feature or bugfix:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### Code Style

We follow these Python style guidelines:

- **PEP 8** for general Python style
- **Black** for code formatting (line length: 100)
- **isort** for import sorting
- **Type hints** for all functions and methods
- **Docstrings** for all public functions and classes

Format your code before committing:

```bash
make format
```

### Type Checking

Run type checking with mypy:

```bash
mypy md2cf
```

### Linting

Run the linter:

```bash
make lint
# or
ruff check md2cf tests
```

## Testing

### Running Tests

Run all tests:

```bash
make test
# or
pytest
```

Run tests with coverage:

```bash
make test-cov
# or
pytest --cov=md2cf --cov-report=html --cov-report=term
```

Run specific test files:

```bash
pytest tests/test_converter.py
```

Run specific test cases:

```bash
pytest tests/test_converter.py::TestBasicConversion::test_heading
```

### Writing Tests

- Write tests for all new features
- Aim for 100% code coverage
- Use pytest fixtures for reusable test setup
- Follow the Arrange-Act-Assert pattern
- Use descriptive test names

Example:

```python
def test_convert_heading_to_confluence() -> None:
    """Test that Markdown headings are converted to Confluence format."""
    # Arrange
    converter = MarkdownToConfluence()
    markdown = "# Test Heading"

    # Act
    result = converter.convert(markdown)

    # Assert
    assert "<h1>Test Heading</h1>" in result
```

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of the function.

    More detailed description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When parameter is invalid

    Example:
        >>> function_name("test", 42)
        True
    """
```

### README Updates

Update the README.md if you:
- Add new features
- Change API interfaces
- Add new dependencies
- Modify installation instructions

## Pull Request Process

1. **Update tests**: Ensure all tests pass and add new tests for your changes

2. **Update documentation**: Update README, docstrings, and comments as needed

3. **Run quality checks**:
   ```bash
   make format
   make lint
   make test-cov
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: Add feature description"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test changes
   - `refactor:` Code refactoring
   - `chore:` Maintenance tasks

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub with:
   - Clear title and description
   - Reference to related issues
   - Screenshots (if applicable)
   - Test results

## Code Review

Your PR will be reviewed for:

- **Functionality**: Does it work as expected?
- **Tests**: Are there adequate tests?
- **Code quality**: Is the code clean and well-documented?
- **Style**: Does it follow our coding standards?
- **Performance**: Are there any performance concerns?

## Release Process

Maintainers will handle releases following semantic versioning:

- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features, backward compatible
- **Patch** (0.0.X): Bug fixes, backward compatible

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/md2cf/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/md2cf/discussions)

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the project
- Show empathy towards other contributors

### Unacceptable Behavior

- Harassment or discriminatory language
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to open an issue for any questions about contributing!
