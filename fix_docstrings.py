#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix docstrings in auto_trader_ui.py
"""

with open('src/auto_trader_ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all docstrings with comments to avoid syntax errors
replacements = [
    ('"""ステータスカード表示"""', '# ステータスカード表示'),
    ('"""コントロールセンター"""', '# コントロールセンター'),
    ('"""本日のサマリー"""', '# 本日のサマリー'),
    ('"""設定フォーム"""', '# 設定フォーム'),
    ('"""ログ表示"""', '# ログ表示'),
    ('"""週次レビュー表示"""', '# 週次レビュー表示'),
]

for old, new in replacements:
    content = content.replace(old, new)

with open('src/auto_trader_ui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all docstrings")
