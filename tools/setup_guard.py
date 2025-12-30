import os
import subprocess
import sys

def setup_hook():
    hook_path = os.path.join(".git", "hooks", "pre-commit")
    
    hook_script = """#!/usr/bin/env python
import os
import sys
import subprocess

def main():
    print("🛡️ [Akashic Guard] Checking syntax for staged files...")
    
    # Get staged files
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True
    )
    staged_files = [f for f in result.stdout.splitlines() if f.endswith(".py") and "src_corrupted_backup" not in f]
    
    if not staged_files:
        print("No Python files staged. Skipping check.")
        return 0

    errors = 0
    for file_path in staged_files:
        if not os.path.exists(file_path):
            continue
            
        try:
            # Check with python's compile module
            subprocess.run([sys.executable, "-m", "py_compile", file_path], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ SYNTAX ERROR in {file_path}:")
            print(e.stderr.decode().strip())
            errors += 1

    if errors > 0:
        print(f"🛡️ [Akashic Guard] COMMIT REJECTED. Found {errors} syntax errors.")
        print("Please fix the errors and try again.")
        return 1

    print("✅ [Akashic Guard] All staged files are syntactically valid.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""

    try:
        if not os.path.exists(".git"):
            print("Error: Not a git repository.")
            return

        with open(hook_path, "w", encoding="utf-8") as f:
            f.write(hook_script)
        
        # On Unix, we would need chmod +x. On Windows, git execution might handle it differently, 
        # but typically git bash or WSL will respect it if we try to set it.
        # For Windows, git handles the execution.
        print(f"✅ Pre-commit hook created at {hook_path}")
        print("Akashic Guard is now active.")
    except Exception as e:
        print(f"Failed to setup hook: {e}")

if __name__ == "__main__":
    setup_hook()
