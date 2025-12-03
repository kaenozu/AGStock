# 🧹 システム軽量化レポート

**実施日時:** 2025-12-02 07:38  
**対象:** 個人利用に不要なファイルの整理

---

## 📊 現状分析

### ファイル数
- **ディレクトリ:** 22個
- **ファイル:** 135個
- **合計:** 157個

### 問題点
- ❌ 重複したドキュメント (10個以上)
- ❌ 古いバックアップファイル
- ❌ テスト出力ファイル (15個以上)
- ❌ 使われていないスクリプト

---

## 🗑️ 削除推奨ファイル

### 1. 重複ドキュメント (削除推奨)

**残すべきドキュメント (5個):**
- ✅ `README.md` - メインドキュメント
- ✅ `GETTING_STARTED.md` - スタートガイド
- ✅ `COMPLETION_SUMMARY.md` - 完成サマリー
- ✅ `MORNING_DASHBOARD_GUIDE.md` - 朝活ガイド
- ✅ `QUICK_START.md` - クイックスタート

**削除候補 (15個):**
```
❌ COMPLETION_REPORT.md (重複)
❌ DEMO_REPORT.md (不要)
❌ DEPLOYMENT_GUIDE.md (個人利用では不要)
❌ FINAL_REPORT.md (重複)
❌ NEW_FEATURES_GUIDE.md (古い)
❌ PERSONAL_INVESTOR_GUIDE.md (GETTING_STARTEDに統合済み)
❌ PHASE_COMPLETION_REPORT.md (重複)
❌ PROJECT_COMPLETE.txt (不要)
❌ PROJECT_COMPLETION_REPORT.md (重複)
❌ QUICK_SETUP_GUIDE.md (重複)
❌ QUICK_START_AUTO.md (重複)
❌ TEST_MODE_GUIDE.md (不要)
❌ USER_MANUAL.md (古い)
❌ implementation_plan.md (開発用)
❌ reliability_report.md (開発用)
```

### 2. テスト出力ファイル (削除推奨)

```
❌ test_limit_debug.txt
❌ test_loader_debug.txt
❌ test_loader_output.txt
❌ test_output.log
❌ test_output.txt
❌ test_output_2.txt
❌ test_output_3.txt
❌ test_output_4.txt
❌ test_output_5.txt
❌ test_output_adv.txt
❌ test_output_debug.txt
❌ test_output_single.txt
❌ test_trailing_output.txt
❌ results.txt
```

### 3. 古いスクリプト (削除候補)

```
❌ agstock.py (古い)
❌ app_backup.py (バックアップ)
❌ app_phase_tabs.py (古い)
❌ app_with_nulls.py (古い)
❌ auto_invest.py (fully_automated_trader.pyに統合)
❌ auto_trader.py (fully_automated_trader.pyに統合)
❌ analyze_performance.py (統合ダッシュボードに統合)
❌ analyze_portfolio.py (統合ダッシュボードに統合)
❌ check_errors.py (開発用)
❌ debug_data.py (開発用)
❌ debug_import.py (開発用)
❌ fix_docstrings.py (開発用)
❌ master_trading_system.py (fully_automated_trader.pyに統合)
❌ optimize_parameters.py (個人利用では不要)
❌ paper_trade.py (統合ダッシュボードに統合)
❌ performance_tracker.py (統合ダッシュボードに統合)
❌ simple_performance_eval.py (統合ダッシュボードに統合)
❌ system_evaluation.py (開発用)
❌ verify_accuracy.py (開発用)
❌ verify_notifier.py (開発用)
❌ view_performance.py (統合ダッシュボードに統合)
```

### 4. レビュー・分析ファイル (削除推奨)

```
❌ report.md
❌ review.md
❌ roadmap_to_profitability.md
❌ screen_review_2025.md
❌ system_analysis.md
❌ ui_improvements_report.md
❌ ui_review.md
❌ ui_review_v2_2025.md
❌ walkthrough.md
❌ walkthrough_advanced.md
❌ walkthrough_ensemble.md
```

### 5. Docker関連 (個人利用では不要)

```
❌ Dockerfile
❌ docker-compose.yml
❌ .dockerignore
❌ deploy/ (ディレクトリ全体)
```

### 6. HTML出力ファイル (削除候補)

```
❌ backtest_comparison.html (3.5MB)
❌ backtest_drawdown.html (3.6MB)
❌ backtest_monthly_returns.html (3.6MB)
❌ backtest_rolling_sharpe.html (3.6MB)
```

---

## ✅ 残すべきファイル

### コアスクリプト (10個)
```
✅ app.py - メインアプリ
✅ unified_dashboard.py - 統合ダッシュボード
✅ morning_dashboard.py - 朝活ダッシュボード
✅ weekend_advisor.py - 週末戦略会議
✅ setup_wizard.py - 設定ウィザード
✅ quick_start.py - クイックスタート
✅ fully_automated_trader.py - 完全自動トレーダー
✅ daily_scan.py - 市場スキャン
✅ weekly_report_html.py - 週次レポート
✅ weekly_review.py - 週次レビュー
```

### 起動スクリプト (5個)
```
✅ run_unified_dashboard.bat
✅ run_morning_dashboard.bat
✅ run_weekend_advisor.bat
✅ run_app.bat
✅ setup.bat
```

### ドキュメント (10個)
```
✅ README.md
✅ GETTING_STARTED.md
✅ COMPLETION_SUMMARY.md
✅ MORNING_DASHBOARD_GUIDE.md
✅ QUICK_START.md
✅ PHASE_46_COMPLETION.md
✅ PHASE_47_COMPLETION.md
✅ PHASE_48_COMPLETION.md
✅ PHASE_49_COMPLETION.md
✅ PHASE_50_51_COMPLETION.md
```

### 設定ファイル (5個)
```
✅ config.json
✅ requirements.txt
✅ .gitignore
✅ .env.example
✅ pytest.ini
```

### データベース (5個)
```
✅ paper_trading.db
✅ stock_data.db
✅ sentiment_history.db
✅ alerts.db
✅ yfinance_cache.sqlite
```

---

## 📊 軽量化効果

### Before (削除前)
- ファイル数: 135個
- ディレクトリ: 22個
- 合計サイズ: 約20MB (HTMLファイル含む)

### After (削除後)
- ファイル数: 約40個 (-70%)
- ディレクトリ: 約10個 (-55%)
- 合計サイズ: 約5MB (-75%)

---

## 🔧 実行方法

### 手動削除 (推奨)

1. **バックアップ作成**
   ```bash
   # 念のため全体をバックアップ
   xcopy /E /I AGStock AGStock_backup
   ```

2. **不要ファイルを削除**
   - 上記リストを参考に手動削除
   - 確認しながら慎重に

3. **動作確認**
   ```bash
   python setup_wizard.py
   run_unified_dashboard.bat
   ```

### 自動削除スクリプト

**注意: 実行前に必ずバックアップを取ってください!**

```python
# cleanup.py
import os
from pathlib import Path

# 削除対象ファイル
files_to_delete = [
    # ドキュメント
    "COMPLETION_REPORT.md",
    "DEMO_REPORT.md",
    "DEPLOYMENT_GUIDE.md",
    # ... (省略)
]

# 削除実行
for file in files_to_delete:
    filepath = Path(file)
    if filepath.exists():
        filepath.unlink()
        print(f"削除: {file}")
```

---

## 💡 推奨アクション

### オプション1: 手動で慎重に削除 (推奨)
- 時間: 30分
- リスク: 低
- 確実性: 高

### オプション2: 自動スクリプトで一括削除
- 時間: 5分
- リスク: 中
- 確実性: 中

### オプション3: 何もしない
- 現状のまま使用
- ディスク容量に余裕があれば問題なし

---

## 🎯 結論

**個人利用では、以下のファイルだけで十分です:**

1. **コアスクリプト** (10個)
2. **起動スクリプト** (5個)
3. **ドキュメント** (10個)
4. **設定ファイル** (5個)
5. **データベース** (5個)
6. **srcディレクトリ** (必要なモジュールのみ)

**合計: 約40-50個のファイル**

これで、システムは軽量で管理しやすくなります! 🎉

---

*作成日: 2025-12-02 07:38*
