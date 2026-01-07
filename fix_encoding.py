import os

def force_utf8(root_dir):
    for root, dirs, files in os.walk(root_dir):
        if ".venv" in root or ".git" in root:
            continue
        for file in files:
            if file.endswith(".py") or file.endswith(".css") or file.endswith(".json") or file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    # Try common encodings to read
                    content = None
                    for enc in ["utf-8-sig", "utf-8", "cp932", "shift-jis", "latin-1"]:
                        try:
                            with open(file_path, "r", encoding=enc) as f:
                                content = f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if content is not None:
                        # Force save as plain UTF-8 (no BOM)
                        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
                            f.write(content)
                        # print(f"Normalized: {file_path}")
                except Exception as e:
                    print(f"Error normalized {file_path}: {e}")

if __name__ == "__main__":
    force_utf8(".")
