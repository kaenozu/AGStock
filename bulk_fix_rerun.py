import os
import re

def replace_rerun(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    if "st.rerun()" in content:
                        print(f"Replacing st.rerun in {path}")
                        new_content = content.replace("st.rerun()", "st.experimental_rerun()")
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                except Exception as e:
                    print(f"Error processing {path}: {e}")

if __name__ == "__main__":
    replace_rerun("c:\\gemini-thinkpad\\AGStock\\src")
    # Also handle app.py
    app_path = "c:\\gemini-thinkpad\\AGStock\\app.py"
    try:
        with open(app_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "st.rerun()" in content:
            print(f"Replacing st.rerun in {app_path}")
            new_content = content.replace("st.rerun()", "st.experimental_rerun()")
            with open(app_path, "w", encoding="utf-8") as f:
                f.write(new_content)
    except Exception as e:
        print(f"Error processing {app_path}: {e}")
