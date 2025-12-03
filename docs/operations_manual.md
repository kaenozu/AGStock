# AGStock 運用マニュアル

**バージョン**: 1.0  
**最終更新**: 2025-11-30

---

## 📋 目次

1. [日次運用](#日次運用)
2. [週次運用](#週次運用)
3. [月次運用](#月次運用)
4. [トラブルシューティング](#トラブルシューティング)
5. [緊急時対応](#緊急時対応)

---

## 日次運用

### 朝の確認（9:00）

1. **システムヘルスチェック**
   ```bash
   # ダッシュボードで確認
   http://localhost:8503
   
   # 確認項目
   - CPU使用率 < 70%
   - メモリ使用率 < 80%
   - ディスク使用率 < 85%
   - エラーアラートなし
   ```

2. **ポートフォリオ確認**
   - 総資産額
   - 保有ポジション
   - 含み損益

3. **前日のトレード確認**
   - 実行された取引
   - 損益
   - エラーの有無

### 夕方の確認（17:00）

1. **本日の実績確認**
   - 取引回数
   - 確定損益
   - 勝率

2. **アラート確認**
   - 異常検知の有無
   - システムエラーの有無

3. **ログ確認**
   ```bash
   # エラーログの確認
   tail -n 100 logs/auto_trader.log | grep ERROR
   ```

---

## 週次運用

### 日曜日（週次メンテナンス）

1. **データベースバックアップ**
   ```bash
   python -m src.db_maintenance
   ```

2. **パフォーマンスレビュー**
   - 週次レポート確認
   - シャープレシオ
   - 最大ドローダウン

3. **システムアップデート**
   ```bash
   git pull origin main
   pip install -r requirements.txt
   ```

4. **ログローテーション**
   ```bash
   # 古いログの圧縮・削除
   find logs/ -name "*.log" -mtime +30 -delete
   ```

---

## 月次運用

### 月末（パフォーマンス分析）

1. **月次レポート生成**
   - PDFレポート自動生成
   - AI分析レビュー

2. **ポートフォリオ最適化**
   - 相関分析
   - リバランス検討

3. **システム監査**
   - セキュリティチェック
   - パフォーマンス最適化

---

## トラブルシューティング

### よくある問題と解決策

#### 1. Streamlitが起動しない

**症状**: `streamlit run app.py` が失敗

**原因**:
- ポート8503が使用中
- 依存関係の問題

**解決策**:
```bash
# ポート確認
netstat -ano | findstr :8503

# プロセス終了
taskkill /PID <PID> /F

# 依存関係再インストール
pip install -r requirements.txt --force-reinstall
```

#### 2. データ取得エラー

**症状**: "データ取得に失敗しました"

**原因**:
- yfinance API障害
- ネットワーク問題

**解決策**:
```python
# キャッシュクリア
import yfinance as yf
yf.cache.clear()

# 手動でデータ確認
data = yf.download("7203.T", period="1d")
print(data)
```

#### 3. データベースロック

**症状**: "database is locked"

**原因**:
- 複数プロセスが同時アクセス
- 異常終了による残存ロック

**解決策**:
```bash
# プロセス確認
ps aux | grep python

# ロックファイル削除
rm paper_trading.db-journal
```

#### 4. メモリ不足

**症状**: システムが遅い、クラッシュ

**原因**:
- データの蓄積
- メモリリーク

**解決策**:
```bash
# キャッシュクリア
python -c "import streamlit as st; st.cache_data.clear()"

# アプリ再起動
streamlit run app.py --server.maxUploadSize 200
```

---

## 緊急時対応

### システム停止時

1. **即座に実行**
   ```bash
   # システム停止
   docker-compose -f deploy/docker-compose.prod.yml down
   
   # データベースバックアップ
   python -m src.db_maintenance
   ```

2. **原因調査**
   ```bash
   # ログ確認
   tail -n 500 logs/auto_trader.log
   
   # システムリソース確認
   top
   df -h
   ```

3. **復旧**
   ```bash
   # 最新コードに更新
   git pull origin main
   
   # 再デプロイ
   bash deploy/deploy.sh
   ```

### データ損失時

1. **バックアップから復元**
   ```bash
   # 最新バックアップを確認
   ls -lt backups/
   
   # 復元
   cp backups/paper_trading_YYYYMMDD_HHMMSS.db paper_trading.db
   ```

2. **整合性チェック**
   ```python
   import sqlite3
   conn = sqlite3.connect('paper_trading.db')
   cursor = conn.cursor()
   cursor.execute("PRAGMA integrity_check")
   print(cursor.fetchall())
   ```

### セキュリティインシデント

1. **即座に実行**
   - システム停止
   - ネットワーク切断
   - 管理者に連絡

2. **調査**
   - アクセスログ確認
   - 不正な変更の特定

3. **対策**
   - パスワード変更
   - APIキー再発行
   - セキュリティパッチ適用

---

## エスカレーションフロー

### レベル1: 自動対応
- 自動リトライ
- サーキットブレーカー
- 自動アラート

### レベル2: 運用者対応
- ログ確認
- 手動リカバリー
- 設定変更

### レベル3: 開発者対応
- コード修正
- システム再設計
- 緊急パッチ

---

## 連絡先

### 緊急連絡先
- システム管理者: [連絡先]
- 開発チーム: [連絡先]

### 外部サポート
- yfinance: https://github.com/ranaroussi/yfinance
- Streamlit: https://discuss.streamlit.io/

---

## 付録

### 便利なコマンド

```bash
# システム状態確認
docker-compose -f deploy/docker-compose.prod.yml ps

# ログ確認
docker-compose -f deploy/docker-compose.prod.yml logs -f app

# データベースバックアップ
python -m src.db_maintenance

# メトリクス確認
python -m src.metrics_collector

# パフォーマンステスト
python -m pytest tests/ -v
```

### 設定ファイル

- `config.json`: システム設定
- `.env`: 環境変数（APIキー等）
- `deploy/docker-compose.prod.yml`: Docker設定

---

**注意**: このマニュアルは定期的に更新してください。
