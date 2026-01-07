with open("unified_dashboard.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 131行目から修正
# 現在: st.markdown(f"""
# 次の行: check_and_execute_missed_trades()

# 131行目を完成させる
lines[130] = '        st.markdown(f"""\n'
lines[131] = '        \u003cdiv class="metric-card"\u003e\n'
lines.insert(132, '            \u003cdiv class="metric-label"\u003e勝率\u003c/div\u003e\n')
lines.insert(133, '            \u003cdiv class="metric-value"\u003e{format_percentage(win_rate)}\u003c/div\u003e\n')
lines.insert(134, "        \u003c/div\u003e\n")
lines.insert(135, '        """, unsafe_allow_html=True)\n')
lines.insert(136, "\n")
lines.insert(137, "def check_and_execute_missed_trades():\n")
lines.insert(138, '    """前日の取引漏れをチェック"""\n')
lines.insert(139, "    pass\n")
lines.insert(140, "\n")
lines.insert(141, "def main():\n")
lines.insert(142, '    """メイン関数"""\n')
lines.insert(143, "    check_and_execute_missed_trades()\n")
lines.insert(144, "    \n")

with open("unified_dashboard.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Fixed unified_dashboard.py!")
