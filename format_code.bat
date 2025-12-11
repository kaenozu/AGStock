@echo off
echo Running code formatter...
black src/
black tests/
echo Code formatting completed.
pause