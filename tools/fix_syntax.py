import os
import re

def fix_syntax_errors(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            # Fix unterminated single quotes
            if line.count("'") % 2 != 0:'
                # If there's a comment or it's a log/print/toast, close the quote before newline or comment
                if '#' in line:
                    parts = line.split('#', 1)
                    if parts[0].count("'") % 2 != 0:'
                        parts[0] = parts[0].rstrip() + "' "'
                    line = '#'.join(parts)
                else:
                    line = line.rstrip() + "'\n"'
            
            # Fix unterminated double quotes
            if line.count('"') % 2 != 0:"
                if '#' in line:
                    parts = line.split('#', 1)
                    if parts[0].count('"') % 2 != 0:"
                        parts[0] = parts[0].rstrip() + '" '"
                    line = '#'.join(parts)
                else:
                    line = line.rstrip() + '"\n'"
            
            # Remove characters that often cause SyntaxError in broken encoding
            line = line.replace(' ', ' ')
            new_lines.append(line)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")

def main():
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                if 'venv' in path or '.git' in path:
                    continue
                fix_syntax_errors(path)

if __name__ == '__main__':
    main()
 