"""
AGStock Quick Start - ワンクリック起動スクリプト
個人投資家向けの簡単セットアップと起動
"""

import json
import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Python バージョンチェック"""
    print("🔍 Python バージョンを確認中...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8以上が必要です")
        print(f"   現在のバージョン: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """依存パッケージのチェック"""
    print("\n📦 依存パッケージを確認中...")
    required_packages = ["streamlit", "pandas", "numpy", "yfinance", "plotly", "ta"]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing.append(package)

    if missing:
        print(f"\n⚠️  不足しているパッケージがあります: {', '.join(missing)}")
        print("   インストールしますか? (y/n): ", end="")
        response = input().strip().lower()
        if response == "y":
            print("\n📥 パッケージをインストール中...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ インストール完了")
        else:
            print("❌ 依存パッケージが不足しています")
            return False

    return True


def check_config():
    """設定ファイルのチェック"""
    print("\n⚙️  設定ファイルを確認中...")

    config_path = Path("config.json")
    if not config_path.exists():
        print("  ⚠️  config.json が見つかりません")
        print("  📝 デフォルト設定を作成します...")

        default_config = {
            "capital": {"initial_capital": 1000000, "currency": "JPY"},
            "risk": {"max_position_size": 0.1, "stop_loss_pct": 0.05},
            "notifications": {
                "enabled": False,
                "min_confidence": 0.7,
                "min_expected_return": 0.03,
                "quiet_hours": "22:00-07:00",
                "line": {"enabled": False, "token": ""},
                "discord": {"enabled": False, "webhook_url": ""},
            },
            "automation": {"daily_scan_time": "15:30", "morning_brief_time": "08:00"},
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)

        print("  ✅ config.json を作成しました")
        print("  💡 必要に応じて設定を編集してください")
    else:
        print("  ✅ config.json")

    return True


def check_database():
    """データベースの確認"""
    print("\n💾 データベースを確認中...")

    db_files = ["paper_trading.db", "stock_data.db"]

    for db_file in db_files:
        if Path(db_file).exists():
            print(f"  ✅ {db_file}")
        else:
            print(f"  ℹ️  {db_file} (初回起動時に作成されます)")

    return True


def start_app():
    """Streamlit アプリを起動"""
    print("\n🚀 AGStock を起動します...")
    print("   ブラウザが自動的に開きます")
    print("   終了するには Ctrl+C を押してください\n")
    print("=" * 60)

    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n\n👋 AGStock を終了しました")
        sys.exit(0)


def main():
    """メイン処理"""
    print("=" * 60)
    print("  🚀 AGStock Quick Start")
    print("  個人投資家向けAI株式自動取引システム")
    print("=" * 60)

    # 環境チェック
    if not check_python_version():
        sys.exit(1)

    if not check_dependencies():
        print("\n❌ セットアップに失敗しました")
        print("   手動で requirements.txt をインストールしてください:")
        print("   pip install -r requirements.txt")
        sys.exit(1)

    if not check_config():
        sys.exit(1)

    check_database()

    # 起動確認
    print("\n" + "=" * 60)
    print("✅ 環境チェック完了!")
    print("=" * 60)
    print("\n起動しますか? (y/n): ", end="")
    response = input().strip().lower()

    if response == "y":
        start_app()
    else:
        print("\n💡 後で起動する場合:")
        print("   python quick_start.py")
        print("   または")
        print("   streamlit run app.py")


if __name__ == "__main__":
    main()
