"""
システムクリーンアップスクリプト
個人利用に不要なファイルを削除

⚠️ 警告: 実行前に必ずバックアップを取ってください!

使い方:
  python cleanup_system.py --dry-run  # 削除対象を確認
  python cleanup_system.py            # 実際に削除
"""
import os
import sys
from pathlib import Path
import shutil
from datetime import datetime

class SystemCleanup:
    """システムクリーンアップ"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.deleted_count = 0
        self.freed_space = 0
        
        # 削除対象ファイル
        self.files_to_delete = [
            # 重複ドキュメント
            "COMPLETION_REPORT.md",
            "DEMO_REPORT.md",
            "DEPLOYMENT_GUIDE.md",
            "FINAL_REPORT.md",
            "NEW_FEATURES_GUIDE.md",
            "PERSONAL_INVESTOR_GUIDE.md",
            "PHASE_COMPLETION_REPORT.md",
            "PROJECT_COMPLETE.txt",
            "PROJECT_COMPLETION_REPORT.md",
            "QUICK_SETUP_GUIDE.md",
            "QUICK_START_AUTO.md",
            "TEST_MODE_GUIDE.md",
            "USER_MANUAL.md",
            "implementation_plan.md",
            "reliability_report.md",
            
            # テスト出力
            "test_limit_debug.txt",
            "test_loader_debug.txt",
            "test_loader_output.txt",
            "test_output.log",
            "test_output.txt",
            "test_output_2.txt",
            "test_output_3.txt",
            "test_output_4.txt",
            "test_output_5.txt",
            "test_output_adv.txt",
            "test_output_debug.txt",
            "test_output_single.txt",
            "test_trailing_output.txt",
            "results.txt",
            
            # 古いスクリプト
            "agstock.py",
            "app_backup.py",
            "app_phase_tabs.py",
            "app_with_nulls.py",
            "auto_invest.py",
            "auto_trader.py",
            "analyze_performance.py",
            "analyze_portfolio.py",
            "check_errors.py",
            "debug_data.py",
            "debug_import.py",
            "fix_docstrings.py",
            "master_trading_system.py",
            "optimize_parameters.py",
            "paper_trade.py",
            "performance_tracker.py",
            "simple_performance_eval.py",
            "system_evaluation.py",
            "verify_accuracy.py",
            "verify_notifier.py",
            "view_performance.py",
            
            # レビュー・分析
            "report.md",
            "review.md",
            "roadmap_to_profitability.md",
            "screen_review_2025.md",
            "system_analysis.md",
            "ui_improvements_report.md",
            "ui_review.md",
            "ui_review_v2_2025.md",
            "walkthrough.md",
            "walkthrough_advanced.md",
            "walkthrough_ensemble.md",
            
            # Docker関連
            "Dockerfile",
            "docker-compose.yml",
            ".dockerignore",
            
            # 大きなHTMLファイル
            "backtest_comparison.html",
            "backtest_drawdown.html",
            "backtest_monthly_returns.html",
            "backtest_rolling_sharpe.html",
            
            # その他
            "backtest_summary.csv",
            "best_params.json",
            "ensemble_state.json",
            "scan_results.json",
            "deployment_log.txt",
        ]
        
        # 削除対象ディレクトリ
        self.dirs_to_delete = [
            "deploy",
            "htmlcov",
            ".benchmarks",
            "proposals",
            "pwa",
        ]
    
    def create_backup(self) -> str:
        """バックアップ作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(f"../AGStock_backup_{timestamp}")
        
        print(f"\n📦 バックアップ作成中...")
        print(f"   保存先: {backup_dir}")
        
        if not self.dry_run:
            try:
                shutil.copytree(".", backup_dir, ignore=shutil.ignore_patterns(
                    '.git', '.venv', '__pycache__', '*.pyc', 'node_modules'
                ))
                print(f"✅ バックアップ完了")
                return str(backup_dir)
            except Exception as e:
                print(f"❌ バックアップ失敗: {e}")
                return None
        else:
            print(f"   (ドライラン: 実際には作成しません)")
            return "dry_run"
    
    def delete_file(self, filepath: Path):
        """ファイル削除"""
        if filepath.exists():
            size = filepath.stat().st_size
            
            if self.dry_run:
                print(f"  [削除予定] {filepath} ({size:,} bytes)")
            else:
                try:
                    filepath.unlink()
                    print(f"  ✅ 削除: {filepath} ({size:,} bytes)")
                    self.deleted_count += 1
                    self.freed_space += size
                except Exception as e:
                    print(f"  ❌ 削除失敗: {filepath} - {e}")
    
    def delete_directory(self, dirpath: Path):
        """ディレクトリ削除"""
        if dirpath.exists() and dirpath.is_dir():
            # サイズ計算
            size = sum(f.stat().st_size for f in dirpath.rglob('*') if f.is_file())
            
            if self.dry_run:
                print(f"  [削除予定] {dirpath}/ ({size:,} bytes)")
            else:
                try:
                    shutil.rmtree(dirpath)
                    print(f"  ✅ 削除: {dirpath}/ ({size:,} bytes)")
                    self.deleted_count += 1
                    self.freed_space += size
                except Exception as e:
                    print(f"  ❌ 削除失敗: {dirpath} - {e}")
    
    def cleanup(self, force: bool = False):
        """クリーンアップ実行"""
        print("=" * 60)
        print("  🧹 システムクリーンアップ")
        print("=" * 60)
        
        if self.dry_run:
            print("\n⚠️  ドライランモード (実際には削除しません)")
        else:
            print("\n⚠️  実際に削除します!")
            if not force:
                response = input("続行しますか? (yes/no): ").strip().lower()
                if response != 'yes':
                    print("❌ キャンセルしました")
                    return
            else:
                print("⚠️  Forceモード: 確認をスキップして実行します")
            
            # バックアップ作成
            backup_path = self.create_backup()
            if not backup_path:
                print("❌ バックアップ失敗のため中止します")
                return
        
        # ファイル削除
        print("\n📄 ファイル削除:")
        for filename in self.files_to_delete:
            filepath = Path(filename)
            self.delete_file(filepath)
        
        # ディレクトリ削除
        print("\n📁 ディレクトリ削除:")
        for dirname in self.dirs_to_delete:
            dirpath = Path(dirname)
            self.delete_directory(dirpath)
        
        # サマリー
        print("\n" + "=" * 60)
        print("  📊 クリーンアップ完了")
        print("=" * 60)
        
        if self.dry_run:
            print(f"\n削除予定:")
        else:
            print(f"\n削除完了:")
        
        print(f"  ファイル/ディレクトリ数: {self.deleted_count}")
        print(f"  解放容量: {self.freed_space / 1024 / 1024:.2f} MB")
        
        if not self.dry_run:
            print(f"\n💾 バックアップ: {backup_path}")
            print(f"\n✅ クリーンアップ完了!")
            print(f"\n次のステップ:")
            print(f"  1. 動作確認: run_unified_dashboard.bat")
            print(f"  2. 問題なければバックアップを削除")

def main():
    """メイン処理"""
    # コマンドライン引数チェック
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    force = "--force" in sys.argv or "-f" in sys.argv
    
    if not dry_run and not force:
        print("⚠️  警告: このスクリプトはファイルを削除します!")
        print("⚠️  実行前に必ずバックアップを取ってください!")
        print("\n推奨: まずドライランで確認してください")
        print("  python cleanup_system.py --dry-run")
        print()
    
    cleanup = SystemCleanup(dry_run=dry_run)
    cleanup.cleanup(force=force)

if __name__ == "__main__":
    main()
