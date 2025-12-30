import py_compile
import subprocess
from pathlib import Path

def check_untracked():
    # Get untracked files
    try:
        output = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], encoding='utf-8')
        untracked = [line.strip() for line in output.splitlines() if line.endswith('.py')]
    except:
        print("Git failed")
        return

    print(f"Checking {len(untracked)} untracked Python files...")
    errors = 0
    for f in untracked:
        try:
            py_compile.compile(f, doraise=True)
        except Exception as e:
            print(f"  {f}: {str(e).strip().splitlines()[-1]}")
            errors += 1
    
    print(f"Found {errors} errors in untracked files.")

if __name__ == "__main__":
    check_untracked()
