import os
import tokenize
import io

def rescue_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')
        
        # Remove any non-ASCII characters to prevent encoding issues during parse
        content = "".join(c for c in content if ord(c) <= 127)
        
        # Try to fix missing quotes using tokenize
        result = []
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(content).readline))
            for token in tokens:
                result.append(token.string)
        except tokenize.TokenError as e:
            # TokenError often means unterminated string
            if "multi-line string" in str(e) or "EOF in multi-line string" in str(e):
                content += '"""\n'
            elif "unterminated string literal" in str(e):
                content += ' \n'
        
        # If the file still fails to parse, it might be due to bad lines we added
        # Let s do a line-by-line quote check
        lines = content.splitlines()
        clean_lines = []
        for line in lines:
            # If a line has an odd number of quotes AND it s not a multi-line docstring start
            if line.count('"') % 2 != 0 and '"""' not in line:
                line = line.replace(' ', ' ')
            if line.count("'") % 2 != 0 and "'''" not in line:
                line = line.replace(" ",    )
            clean_lines.append(line)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(clean_lines))
        return True
    except Exception as e:
        print(f"Rescue failed for {file_path}: {e}")
        return False

def main():
    print("Starting final rescue operation...")
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                if 'venv' in path or '.git' in path:
                    continue
                rescue_file(path)
    print("Rescue operation finished.")

if __name__ == '__main__':
    main()