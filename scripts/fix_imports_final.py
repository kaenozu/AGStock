import os
import re

def fix_imports():
    pattern = re.compile(r'agstock\.src\.')
    count = 0
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    if "src." in content:
                        new_content = content.replace("src.", "src.")
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        print(f"✅ Fixed: {path}")
                        count += 1
                except Exception as e:
                    print(f"❌ Error in {path}: {e}")
    print(f"Done! Updated {count} files.")

if __name__ == "__main__":
    fix_imports()
