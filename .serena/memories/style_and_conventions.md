# Style and Conventions

## Formatting
- **Tool**: Black
- **Line Length**: 120 characters
- **Target Versions**: Python 3.8 to 3.11 (though README mentions 3.12)

## Linting
- **Tool**: Flake8
- **Scope**: `src/` and `tests/`

## Type Checking
- **Tool**: Mypy
- **Python Version**: 3.10
- **Configuration**: Strict optional checking, warns on unused configs and redundant casts.

## Testing
- **Framework**: Pytest
- **Markers**: `slow`, `integration`, `unit`
- **Coverage**: Tracked for `src/` using `pytest-cov`

## Code Structure
- Flat but massive `src/` directory.
- Use of sub-packages for specific domains (e.g., `src/ui`, `src/trading`, `src/agents`).
- Automation scripts at the root (many `.py` and `.bat` files).
