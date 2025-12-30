"""bare except句を修正するスクリプト"""
import os
import re
from pathlib import Path

def fix_bare_except_in_file(filepath: str) -> tuple[bool, int]:
    """ファイル内のbare exceptを修正"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return False, 0
    
    original = content
    count = 0
    
    # パターン1: except: (単独行)
    pattern1 = re.compile(r'^(\s*)except:\s*$', re.MULTILINE)
    content, n = pattern1.subn(r'\1except Exception:', content)
    count += n
    
    # パターン2: except: の後にコメントがある場合
    pattern2 = re.compile(r'^(\s*)except:\s*(#.*)$', re.MULTILINE)
    content, n = pattern2.subn(r'\1except Exception:  \2', content)
    count += n
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, count
    
    return False, 0

def main():
    src_dir = Path("src")
    total_fixed = 0
    files_modified = 0
    
    for pyfile in src_dir.rglob("*.py"):
        modified, count = fix_bare_except_in_file(str(pyfile))
        if modified:
            print(f"✅ Fixed {count} bare except(s) in {pyfile}")
            total_fixed += count
            files_modified += 1
    
    # ルートディレクトリのPythonファイルも
    for pyfile in Path(".").glob("*.py"):
        modified, count = fix_bare_except_in_file(str(pyfile))
        if modified:
            print(f"✅ Fixed {count} bare except(s) in {pyfile}")
            total_fixed += count
            files_modified += 1
    
    print(f"\n✅ Total: {total_fixed} bare except(s) fixed in {files_modified} files")

if __name__ == "__main__":
    main()
