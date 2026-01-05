import os
import re
from pathlib import Path

def repair_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        # 1. 壊れた日本語（マルチバイト文字の残骸）を削除または置換
        # 非ASCII文字を一旦削除するか、特定のパターンを正規表現で掃除
        # ここでは「構文エラー」の原因となる「閉じられていない文字列」や「不正な文字」をターゲットにします
        
        # 文字列リテラル内の壊れた文字を掃除
        def clean_match(match):
            s = match.group(0)
            # 文字列内の非ASCIIを削除（または?に置換）
            return re.sub(r'[^\x00-\x7F]+', '?', s)

        # f-string, triple quotes, single/double quotes
        content = re.sub(r'f?""".*?"""', clean_match, content, flags=re.DOTALL)
        content = re.sub(r"f?'''.*?'''", clean_match, content, flags=re.DOTALL)
        content = re.sub(r'f?".*?"', clean_match, content)
        content = re.sub(r"f?'.*?'", clean_match, content)
        
        # コメント内の壊れた文字を掃除
        content = re.sub(r'#.*', lambda m: re.sub(r'[^\x00-\x7F]+', '?', m.group(0)), content)

        # 2. 特殊な構文エラー（f-string内のバックスラッシュ等）の修正
        # (前回の修正を再適用)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error repairing {file_path}: {e}")
        return False

def main():
    files_to_fix = []
    for root, _, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                files_to_fix.append(os.path.join(root, file))
    
    # ルートの主要ファイルも追加
    for file in ["unified_dashboard.py", "mobile_dashboard.py", "personal_dashboard.py", "simple_unified_dashboard.py"]:
        if os.path.exists(file):
            files_to_fix.append(file)

    print(f"Repairing {len(files_to_fix)} files...")
    for f in files_to_fix:
        if repair_file(f):
            print(f"✅ Repaired: {f}")

if __name__ == "__main__":
    main()
