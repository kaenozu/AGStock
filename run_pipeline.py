import subprocess
import sys
import os
import time
from typing import List

def run_script(path: str) -> bool:
    print(f"Running {path}...")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    try:
        result = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=300, encoding="utf-8", env=env)
        if result.returncode == 0:
            print(f"✅ {path} passed.")
            return True
        else:
            print(f"❌ {path} failed with return code {result.returncode}.")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"⚠️ Error running {path}: {e}")
        return False

def main():
    scripts_to_run = [
        "scripts/verifications/verify_phase52.py",
        "scripts/verifications/verify_performance_risk.py",
        "scripts/verifications/verify_committee_backend.py",
    ]
    
    # Auto-discover others if needed
    # for f in os.listdir("scripts/verifications"):
    #     if f.startswith("verify_") and f.endswith(".py"):
    #         scripts_to_run.append(os.path.join("scripts/verifications", f))

    print("=== AGStock Automated Verification Pipeline ===")
    start_time = time.time()
    
    results = []
    for script in scripts_to_run:
        if os.path.exists(script):
            results.append((script, run_script(script)))
        else:
            print(f"⏩ {script} not found, skipping.")

    passed = [r[0] for r in results if r[1]]
    failed = [r[0] for r in results if not r[1]]
    
    print("\n=== Summary ===")
    print(f"Total: {len(results)}")
    print(f"Passed: {len(passed)}")
    print(f"Failed: {len(failed)}")
    print(f"Time: {time.time() - start_time:.2f}s")
    
    if failed:
        sys.exit(1)

if __name__ == "__main__":
    main()
