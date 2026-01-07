import os
import subprocess

def get_git_files():
    output = subprocess.check_output(["git", "ls-tree", "-r", "HEAD", "--name-only"]).decode('utf-8')
    return [f for f in output.splitlines() if f.startswith("src/")]

def determine_dest(path):
    filename = os.path.basename(path)
    if "ui" in path or filename.startswith("ui_") or filename in ["simple_dashboard.py", "visualizer.py", "shortcuts.py", "playbooks.py"]:
        return os.path.join("src/ui", filename)
    if "trading" in path or filename in ["paper_trader.py", "live_trading.py", "broker.py", "rakuten_broker.py"]:
        return os.path.join("src/trading", filename)
    if "models" in path or "predictor" in filename or filename in ["online_learning.py", "advanced_models.py", "bert_sentiment.py"]:
        return os.path.join("src/models", filename)
    if "analysis" in path or filename in ["fundamentals.py", "sentiment.py", "patterns.py", "regime.py"]:
        return os.path.join("src/analysis", filename)
    if "risk" in path or "guard" in filename or "limiter" in filename or "manager" in filename:
        if filename == "config_manager.py": return "src/core/config_manager.py"
        return os.path.join("src/risk", filename)
    if "data" in path or "loader" in filename or "processor" in filename or "manager" in filename:
        return os.path.join("src/data", filename)
    if "services" in path or "notifier" in filename or "system" in filename:
        return os.path.join("src/services", filename)
    if "utils" in path or filename in ["helpers.py", "formatters.py", "error_handling.py", "errors.py"]:
        return os.path.join("src/utils", filename)
    if filename in ["config.py", "constants.py", "types.py", "schemas.py", "logger_config.py"]:
        return os.path.join("src/core", filename)
    
    return path # Default

def restore_all():
    files = get_git_files()
    for f in files:
        dest = determine_dest(f)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        try:
            c = subprocess.check_output(["git", "show", f"HEAD:{f}"])
            with open(dest, "wb") as out: out.write(c)
            print(f"Restored {f} -> {dest}")
        except: pass

if __name__ == "__main__":
    restore_all()
