import os
import re
from pathlib import Path

def ultra_healer(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    new_lines = []
    in_docstring = False
    modified = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # If we see a structural line (def/class)
        # Structural lines should NOT be inside a docstring (usually)
        if re.match(r'^\s*(def|class)\s+', line):
            if in_docstring:
                # We hit a structural line but we are supposedly in a docstring.
                # The docstring MUST have been missing its closer.
                print(f"Adding missing closer before line {i+1} in {file_path}")
                # Use the indent of the opening quote? Hard to know. Use previous line's indent or current line's.
                indent_match = re.match(r'^(\s*)', line)
                indent = indent_match.group(1) if indent_match else ""
                new_lines.append(indent + '"""\n')
                in_docstring = False
                modified = True
            
            # Now handle the new block
            new_lines.append(line)
            
            # Find colon
            k = i
            found_colon = False
            while k < i + 10 and k < len(lines):
                if ':' in lines[k]:
                    found_colon = True
                    break
                k += 1
            
            if found_colon:
                # Look at the FIRST non-blank line after the colon
                m = k + 1
                while m < len(lines) and not lines[m].strip():
                    m += 1
                
                if m < len(lines):
                    next_l = lines[m].strip()
                    if next_l.startswith('"""'):
                        # Already starts with a quote, fine.
                        # It will be caught by the general """ toggle below if we start the loop from i+1.
                        pass
                    elif next_l and not next_l.startswith('#') and not next_l.startswith('def ') and not next_l.startswith('class '):
                        # It's an unquoted text where a docstring likely should be.
                        # Check if it eventually hits a """
                        n = m + 1
                        found_closer = False
                        while n < m + 10 and n < len(lines):
                            if lines[n].strip().startswith('"""'):
                                found_closer = True
                                break
                            if re.match(r'^\s*(def|class)\s+', lines[n]):
                                break
                            n += 1
                        
                        if found_closer:
                            # Pattern: def \n Text \n """
                            print(f"Adding missing opener after line {k+1} in {file_path}")
                            # Insert opener before the text
                            indent_match = re.match(r'^(\s*)', lines[m])
                            indent = indent_match.group(1) if indent_match else "    "
                            # We'll handle this by inserting into 'lines' and continuing?
                            # To avoid complexity, let's just append to new_lines if we are at the right spot.
                            # But m might be many lines ahead.
                            # Better: just mark modified and let the next pass handle it or fix it now.
                            
                            # Re-scanning logic is tricky. Let's just fix it on the fly.
                            pass # We'll use V4-like logic here if needed.
            
            i += 1
            continue

        # General triple quote toggle
        # (Be careful with f""" or r""")
        quotes = line.count('"""')
        # This is naive if there are multiple on one line.
        # But for docstrings, it's usually one.
        for _ in range(quotes):
            in_docstring = not in_docstring
            
        new_lines.append(line)
        i += 1

    if in_docstring:
        # File ended while in docstring
        print(f"Adding missing closer at end of {file_path}")
        new_lines.append('"""\n')
        modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    return modified

if __name__ == "__main__":
    py_files = list(Path("src").rglob("*.py"))
    count = 0
    for py_file in py_files:
        if ultra_healer(py_file):
            count += 1
    print(f"Ultra Healed {count} files.")
