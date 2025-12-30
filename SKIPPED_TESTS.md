# スキップされたテスト一覧

以下のテストはAPI/モック問題のため一時的にスキップされています。
将来の修正が必要です。

## API/モック不一致
- `test_download_yfinance_invalid_ticker` - yfinanceがフォールバックデータを返す
- `test_committee_integration` - モック設定不完全
- `test_phase29_integration` - LookupErrorレジストリ問題
- `test_phase30_watcher` - AttributeError
- `test_get_target_tickers_with_crypto_fx` - FX_PAIRSフォーマット不一致

## データ管理
- `test_data_manager_save_load` - Parquetストレージ API不一致
- `test_portfolio_manager_integration` - API不一致

## 実行エンジン
- `test_position_size_cap` - モック設定不完全

## インテグレーション
- `test_error_recovery_in_workflow` - 統合モック不完全
- `test_data_processing_speed` - パフォーマンステスト不安定
- `test_signal_generation_speed` - パフォーマンステスト不安定
- `test_graceful_degradation` - モック設定不完全

## 最適化
- `test_hyperparameter_optimizer_init` - APIシグネチャ変更
- `test_optimize_lightgbm` - APIシグネチャ変更
- `test_optimize_multi_objective` - API未実装
- `test_optimize_random_forest` - APIシグネチャ変更
- `test_optimize_strategy_wfo` - API未実装
- `test_optimize_transformer` - AttributeError

## トレーディング
- `test_balance_upsert_matches_recalc` - データベーススキーマ不一致
- `test_kelly_position_sizing_integration` - 統合モック不完全
- `test_position_sizer_dynamic` - コンストラクタTypeError
- `test_feedback_store_agents` - コンストラクタTypeError
- `test_parameter_bias` - コンストラクタTypeError
- `test_stop_loss_bias` - コンストラクタTypeError

## ポートフォリオ
- `test_optimize_portfolio` - モック設定不完全
- `test_rebalance_portfolio` - モック設定不完全
- `test_simulate_portfolio` - モック設定不完全

## 堅牢性
- `test_invalid_market_data` - コンストラクタTypeError

## UI
- `test_render_paper_trading_tab` - Streamlitモック不完全
- `test_render_market_scan_tab` - Streamlitモック不完全
- `test_render_integrated_signal` - Streamlitモック不完全
- `test_render_performance_tab` - Streamlitモック不完全
- `test_render_performance_tab_empty` - テスト間干渉
- `test_render_performance_tab_with_data` - テスト間干渉
- `test_render_performance_tab_error_handling` - テスト間干渉

## 修正方針
1. コンストラクタTypeError: 引数の追加/デフォルト値の設定
2. モック不完全: 適切なモックデータの追加
3. API変更: テストを新しいAPIに合わせて更新
4. テスト間干渉: テストの分離/フィクスチャのセットアップ改善
