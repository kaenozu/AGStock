<<<<<<< HEAD
# AGStock 運用ガイド

## 📋 目次

1. [本番環境セットアップ](#本番環境セットアップ)
2. [日次運用手順](#日次運用手順)
3. [監視とメンテナンス](#監視とメンテナンス)
4. [バックアップとリカバリ](#バックアップとリカバリ)
5. [トラブル対応](#トラブル対応)
6. [セキュリティベストプラクティス](#セキュリティベストプラクティス)

---

## 本番環境セットアップ

### 初回セットアップ

#### 1. システム要件の確認

```bash
# Python バージョン確認
python --version  # 3.9以上

# メモリ確認
# Windows
systeminfo | findstr "Physical Memory"

# Linux/Mac
free -h
```

#### 2. 環境変数の設定

`.env`ファイルを作成:

```env
# 必須
GEMINI_API_KEY=your_gemini_api_key

# オプション（実取引を行う場合）
RAKUTEN_USER_ID=your_user_id
RAKUTEN_PASSWORD=your_password

# 運用設定
TRADING_MODE=paper  # paper または live
LOG_LEVEL=INFO
MAX_DAILY_TRADES=10
SAFE_MODE=false
```

#### 3. データディレクトリの準備

```bash
# 必要なディレクトリを作成
mkdir -p data/eternal_archive
mkdir -p data/backups
mkdir -p logs
mkdir -p models
```

#### 4. 初期設定の確認

```bash
# 設定検証スクリプトを実行
python scripts/verify_config.py

# テストスイートを実行
python tests/test_core_functions.py
python tests/test_integration.py
```

---

## 日次運用手順

### 朝のルーティン（市場開始前）

#### 1. システムヘルスチェック

```bash
# ログの確認
tail -n 50 logs/agstock.log

# エラーの確認
grep "ERROR" logs/agstock.log | tail -n 20

# ディスク容量確認
df -h
```

#### 2. 市場データの更新確認

```bash
# データ更新スクリプト実行
python scripts/update_market_data.py

# データ整合性チェック
python scripts/verify_data_integrity.py
```

#### 3. システム起動

```bash
# Streamlitアプリ起動
streamlit run app.py --server.headless=true --server.port=8501

# または
./run_unified_dashboard.bat  # Windows
./run_unified_dashboard.sh   # Linux/Mac
```

### 日中の監視

#### リアルタイム監視項目

1. **パフォーマンス**
   - CPU使用率 < 70%
   - メモリ使用率 < 80%
   - 応答時間 < 2秒

2. **取引状況**
   - 実行された取引数
   - エラー発生件数
   - ポジション状況

3. **アラート**
   - 異常な価格変動
   - システムエラー
   - API制限到達

### 夕方のルーティン（市場終了後）

#### 1. 日次レポート生成

```bash
# パフォーマンスレポート生成
python scripts/generate_daily_report.py

# レポート確認
cat reports/daily_report_$(date +%Y%m%d).txt
```

#### 2. バックアップ

```bash
# 自動バックアップスクリプト実行
python scripts/backup_data.py

# バックアップ確認
ls -lh data/backups/
```

#### 3. ログローテーション

```bash
# 古いログのアーカイブ
python scripts/rotate_logs.py
```

---

## 監視とメンテナンス

### 週次メンテナンス（週末）

#### 1. システムアップデート確認

```bash
# 依存パッケージの更新確認
pip list --outdated

# セキュリティアップデート
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

#### 2. データベース最適化

```bash
# SQLiteデータベースの最適化
sqlite3 data/agstock.db "VACUUM;"
sqlite3 data/agstock.db "ANALYZE;"
```

#### 3. パフォーマンス分析

```bash
# 週次パフォーマンスレポート
python scripts/weekly_performance_analysis.py
```

### 月次メンテナンス

#### 1. 包括的バックアップ

```bash
# 完全バックアップ
tar -czf backup_$(date +%Y%m).tar.gz data/ config.json .env

# クラウドへのアップロード（オプション）
# aws s3 cp backup_$(date +%Y%m).tar.gz s3://your-bucket/
```

#### 2. ログの分析

```bash
# エラー統計
grep "ERROR" logs/*.log | wc -l

# 警告統計
grep "WARNING" logs/*.log | wc -l

# パフォーマンス統計
python scripts/analyze_performance_logs.py
```

#### 3. ストレージクリーンアップ

```bash
# 古いログファイルの削除（30日以上前）
find logs/ -name "*.log" -mtime +30 -delete

# 古いバックアップの削除（90日以上前）
find data/backups/ -name "*.tar.gz" -mtime +90 -delete
```

---

## バックアップとリカバリ

### バックアップ戦略

#### 1. 日次バックアップ

```bash
#!/bin/bash
# daily_backup.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="data/backups/daily"

mkdir -p $BACKUP_DIR

# データベースバックアップ
cp data/agstock.db $BACKUP_DIR/agstock_$DATE.db

# 設定ファイルバックアップ
cp config.json $BACKUP_DIR/config_$DATE.json

# アーカイブデータバックアップ
tar -czf $BACKUP_DIR/archive_$DATE.tar.gz data/eternal_archive/

echo "Daily backup completed: $DATE"
```

#### 2. 週次バックアップ

```bash
#!/bin/bash
# weekly_backup.sh

WEEK=$(date +%Y_W%V)
BACKUP_DIR="data/backups/weekly"

mkdir -p $BACKUP_DIR

# 完全バックアップ
tar -czf $BACKUP_DIR/full_backup_$WEEK.tar.gz \
    data/ \
    config.json \
    .env \
    models/

echo "Weekly backup completed: $WEEK"
```

### リカバリ手順

#### データベースのリカバリ

```bash
# 1. システム停止
pkill -f "streamlit run app.py"

# 2. 現在のデータベースをバックアップ
cp data/agstock.db data/agstock.db.broken

# 3. バックアップから復元
cp data/backups/daily/agstock_20241229.db data/agstock.db

# 4. 整合性チェック
sqlite3 data/agstock.db "PRAGMA integrity_check;"

# 5. システム再起動
streamlit run app.py
```

#### 完全リカバリ

```bash
# 1. バックアップアーカイブを展開
tar -xzf data/backups/weekly/full_backup_2024_W52.tar.gz

# 2. 設定ファイルの復元
cp config.json.backup config.json
cp .env.backup .env

# 3. 検証
python scripts/verify_config.py

# 4. システム起動
streamlit run app.py
```

---

## トラブル対応

### 一般的な問題と対処法

#### 1. システムが起動しない

```bash
# ログ確認
tail -n 100 logs/agstock.log

# ポート競合確認
netstat -ano | findstr :8501  # Windows
lsof -i :8501                  # Linux/Mac

# 別ポートで起動
streamlit run app.py --server.port=8502
```

#### 2. データ取得エラー

```bash
# ネットワーク確認
ping yahoo.com

# API制限確認
grep "rate limit" logs/agstock.log

# 手動データ更新
python scripts/manual_data_fetch.py
```

#### 3. メモリ不足

```bash
# メモリ使用状況確認
ps aux | grep python

# キャッシュクリア
python scripts/clear_cache.py

# システム再起動
```

### 緊急時の対応

#### システムダウン時

1. **即座の対応**
   ```bash
   # ログ保存
   cp logs/agstock.log logs/emergency_$(date +%Y%m%d_%H%M%S).log
   
   # システム再起動
   ./restart_system.sh
   ```

2. **原因調査**
   ```bash
   # エラーログ分析
   grep "CRITICAL\|ERROR" logs/emergency_*.log
   
   # システムリソース確認
   top -n 1
   ```

3. **復旧確認**
   ```bash
   # ヘルスチェック
   curl http://localhost:8501
   
   # 機能テスト
   python tests/test_core_functions.py
   ```

---

## セキュリティベストプラクティス

### 1. 認証情報の管理

```bash
# .envファイルのパーミッション設定
chmod 600 .env

# .gitignoreに追加（既に設定済み）
echo ".env" >> .gitignore
```

### 2. ログの保護

```bash
# ログディレクトリのパーミッション
chmod 700 logs/

# 機密情報のマスキング確認
grep -r "password\|api_key" logs/  # 何も出力されないこと
```

### 3. 定期的なセキュリティチェック

```bash
# 依存パッケージの脆弱性スキャン
pip install safety
safety check

# コードの静的解析
pip install bandit
bandit -r src/
```

### 4. アクセス制限

```bash
# ローカルホストのみ許可（デフォルト）
streamlit run app.py --server.address=localhost

# 外部アクセスが必要な場合は認証を追加
# （Streamlitの認証機能を使用）
```

---

## 運用チェックリスト

### 日次チェックリスト

- [ ] システムヘルスチェック
- [ ] ログエラー確認
- [ ] 取引実行状況確認
- [ ] パフォーマンス確認
- [ ] 日次バックアップ実行

### 週次チェックリスト

- [ ] 週次パフォーマンスレポート確認
- [ ] データベース最適化
- [ ] ログローテーション
- [ ] セキュリティアップデート確認
- [ ] 週次バックアップ実行

### 月次チェックリスト

- [ ] 月次レポート生成
- [ ] 完全バックアップ実行
- [ ] ストレージクリーンアップ
- [ ] パフォーマンス分析
- [ ] 設定見直し

---

**最終更新**: 2024年12月29日  
**バージョン**: 1.0.0
=======
# AGStock 運用ガイド

## 📋 目次

1. [本番環境セットアップ](#本番環境セットアップ)
2. [日次運用手順](#日次運用手順)
3. [監視とメンテナンス](#監視とメンテナンス)
4. [バックアップとリカバリ](#バックアップとリカバリ)
5. [トラブル対応](#トラブル対応)
6. [セキュリティベストプラクティス](#セキュリティベストプラクティス)

---

## 本番環境セットアップ

### 初回セットアップ

#### 1. システム要件の確認

```bash
# Python バージョン確認
python --version  # 3.9以上

# メモリ確認
# Windows
systeminfo | findstr "Physical Memory"

# Linux/Mac
free -h
```

#### 2. 環境変数の設定

`.env`ファイルを作成:

```env
# 必須
GEMINI_API_KEY=your_gemini_api_key

# オプション（実取引を行う場合）
RAKUTEN_USER_ID=your_user_id
RAKUTEN_PASSWORD=your_password

# 運用設定
TRADING_MODE=paper  # paper または live
LOG_LEVEL=INFO
MAX_DAILY_TRADES=10
SAFE_MODE=false
```

#### 3. データディレクトリの準備

```bash
# 必要なディレクトリを作成
mkdir -p data/eternal_archive
mkdir -p data/backups
mkdir -p logs
mkdir -p models
```

#### 4. 初期設定の確認

```bash
# 設定検証スクリプトを実行
python scripts/verify_config.py

# テストスイートを実行
python tests/test_core_functions.py
python tests/test_integration.py
```

---

## 日次運用手順

### 朝のルーティン（市場開始前）

#### 1. システムヘルスチェック

```bash
# ログの確認
tail -n 50 logs/agstock.log

# エラーの確認
grep "ERROR" logs/agstock.log | tail -n 20

# ディスク容量確認
df -h
```

#### 2. 市場データの更新確認

```bash
# データ更新スクリプト実行
python scripts/update_market_data.py

# データ整合性チェック
python scripts/verify_data_integrity.py
```

#### 3. システム起動

```bash
# Streamlitアプリ起動
streamlit run app.py --server.headless=true --server.port=8501

# または
./run_unified_dashboard.bat  # Windows
./run_unified_dashboard.sh   # Linux/Mac
```

### 日中の監視

#### リアルタイム監視項目

1. **パフォーマンス**
   - CPU使用率 < 70%
   - メモリ使用率 < 80%
   - 応答時間 < 2秒

2. **取引状況**
   - 実行された取引数
   - エラー発生件数
   - ポジション状況

3. **アラート**
   - 異常な価格変動
   - システムエラー
   - API制限到達

### 夕方のルーティン（市場終了後）

#### 1. 日次レポート生成

```bash
# パフォーマンスレポート生成
python scripts/generate_daily_report.py

# レポート確認
cat reports/daily_report_$(date +%Y%m%d).txt
```

#### 2. バックアップ

```bash
# 自動バックアップスクリプト実行
python scripts/backup_data.py

# ブロックチェーン・レジャーのバックアップ
cp data/signal_chain.json data/backups/signal_chain_$(date +%Y%m%d).json

# バックアップ確認
ls -lh data/backups/
```

#### 3. ログローテーション

```bash
# 古いログのアーカイブ
python scripts/rotate_logs.py
```

---

## 監視とメンテナンス

### 週次メンテナンス（週末）

#### 1. システムアップデート確認

```bash
# 依存パッケージの更新確認
pip list --outdated

# セキュリティアップデート
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

#### 2. データベース最適化

```bash
# SQLiteデータベースの最適化
sqlite3 data/agstock.db "VACUUM;"
sqlite3 data/agstock.db "ANALYZE;"
```

#### 3. パフォーマンス分析

```bash
# 週次パフォーマンスレポート
python scripts/weekly_performance_analysis.py
```

### 月次メンテナンス

#### 1. 包括的バックアップ

```bash
# 完全バックアップ
tar -czf backup_$(date +%Y%m).tar.gz data/ config.json .env

# クラウドへのアップロード（オプション）
# aws s3 cp backup_$(date +%Y%m).tar.gz s3://your-bucket/
```

#### 2. ログの分析

```bash
# エラー統計
grep "ERROR" logs/*.log | wc -l

# 警告統計
grep "WARNING" logs/*.log | wc -l

# パフォーマンス統計
python scripts/analyze_performance_logs.py
```

#### 3. ストレージクリーンアップ

```bash
# 古いログファイルの削除（30日以上前）
find logs/ -name "*.log" -mtime +30 -delete

# 古いバックアップの削除（90日以上前）
find data/backups/ -name "*.tar.gz" -mtime +90 -delete
```

---

## バックアップとリカバリ

### バックアップ戦略

#### 1. 日次バックアップ

```bash
#!/bin/bash
# daily_backup.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="data/backups/daily"

mkdir -p $BACKUP_DIR

# データベースバックアップ
cp data/agstock.db $BACKUP_DIR/agstock_$DATE.db

# 設定ファイルバックアップ
cp config.json $BACKUP_DIR/config_$DATE.json

# アーカイブデータバックアップ
tar -czf $BACKUP_DIR/archive_$DATE.tar.gz data/eternal_archive/

echo "Daily backup completed: $DATE"
```

#### 2. 週次バックアップ

```bash
#!/bin/bash
# weekly_backup.sh

WEEK=$(date +%Y_W%V)
BACKUP_DIR="data/backups/weekly"

mkdir -p $BACKUP_DIR

# 完全バックアップ
tar -czf $BACKUP_DIR/full_backup_$WEEK.tar.gz \
    data/ \
    config.json \
    .env \
    models/

echo "Weekly backup completed: $WEEK"
```

### リカバリ手順

#### データベースのリカバリ

```bash
# 1. システム停止
pkill -f "streamlit run app.py"

# 2. 現在のデータベースをバックアップ
cp data/agstock.db data/agstock.db.broken

# 3. バックアップから復元
cp data/backups/daily/agstock_20241229.db data/agstock.db

# 4. 整合性チェック
sqlite3 data/agstock.db "PRAGMA integrity_check;"

# 5. システム再起動
streamlit run app.py
```

#### 完全リカバリ

```bash
# 1. バックアップアーカイブを展開
tar -xzf data/backups/weekly/full_backup_2024_W52.tar.gz

# 2. 設定ファイルの復元
cp config.json.backup config.json
cp .env.backup .env

# 3. 検証
python scripts/verify_config.py

# 4. システム起動
streamlit run app.py
```

---

## トラブル対応

### 一般的な問題と対処法

#### 1. システムが起動しない

```bash
# ログ確認
tail -n 100 logs/agstock.log

# ポート競合確認
netstat -ano | findstr :8501  # Windows
lsof -i :8501                  # Linux/Mac

# 別ポートで起動
streamlit run app.py --server.port=8502
```

#### 2. データ取得エラー

```bash
# ネットワーク確認
ping yahoo.com

# API制限確認
grep "rate limit" logs/agstock.log

# 手動データ更新
python scripts/manual_data_fetch.py
```

#### 3. メモリ不足

```bash
# メモリ使用状況確認
ps aux | grep python

# キャッシュクリア
python scripts/clear_cache.py

# システム再起動
```

### 緊急時の対応

#### システムダウン時

1. **即座の対応**
   ```bash
   # ログ保存
   cp logs/agstock.log logs/emergency_$(date +%Y%m%d_%H%M%S).log
   
   # システム再起動
   ./restart_system.sh
   ```

2. **原因調査**
   ```bash
   # エラーログ分析
   grep "CRITICAL\|ERROR" logs/emergency_*.log
   
   # システムリソース確認
   top -n 1
   ```

3. **復旧確認**
   ```bash
   # ヘルスチェック
   curl http://localhost:8501
   
   # 機能テスト
   python tests/test_core_functions.py
   ```

---

## セキュリティベストプラクティス

### 1. 認証情報の管理

```bash
# .envファイルのパーミッション設定
chmod 600 .env

# .gitignoreに追加（既に設定済み）
echo ".env" >> .gitignore
```

### 2. ログの保護

```bash
# ログディレクトリのパーミッション
chmod 700 logs/

# 機密情報のマスキング確認
grep -r "password\|api_key" logs/  # 何も出力されないこと
```

### 3. 定期的なセキュリティチェック

```bash
# 依存パッケージの脆弱性スキャン
pip install safety
safety check

# コードの静的解析
pip install bandit
bandit -r src/
```

### 4. アクセス制限

```bash
# ローカルホストのみ許可（デフォルト）
streamlit run app.py --server.address=localhost

# 外部アクセスが必要な場合は認証を追加
# （Streamlitの認証機能を使用）
```

---

## 運用チェックリスト

### 日次チェックリスト

- [ ] システムヘルスチェック
- [ ] ログエラー確認
- [ ] 取引実行状況確認
- [ ] パフォーマンス確認
- [ ] 日次バックアップ実行

### 週次チェックリスト

- [ ] 週次パフォーマンスレポート確認
- [ ] データベース最適化
- [ ] ログローテーション
- [ ] セキュリティアップデート確認
- [ ] 週次バックアップ実行

### 月次チェックリスト

- [ ] 月次レポート生成
- [ ] 完全バックアップ実行
- [ ] ストレージクリーンアップ
- [ ] パフォーマンス分析
- [ ] 設定見直し

---

**最終更新**: 2024年12月29日  
**バージョン**: 1.0.0
>>>>>>> 9ead59c0c8153a0969ef2e94b492063a605db31f
