import pytest

pytest_plugins = ("pytester",)

from src import pytest_cov_optional


def test_registers_cov_options_when_plugin_missing(pytester, monkeypatch):
    monkeypatch.setattr(pytest_cov_optional, "_pytest_cov_installed", lambda: False)

    result = pytester.runpytest("--cov=src", "--cov-report=html", plugins=[pytest_cov_optional])

    assert result.ret != pytest.ExitCode.USAGE_ERROR


def test_registers_cov_config_option(pytester, monkeypatch):
    monkeypatch.setattr(pytest_cov_optional, "_pytest_cov_installed", lambda: False)

    result = pytester.runpytest(
        "--cov=src",
        "--cov-report=term",
        "--cov-config=.coveragerc",
        plugins=[pytest_cov_optional],
    )

    assert result.ret != pytest.ExitCode.USAGE_ERROR


def test_defers_when_plugin_present(monkeypatch):
    added_options = []

    class DummyParser:
        def getgroup(self, name):
            added_options.append(name)
            return self

        def addoption(self, *args, **kwargs):
            raise AssertionError("Should not register stub options when pytest-cov is present")

    monkeypatch.setattr(pytest_cov_optional, "_pytest_cov_installed", lambda: True)

    pytest_cov_optional.pytest_addoption(DummyParser())

    assert added_options == []
