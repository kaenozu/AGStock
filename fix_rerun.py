"""
st.rerun() を st.experimental_rerun() に一括置換するスクリプト (エンコーディング対応版)
"""
import pathlib

def replace_rerun():
    src_path = pathlib.Path('src')
    count = 0
    encodings = ['utf-8', 'shift_jis', 'cp932', 'latin-1']
    
    for py_file in src_path.rglob('*.py'):
        content = None
        used_encoding = None
        
        # Try different encodings
        for enc in encodings:
            try:
                content = py_file.read_text(encoding=enc)
                used_encoding = enc
                break
            except (UnicodeDecodeError, LookupError):
                continue
        
        if content is None:
            print(f"Skipped (encoding error): {py_file}")
            continue
        
        if 'st.rerun()' in content:
            try:
                new_content = content.replace('st.rerun()', 'st.experimental_rerun()')
                py_file.write_text(new_content, encoding='utf-8')  # Always write as UTF-8
                count += 1
                print(f"Updated: {py_file} (was {used_encoding})")
            except Exception as e:
                print(f"Error writing {py_file}: {e}")
    
    print(f"\nTotal files updated: {count}")

if __name__ == "__main__":
    replace_rerun()
