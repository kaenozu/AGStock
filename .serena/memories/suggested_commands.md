# Suggested Commands

## Setup
- `make install`: Install dependencies and pre-commit hooks.
- `setup_wizard.py`: Interactive configuration.

## Development
- `make format`: Format code with Black.
- `make lint`: Run Flake8 and Black check.
- `make mypy`: Run type checker.
- `make check`: Run lint, mypy, and tests.

## Testing
- `make test`: Run all tests.
- `make test-smoke`: Run fast subset of tests.
- `make test-cov`: Run tests with coverage report.

## Execution
- `run_unified_dashboard.bat`: Start the main Streamlit dashboard.
- `run_morning_dashboard.bat`: Start the morning briefing dashboard.
- `run_weekend_advisor.bat`: Start the weekend strategy advisor.
- `python fully_automated_trader.py`: Start the automated trading engine.

## Maintenance
- `make clean`: Remove temporary files and caches.
- `make add-indexes`: Optimize SQLite database.
- `make clear-cache`: Flush memory cache.
