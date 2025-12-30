import py_compile
from pathlib import Path

def summarize_errors():
    py_files = list(Path("src").rglob("*.py"))
    errors = []
    
    for py_file in py_files:
        try:
            py_compile.compile(str(py_file), doraise=True)
        except Exception as e:
            errors.append((py_file, str(e)))
            
    if not errors:
        print("No syntax errors found!")
        return
        
    print(f"Found {len(errors)} files with syntax errors:")
    # Group by error type
    from collections import Counter
    error_types = Counter()
    for file, msg in errors:
        type_name = "Other"
        if "IndentationError" in msg:
            type_name = "IndentationError"
        elif "SyntaxError: unterminated triple-quoted string literal" in msg:
            type_name = "Unterminated Triple Quote"
        elif "SyntaxError" in msg:
            type_name = "SyntaxError"
        error_types[type_name] += 1
        
    for type_name, count in error_types.items():
        print(f"  {type_name}: {count}")
        
    print("\nDetailed list (first 20):")
    for file, msg in errors[:20]:
        print(f"  {file}: {msg.strip().splitlines()[-1]}")

if __name__ == "__main__":
    summarize_errors()
