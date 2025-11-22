"""Project-level pytest configuration.

Loads the optional pytest-cov fallback plugin so coverage flags in
``pytest.ini`` do not break test runs when ``pytest-cov`` is absent.
"""

from src.pytest_cov_optional import pytest_addoption

__all__ = ["pytest_addoption"]
