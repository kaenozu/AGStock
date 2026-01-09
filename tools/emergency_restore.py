import os
import subprocess

def restore_to_original_state():
    print("Force restoring all files to original paths from Git...")
    
    # Get all tracked files from HEAD
    try:
        output = subprocess.check_output(["git", "ls-tree", "-r", "HEAD", "--name-only"]).decode("utf-8")
        files = output.splitlines()
    except Exception as e:
        print(f"Failed to get file list: {e}")
        return

    for f in files:
        # Restore only if it's a python file or critical config
        if f.endswith(".py") or f.endswith(".json") or f.endswith(".bat"):
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(f), exist_ok=True) if os.path.dirname(f) else None
                # Restore content binary clean
                content = subprocess.check_output(["git", "show", f"HEAD:{f}"])
                with open(f, "wb") as out:
                    out.write(content)
                print(f"Restored: {f}")
            except Exception as e:
                print(f"Failed to restore {f}: {e}")

    # Cleanup failed refactoring folders inside src
    bad_folders = ["src/core", "src/ui", "src/trading", "src/models", "src/analysis", "src/data", "src/risk", "src/services", "src/utils"]
    import shutil
    for folder in bad_folders:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"Removed bad folder: {folder}")
            except: pass

if __name__ == "__main__":
    restore_to_original_state()
    print("Full restoration complete.")
