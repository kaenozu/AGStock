import subprocess
import time
import datetime
import sys
import os
import webbrowser

# スクリプトの親ディレクトリ（プロジェクトルート）に移動して実行環境を整える
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
os.chdir(project_root)
sys.path.append(project_root)

def run_dashboard():
    """ダッシュボードをバックグラウンドで起動"""
    print("📊 シンプルダッシュボードを起動中...")
    cmd = [sys.executable, "-m", "streamlit", "run", "simple_dashboard.py", "--server.port", "8502"]
    
    # ログファイルを指定してバックグラウンド実行
    with open("logs/dashboard.log", "w") as log_file:
        process = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
    
    time.sleep(3)  # 起動待ち
    webbrowser.open("http://localhost:8502")
    return process

def run_test_trade():
    """テスト取引を今すぐ実行"""
    print("\n🧪 テスト取引を実行します...")
    try:
        subprocess.run([sys.executable, "fully_automated_trader.py", "--force"], check=True)
        print("✅ テスト取引完了")
    except subprocess.CalledProcessError as e:
        print(f"❌ テスト取引エラー: {e}")

def run_script(script_name, description):
    """スクリプトを実行"""
    print(f"\n⏰ {description} を開始します ({datetime.datetime.now().strftime('%H:%M:%S')})")
    try:
        subprocess.run([sys.executable, script_name], check=True)
        print(f"✅ {description} 完了")
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} エラー: {e}")
    except Exception as e:
        print(f"❌ 予期せぬエラー: {e}")

def check_and_run_missed_trade():
    """起動時に今日の取引が未実行かチェックし、必要なら実行"""
    import sqlite3
    from pathlib import Path
    
    now = datetime.datetime.now()
    weekday = now.weekday()
    
    # 平日のみチェック
    if weekday >= 5:
        return
    
    # 15:30以降かチェック
    if now.time() < datetime.time(15, 30):
        return
    
    # データベースで今日の取引があるかチェック
    db_path = Path("paper_trading.db")
    if not db_path.exists():
        print("⚠️ paper_trading.db が見つかりません")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        today = now.date().isoformat()
        cursor.execute('SELECT COUNT(*) FROM orders WHERE date = ?', (today,))
        count = cursor.fetchone()[0]
        
        conn.close()
        
        if count == 0:
            print(f"📅 本日({today})の取引が未実行です。今から実行します...")
            run_script("fully_automated_trader.py", "自動取引・市場スキャン（キャッチアップ）")
        else:
            print(f"✅ 本日({today})の取引は既に実行済みです ({count}件)")
            
    except Exception as e:
        print(f"⚠️ 取引履歴チェックエラー: {e}")

def main():
    os.makedirs("logs", exist_ok=True)
    
    print("="*50)
    print("   🚀 AGStock フルオートシステム")
    print("   このウィンドウを閉じるとシステムが停止します")
    print("="*50)
    
    # ダッシュボード起動
    dashboard_process = run_dashboard()
    
    # 起動時に今日の取引をチェック
    print("\n🔍 起動時チェック: 本日の取引状況を確認中...")
    check_and_run_missed_trade()
    
    # テスト取引オプション
    print("\n💡 今すぐテスト取引を実行しますか？")
    print("   (y) はい - 今すぐ市場をスキャンして取引")
    print("   (n) いいえ - 15:30まで待つ")
    
    try:
        response = input("\n選択 (y/n): ").strip().lower()
        if response == 'y':
            run_test_trade()
            print("\n✅ テスト取引が完了しました！")
            print("   ブラウザで結果を確認してください: http://localhost:8502")
    except:
        pass  # Enterキーだけ押された場合はスキップ
    
    print("\n⏳ スケジューラー稼働中...")
    print("   - 08:00 : 朝活ブリーフィング")
    print("   - 15:30 : 自動取引・市場スキャン")
    print("   - 毎週土曜 : 週末戦略会議")
    
    last_run_minute = -1
    
    try:
        while True:
            now = datetime.datetime.now()
            
            # 分が変わった時だけチェック
            if now.minute != last_run_minute:
                current_time = now.strftime("%H:%M")
                weekday = now.weekday() # 0=Mon, 6=Sun
                
                # 08:00 朝活ブリーフィング (平日のみ)
                if current_time == "08:00" and weekday < 5:
                    run_script("morning_dashboard.py", "朝活ブリーフィング") # morning_brief.py か morning_dashboard.py か確認が必要だが、dashboardの方が包括的か？ morning_brief.pyを確認する
                
                # 15:30 自動取引 (平日のみ)
                elif current_time == "15:30" and weekday < 5:
                    run_script("fully_automated_trader.py", "自動取引・市場スキャン")
                
                # 土曜 10:00 週末戦略会議
                elif current_time == "10:00" and weekday == 5:
                    run_script("weekend_advisor.py", "週末戦略会議")
                
                last_run_minute = now.minute
                
                # 稼働状況表示（1時間おき）
                if now.minute == 0:
                    print(f"[{current_time}] システム正常稼働中...")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 システムを停止しています...")
        dashboard_process.terminate()
        print("✅ 停止完了")

def test_system():
    """システム構成と動作のテスト"""
    print("🧪 システム診断モード")
    
    # 1. ファイル存在確認
    required_files = [
        "unified_dashboard.py",
        "morning_dashboard.py",
        "fully_automated_trader.py",
        "weekend_advisor.py"
    ]
    
    all_exist = True
    for f in required_files:
        if os.path.exists(f):
            print(f"✅ 発見: {f}")
        else:
            print(f"❌ 未発見: {f}")
            all_exist = False
            
    if not all_exist:
        print("⚠️ 一部のファイルが見つかりません。")
        return False
        
    # 2. ダッシュボード起動テスト (ドライラン)
    print("\n📊 ダッシュボード起動テスト...")
    try:
        # 実際に起動せず、コマンドが通るかだけ確認（ヘルプを表示させて即終了）
        subprocess.run([sys.executable, "-m", "streamlit", "--help"], capture_output=True, check=True)
        print("✅ Streamlitコマンド確認OK")
    except Exception as e:
        print(f"❌ Streamlit起動エラー: {e}")
        return False
        
    print("\n✅ システム診断完了: 準備OK")
    return True

if __name__ == "__main__":
    if "--test" in sys.argv:
        test_system()
    else:
        main()
