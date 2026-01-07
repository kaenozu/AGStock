import os

def clean_non_ascii():
    print("Aggressively cleaning ALL non-ASCII characters from ALL .py files...")
    for root, dirs, files in os.walk('src'):
        for file in files:
            if not file.endswith('.py'): continue
            path = os.path.join(root, file)
            try:
                with open(path, "rb") as f:
                    content = f.read()
                
                # Decode ignoring errors, then encode back to clean ASCII
                clean_text = content.decode('utf-8', errors='ignore')
                clean_text = "".join(c for c in clean_text if ord(c) <= 127)
                
                with open(path, "w", encoding="utf-8") as f:
                    f.write(clean_text)
            except Exception as e:
                print(f"Failed to clean {path}: {e}")
    
    # Also clean entry points
    for p in ["app.py", "fully_automated_trader.py"]:
        if os.path.exists(p):
            with open(p, "rb") as f: content = f.read()
            clean_text = content.decode('utf-8', errors='ignore')
            clean_text = "".join(c for c in clean_text if ord(c) <= 127)
            with open(p, "w", encoding="utf-8") as f: f.write(clean_text)

if __name__ == "__main__":
    clean_non_ascii()
