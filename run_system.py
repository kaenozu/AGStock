import subprocess
import time
import sys
import os

def main():
    print("🚀 AGStock System Launcher")
    print("--------------------------------")
    print("1. Starting Scheduler (Background)...")
    # Use python executable relative to current env if possible, else just 'python'
    python_exe = sys.executable
    
    # scheduler.py logs to console, so we might want to capture it or let it share console?
    # For now, let it share user console or just run in background.
    scheduler_process = subprocess.Popen([python_exe, "scheduler.py"], cwd=os.getcwd())
    
    print("2. Starting Streamlit Dashboard...")
    ui_process = subprocess.Popen([python_exe, "-m", "streamlit", "run", "app.py"], cwd=os.getcwd())
    
    print("✅ All systems go! Press Ctrl+C to stop.")
    print("--------------------------------")

    try:
        while True:
            time.sleep(1)
            # Check if processes are alive
            if scheduler_process.poll() is not None:
                print("⚠️ Scheduler has stopped unexpectedly!")
                break
            if ui_process.poll() is not None:
                print("⚠️ UI Dashboard has stopped!")
                break
    except KeyboardInterrupt:
        print("\n🛑 Stopping systems...")
        scheduler_process.terminate()
        ui_process.terminate()
        print("Done.")

if __name__ == "__main__":
    main()
