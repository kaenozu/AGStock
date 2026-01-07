import os
import re

def clean_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Try to decode as utf-8, ignore errors to remove broken characters
        text = content.decode('utf-8', errors='ignore')
        
        # Remove common PowerShell-induced artifacts
        text = re.sub(r'', '', text)
        
        # Ensure common docstring quotes are closed (heuristic)
# FIXED SYNTAX: # FIXED SYNTAX: # FIXED SYNTAX: # FIXED SYNTAX: # FIXED SYNTAX: # FIXED SYNTAX: # FIXED SYNTAX: # FIXED SYNTAX: # FIXED SYNTAX: # FIXED SYNTAX:         # This is complex, but we can at least ensure we don t have dangling single quotes on comment lines
        lines = text.splitlines()
        new_lines = []
        for line in lines:
            # If a line has an odd number of quotes and looks like a broken comment, fix it
            if line.count('"') % 2 != 0 and ('#' in line or 'log' in line or 'print' in line):"
                line += '"'"
            new_lines.append(line)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        return True
    except Exception as e:
        print(f"Error cleaning {file_path}: {e}")
        return False

def main():
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                if 'venv' in path or '.git' in path:
                    continue
                clean_file(path)

if __name__ == '__main__':
    main() 