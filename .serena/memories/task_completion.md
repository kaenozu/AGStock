# Task Completion Checklist

Before finishing a task, ensure the following steps are performed:

1. **Format Code**:
   ```bash
   make format
   ```
2. **Lint Check**:
   ```bash
   make lint
   ```
3. **Type Check**:
   ```bash
   make mypy
   ```
4. **Run Tests**:
   ```bash
   make test
   ```
   (Or `make test-smoke` for quick verification)

5. **Verify Configuration**:
   ```bash
   make config-validate
   ```

6. **Documentation**:
   If new functions or modules were added, ensure they have proper docstrings and update relevant `.md` files in `docs/` if necessary.
