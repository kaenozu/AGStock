import os
import re

def aggressive_clean(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            # Check if line contains non-ASCII characters
            if any(ord(c) > 127 for c in line):
                # If it s a log or string assignment, replace the string content with ASCII
                # Simple heuristic: look for "..." or '...' containing non-ASCII
                line = re.sub(r'"[^"(Message Cleaned)"]*"', '"(Message Cleaned)"', line)
                line = re.sub(r'\'[^"(Message Cleaned)"]*\'', "'(Message Cleaned)'", line)
                
                # If still contains non-ASCII (e.g., comments), comment out the rest of the line or remove non-ASCII
                if any(ord(c) > 127 for c in line):
                    # Remove any remaining non-ASCII characters
                    line = "".join(c for c in line if ord(c) <= 127)
            
            new_lines.append(line)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"Error cleaning {file_path}: {e}")

def main():
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                if 'venv' in path or '.git' in path:
                    continue
                aggressive_clean(path)

if __name__ == '__main__':
    main()