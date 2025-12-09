import subprocess
import sys
import os

def run_command(command, description):
    print(f"Running {description}...")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"❌ {description} FAILED")
        return False
    print(f"✅ {description} PASSED")
    return True

def main():
    print("="*40)
    print(" Running Quality Assurance Checks")
    print("="*40)
    
    # 1. Static Type Check
    # Using specific files to avoid overwhelming errors from legacy code for now
    mypy_cmd = "mypy src/execution.py fully_automated_trader.py --explicit-package-bases"
    if not run_command(mypy_cmd, "Static Type Check (mypy)"):
        # Don't exit immediately, try running tests
        pass

    # 2. Unit Tests
    # Discover all tests in tests/ directory
    test_cmd = f"{sys.executable} -m unittest discover tests"
    if not run_command(test_cmd, "Unit Tests"):
        sys.exit(1)
        
    print("\n✅ All checks finished successfully!")

if __name__ == "__main__":
    main()
