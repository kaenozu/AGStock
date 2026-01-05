import os
import shutil
import re
from pathlib import Path

# インポートパスの置換ルール
replacements = {
    r'agstock\.src\.': 'src.',
    r'from agstock\.src': 'from src',
    r'import agstock\.src': 'import src',
}

# ディレクトリ移動ルール
move_rules = {
    "src/analytics/advanced_analytics.py": "src/advanced_analytics.py",
    "src/cache/smart_cache.py": "src/smart_cache.py",
    "src/performance/async_processor.py": "src/async_processor.py",
    "src/validation/walk_forward.py": "src/walk_forward.py",
    "src/learning/online_learner.py": "src/online_learner.py",
    "src/reports/morning_strategy_memo.py": "src/morning_strategy_memo.py",
}

# 削除するディレクトリ
dirs_to_remove = [
    "src/analytics", "src/cache", "src/database", "src/learning", 
    "src/mobile", "src/performance", "src/reports", "src/validation",
    "src/strategies/custom", "src/strategies/evolved"
]

def safe_replace(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        new_content = content
        for pattern, replacement in replacements.items():
            new_content = re.sub(pattern, replacement, new_content)
        
        if new_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return False

def main():
    print("🚀 安全なクリーンアップを開始します...")
    
    # 1. ファイル移動
    for src, dst in move_rules.items():
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            print(f"✅ Moved: {src} -> {dst}")

    # 2. パス置換 (src, tests, scripts 内の全ファイルを対象)
    count = 0
    for root, _, files in os.walk("."):
        if any(x in root for x in ["src", "tests", "scripts"]):
            for file in files:
                if file.endswith(".py"):
                    if safe_replace(os.path.join(root, file)):
                        count += 1
    print(f"✅ Updated imports in {count} files.")

    # 3. ディレクトリ削除
    for d in dirs_to_remove:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"✅ Removed directory: {d}")

if __name__ == "__main__":
    main()
