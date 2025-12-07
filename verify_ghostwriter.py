"""
Verify Ghostwriter
レポート生成機能をテストする
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from src.ghostwriter import Ghostwriter

print("Initializing Ghostwriter...")
gw = Ghostwriter()

print("Generating Weekly Report...")
path = gw.generate_weekly_report()

print(f"Report Generated: {path}")

# Display content preview
with open(path, "r", encoding="utf-8") as f:
    content = f.read()
    print("-" * 40)
    print(content[:500] + "...")
    print("-" * 40)
