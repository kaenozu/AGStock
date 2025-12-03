"""
実運用準備チェックスクリプト
Production Readiness Check

システムが実運用に耐えられるか総合的に調査します。

使い方:
  python production_readiness_check.py
"""
import sys
from pathlib import Path
import json
import sqlite3
from datetime import datetime

class ProductionReadinessCheck:
    """実運用準備チェック"""
    
    def __init__(self):
        self.results = {
            'total_checks': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'critical_issues': [],
            'warnings_list': [],
            'passed_checks': []
        }
    
    def print_header(self, title: str):
        """ヘッダー表示"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)
    
    def check_item(self, name: str, passed: bool, message: str = "", critical: bool = False):
        """チェック項目"""
        self.results['total_checks'] += 1
        
        if passed:
            self.results['passed'] += 1
            self.results['passed_checks'].append(name)
            print(f"✅ {name}")
            if message:
                print(f"   {message}")
        else:
            if critical:
                self.results['failed'] += 1
                self.results['critical_issues'].append(f"{name}: {message}")
                print(f"❌ {name}")
            else:
                self.results['warnings'] += 1
                self.results['warnings_list'].append(f"{name}: {message}")
                print(f"⚠️  {name}")
            
            if message:
                print(f"   {message}")
    
    def check_python_version(self):
        """Pythonバージョンチェック"""
        self.print_header("1. Python環境チェック")
        
        version = sys.version_info
        passed = version.major == 3 and version.minor >= 8
        
        self.check_item(
            "Pythonバージョン",
            passed,
            f"Python {version.major}.{version.minor}.{version.micro} {'(OK)' if passed else '(3.8以上が必要)'}",
            critical=True
        )
    
    def check_required_packages(self):
        """必須パッケージチェック"""
        self.print_header("2. 必須パッケージチェック")
        
        required_packages = {
            'streamlit': 'streamlit',
            'pandas': 'pandas',
            'numpy': 'numpy',
            'yfinance': 'yfinance',
            'plotly': 'plotly',
            'ta': 'ta',
            'scikit-learn': 'sklearn',
            'lightgbm': 'lightgbm',
        }
        
        for package, import_name in required_packages.items():
            try:
                __import__(import_name)
                self.check_item(f"パッケージ: {package}", True)
            except ImportError:
                self.check_item(
                    f"パッケージ: {package}",
                    False,
                    "インストールされていません",
                    critical=True
                )
    
    def check_core_files(self):
        """コアファイルチェック"""
        self.print_header("3. コアファイルチェック")
        
        core_files = [
            'unified_dashboard.py',
            'morning_dashboard.py',
            'weekend_advisor.py',
            'setup_wizard.py',
            'quick_start.py',
            'config.json',
            'src/paper_trader.py',
            'src/data_loader.py',
            'src/strategies.py',
        ]
        
        for filepath in core_files:
            path = Path(filepath)
            self.check_item(
                f"ファイル: {filepath}",
                path.exists(),
                "見つかりません" if not path.exists() else "",
                critical=True
            )
    
    def check_database(self):
        """データベースチェック"""
        self.print_header("4. データベースチェック")
        
        # paper_trading.db
        db_path = Path("paper_trading.db")
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # テーブル存在チェック
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['trades', 'positions', 'equity_history']
                for table in required_tables:
                    self.check_item(
                        f"テーブル: {table}",
                        table in tables,
                        "テーブルが存在しません" if table not in tables else ""
                    )
                
                conn.close()
                
            except Exception as e:
                self.check_item(
                    "paper_trading.db",
                    False,
                    f"エラー: {e}",
                    critical=True
                )
        else:
            self.check_item(
                "paper_trading.db",
                False,
                "初回起動時に作成されます",
                critical=False
            )
    
    def check_config(self):
        """設定ファイルチェック"""
        self.print_header("5. 設定ファイルチェック")
        
        config_path = Path("config.json")
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 必須項目チェック
                required_keys = ['capital', 'risk', 'auto_trading', 'notifications']
                for key in required_keys:
                    self.check_item(
                        f"設定項目: {key}",
                        key in config,
                        "設定項目が不足しています" if key not in config else ""
                    )
                
                # リスク設定チェック
                if 'risk' in config:
                    risk = config['risk']
                    
                    # 損切りラインチェック
                    stop_loss = risk.get('stop_loss_pct', 0)
                    self.check_item(
                        "損切りライン設定",
                        0 < stop_loss <= 0.10,
                        f"現在: {stop_loss*100:.1f}% (推奨: 3-10%)"
                    )
                    
                    # ポジションサイズチェック
                    max_pos = risk.get('max_position_size', 0)
                    self.check_item(
                        "最大ポジションサイズ",
                        0 < max_pos <= 0.20,
                        f"現在: {max_pos*100:.1f}% (推奨: 10-20%)"
                    )
                
            except json.JSONDecodeError:
                self.check_item(
                    "config.json",
                    False,
                    "JSONフォーマットエラー",
                    critical=True
                )
            except Exception as e:
                self.check_item(
                    "config.json",
                    False,
                    f"エラー: {e}",
                    critical=True
                )
        else:
            self.check_item(
                "config.json",
                False,
                "setup_wizard.py で作成してください",
                critical=True
            )
    
    def check_src_modules(self):
        """srcモジュールチェック"""
        self.print_header("6. srcモジュールチェック")
        
        critical_modules = [
            'src.paper_trader',
            'src.data_loader',
            'src.strategies',
            'src.formatters',
            'src.anomaly_detector',
            'src.auto_rebalancer',
        ]
        
        for module_name in critical_modules:
            try:
                module = __import__(module_name, fromlist=[''])
                self.check_item(f"モジュール: {module_name}", True)
            except ImportError as e:
                self.check_item(
                    f"モジュール: {module_name}",
                    False,
                    f"インポートエラー: {e}",
                    critical=True
                )
            except Exception as e:
                self.check_item(
                    f"モジュール: {module_name}",
                    False,
                    f"エラー: {e}",
                    critical=True
                )
    
    def check_performance(self):
        """パフォーマンスチェック"""
        self.print_header("7. パフォーマンスチェック")
        
        # メモリ使用量チェック
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            self.check_item(
                "メモリ使用量",
                memory_mb < 500,
                f"現在: {memory_mb:.1f}MB (推奨: 500MB以下)"
            )
        except ImportError:
            self.check_item(
                "メモリ使用量",
                True,
                "psutilがないため確認できません (任意)"
            )
        
        # キャッシュディレクトリ
        cache_dir = Path(".cache")
        if cache_dir.exists():
            cache_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
            cache_size_mb = cache_size / 1024 / 1024
            
            self.check_item(
                "キャッシュサイズ",
                cache_size_mb < 100,
                f"現在: {cache_size_mb:.1f}MB (推奨: 100MB以下)"
            )
        else:
            self.check_item(
                "キャッシュディレクトリ",
                True,
                "初回起動時に作成されます"
            )
    
    def check_security(self):
        """セキュリティチェック"""
        self.print_header("8. セキュリティチェック")
        
        # .envファイルチェック
        env_path = Path(".env")
        self.check_item(
            ".envファイル",
            not env_path.exists() or env_path.stat().st_size > 0,
            "APIキーは.envファイルで管理してください (任意)"
        )
        
        # .gitignoreチェック
        gitignore_path = Path(".gitignore")
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                content = f.read()
            
            important_ignores = ['.env', '*.db', '__pycache__']
            for pattern in important_ignores:
                self.check_item(
                    f".gitignore: {pattern}",
                    pattern in content,
                    "追加を推奨" if pattern not in content else ""
                )
        else:
            self.check_item(
                ".gitignore",
                False,
                "作成を推奨"
            )
    
    def check_documentation(self):
        """ドキュメントチェック"""
        self.print_header("9. ドキュメントチェック")
        
        docs = [
            'README.md',
            'GETTING_STARTED.md',
            'COMPLETION_SUMMARY.md',
        ]
        
        for doc in docs:
            path = Path(doc)
            self.check_item(
                f"ドキュメント: {doc}",
                path.exists(),
                "見つかりません" if not path.exists() else ""
            )
    
    def generate_report(self):
        """レポート生成"""
        self.print_header("📊 総合評価")
        
        total = self.results['total_checks']
        passed = self.results['passed']
        failed = self.results['failed']
        warnings = self.results['warnings']
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n総チェック数: {total}")
        print(f"✅ 合格: {passed}")
        print(f"❌ 失敗: {failed}")
        print(f"⚠️  警告: {warnings}")
        print(f"\n合格率: {pass_rate:.1f}%")
        
        # 評価
        if failed == 0 and warnings == 0:
            grade = "S (完璧)"
            color = "🟢"
        elif failed == 0 and warnings <= 3:
            grade = "A (優秀)"
            color = "🟢"
        elif failed <= 2:
            grade = "B (良好)"
            color = "🟡"
        elif failed <= 5:
            grade = "C (要改善)"
            color = "🟡"
        else:
            grade = "D (不合格)"
            color = "🔴"
        
        print(f"\n{color} 総合評価: {grade}")
        
        # クリティカルな問題
        if self.results['critical_issues']:
            print("\n" + "=" * 70)
            print("  🚨 クリティカルな問題")
            print("=" * 70)
            for issue in self.results['critical_issues']:
                print(f"❌ {issue}")
        
        # 警告
        if self.results['warnings_list']:
            print("\n" + "=" * 70)
            print("  ⚠️  警告")
            print("=" * 70)
            for warning in self.results['warnings_list']:
                print(f"⚠️  {warning}")
        
        # 推奨アクション
        print("\n" + "=" * 70)
        print("  💡 推奨アクション")
        print("=" * 70)
        
        if failed > 0:
            print("\n1. クリティカルな問題を修正してください")
            print("2. 必要なパッケージをインストールしてください:")
            print("   pip install -r requirements.txt")
            print("3. 設定ウィザードを実行してください:")
            print("   python setup_wizard.py")
        elif warnings > 0:
            print("\n1. 警告を確認してください")
            print("2. 可能であれば修正を推奨します")
            print("3. 実運用は可能ですが、改善の余地があります")
        else:
            print("\n✅ すべてのチェックに合格しました!")
            print("✅ 実運用に問題ありません!")
            print("\n次のステップ:")
            print("  1. python setup_wizard.py (未実行の場合)")
            print("  2. run_unified_dashboard.bat")
            print("  3. 実際に使ってみる!")
        
        return failed == 0
    
    def run_all_checks(self):
        """全チェック実行"""
        print("=" * 70)
        print("  🔍 実運用準備チェック")
        print("  Production Readiness Check")
        print("=" * 70)
        print(f"\n実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.check_python_version()
        self.check_required_packages()
        self.check_core_files()
        self.check_database()
        self.check_config()
        self.check_src_modules()
        self.check_performance()
        self.check_security()
        self.check_documentation()
        
        return self.generate_report()

def main():
    """メイン処理"""
    checker = ProductionReadinessCheck()
    ready = checker.run_all_checks()
    
    print("\n" + "=" * 70)
    if ready:
        print("  🎉 実運用準備完了!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("  ⚠️  実運用前に問題を修正してください")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()
