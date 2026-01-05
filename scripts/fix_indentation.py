import os
import re

def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        # コメント記号の後にコードが混ざっているパターン (# ? if ...)
        match = re.match(r'^(\s*)# \? \s+(if|self|from|import|def|class|return|yield|for|while|with|try|except|finally|raise|assert|async|await)\s+', line)
        if match:
            indent = match.group(1)
            code_part = line[len(match.group(0)) - len(match.group(2)):]
            new_lines.append(f"{indent}{code_part}")
            continue
        
        # 行の途中に # ? がある場合
        if " # ?" in line:
            parts = line.split(" # ?")
            new_lines.append(parts[0].rstrip() + "\n")
            continue
            
        new_lines.append(line)
        
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def main():
    for root, _, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                fix_file(os.path.join(root, file))
    print("Done fixing indentation/comment artifacts.")

if __name__ == "__main__":
    main()

