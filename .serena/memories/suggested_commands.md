- Install deps: `pip install -r requirements.txt`; dev deps: `pip install -r requirements-dev.txt`.
- Run app locally: `streamlit run app.py` (or double-click/run `run_app.bat`, which installs deps then launches Streamlit).
- Execute full test suite: `pytest tests -v`; with coverage: `pytest tests --cov=src --cov-report=html`.
- Helpful Windows/Powershell commands: `Get-ChildItem` (ls), `Set-Location <path>` (cd), `Get-Content <file>` (cat), `python <script>.py`, `pip list`, `git status`, `git diff`, `git checkout -b <branch>`. Use `.un_app.bat` to launch via batch script.