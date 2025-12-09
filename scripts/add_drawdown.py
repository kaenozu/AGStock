import re

with open('fully_automated_trader.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ドローダウン保護を daily_routine の try ブロックの先頭に追加
pattern = r'(try:\s+# 1\. Phase 30-1: 市場レジーム検出とリスクパラメータ更新)'
replacement = r'''# 🛡️ ドローダウン保護チェック
        is_safe_dd, dd_reason, emergency_signals = self.advanced_risk.check_drawdown_protection(self.pt, self.log)
        if not is_safe_dd:
            self.log(f"⚠️ {dd_reason}", "WARNING")
            if emergency_signals:
                self.execute_signals(emergency_signals)
            return
        
        \1'''

content = re.sub(pattern, replacement, content)

with open('fully_automated_trader.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ ドローダウン保護を追加しました')
