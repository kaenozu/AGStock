
import os

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app.py")

def fix_app():
    with open(APP_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 1. Fix Menu List
    start_menu_idx = -1
    for i, line in enumerate(lines):
        if 'menu = st.sidebar.radio(' in line:
            start_menu_idx = i
            break
            
    if start_menu_idx != -1:
        # Find start [ and end ]
        list_start = -1
        list_end = -1
        for i in range(start_menu_idx, len(lines)):
             if '[' in lines[i]:
                 list_start = i
                 break
        
        if list_start != -1:
            for i in range(list_start, len(lines)):
                if ']' in lines[i]:
                    list_end = i
                    break
        
        if list_start != -1 and list_end != -1:
            print(f"Replacing menu list from line {list_start+2} to {list_end+1}")
            # Identify indentation
            indent = "            "
            new_list_items = [
                f'{indent}"🏠 ダッシュボード",\n',
                f'{indent}"🤖 AI自動売買",\n',
                f'{indent}"📊 高度分析",\n',
                f'{indent}"🛡️ リスク管理",\n',
                f'{indent}"💬 AIアドバイザー",\n',
                f'{indent}"📝 投資家レター",\n',
                f'{indent}"📰 日次レポート",\n',
                f'{indent}"🏦 NISA管理",\n',
                f'{indent}"💴 税務計算",\n',
                f'{indent}"📈 オプション計算",\n',
                f'{indent}"⚡ リアルタイム監視",\n',
                f'{indent}"⚙️ 自動取引設定",\n',
                f'{indent}"🔧 システム設定"\n'
            ]
            # Replace lines inside []
            # slice assignment: lines[list_start+1 : list_end]
            lines[list_start+1 : list_end] = new_list_items
    
    # Reload lines because indices shifted? No, we perform one big operation.
    # Ah, if we modify the list length, subsequent indices shift.
    # It's safer to re-read or just do strings replacement if possible.
    # But strings are corrupt.
    # Let's save now and reload to be safe for next steps.
    with open(APP_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
    # Re-read for Part 2
    with open(APP_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    # 2. Fix Routing Logic
    for i in range(len(lines)):
        # Check bounds
        if i+1 >= len(lines):
            break
            
        line = lines[i].strip()
        next_line = lines[i+1].strip()
        
        # Determine if this is the corrupted System Settings block
        if 'st.session_state.page = "settings"' in next_line:
             if 'elif menu ==' in line: # Only if it looks like a menu check
                 print(f"Fixing System Settings routing at line {i+1}")
                 lines[i] = '    elif menu == "🔧 システム設定":\n'
             
        # Fix Ghostwriter routing
        if 'src.ui_ghostwriter' in next_line:
            if 'elif menu ==' in line:
                print(f"Fixing Ghostwriter routing at line {i+1}")
                lines[i] = '    elif menu == "📝 投資家レター":\n'
            
        # Fix AI Report routing (There might be two, we fix both to be safe)
        if 'src.ui_ai_report' in next_line and 'elif menu ==' in line:
            # We assume it should be the newspaper icon
            print(f"Fixing AI Report routing at line {i+1}")
            lines[i] = '    elif menu == "📰 日次レポート":\n'

    # 3. Remove rogue function call
    # It is likely near the end of file.
    # We look for 'create_prediction_analysis_dashboard()' used without assignment or def
    for i in range(len(lines) - 20, len(lines)):
        line = lines[i]
        if 'create_prediction_analysis_dashboard()' in line:
             if 'def ' not in line and line.startswith('    '): # Indented call
                 print(f"Removing rogue call at line {i+1}")
                 lines[i] = '\n'
                 
    with open(APP_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
    print("Fix complete.")

if __name__ == "__main__":
    fix_app()
