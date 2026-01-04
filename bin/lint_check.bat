@echo off
echo Running linters...
flake8 src/ --config=.flake8
flake8 tests/ --config=.flake8
echo Lint check completed.
pause