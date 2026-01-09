# AGStock トラブルシューティングガイド

## 🔧 目次

1. [一般的な問題](#一般的な問題)
2. [データ関連の問題](#データ関連の問題)
3. [API関連の問題](#api関連の問題)
4. [パフォーマンス問題](#パフォーマンス問題)
5. [取引実行の問題](#取引実行の問題)
6. [UI/表示の問題](#ui表示の問題)
7. [ログの確認方法](#ログの確認方法)

---

## 一般的な問題

### システムが起動しない

**症状**:
```
streamlit run app.py
```
を実行してもエラーが発生する

**原因と解決方法**:

1. **Pythonバージョンの確認**
   ```bash
   python --version
   ```
   Python 3.9以上が必要です。

2. **依存パッケージの再インストール**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. **ポートの競合**
   ```bash
   # 別のポートで起動
   streamlit run app.py --server.port=8502
   ```

### モジュールが見つからないエラー

**症状**:
```
ModuleNotFoundError: No module named 'src'
```

**解決方法**:
```bash
# プロジェクトルートディレクトリから実行していることを確認
cd /path/to/AGStock
python -m streamlit run app.py
```

---

## データ関連の問題

### 市場データの取得失敗

**症状**: 「データの取得に失敗しました」エラー

**チェックリスト**:

1. **インターネット接続**
   ```bash
   ping yahoo.com
   ```

2. **銘柄コードの形式**
   - 日本株: `7203.T` (トヨタ)
   - 米国株: `AAPL` (Apple)
   - 正しい形式で入力されているか確認

3. **yfinanceの状態確認**
   ```python
   import yfinance as yf
   data = yf.download("7203.T", period="1d")
   print(data)
   ```

4. **プロキシ設定**
   プロキシ環境下の場合:
   ```bash
   export HTTP_PROXY=http://proxy.example.com:8080
   export HTTPS_PROXY=http://proxy.example.com:8080
   ```

### データが古い/更新されない

**症状**: 表示されるデータが古い

**解決方法**:

1. **キャッシュのクリア**
   - ブラウザで `Ctrl + Shift + R` (強制リロード)
   - Streamlitのキャッシュクリア: 右上メニュー → "Clear cache"

2. **手動更新**
   ```python
   # キャッシュTTLの確認
   # src/utils/performance.py の cached_market_data を確認
   ```

---

## API関連の問題

### Gemini APIエラー

**症状**: 「Gemini API Key が設定されていません」

**解決手順**:

1. **APIキーの取得**
   - [Google AI Studio](https://makersuite.google.com/app/apikey) でAPIキーを取得

2. **環境変数の設定**
   ```bash
   # .envファイルに追加
   echo "GEMINI_API_KEY=your_api_key_here" >> .env
   ```

3. **環境変数の読み込み確認**
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print(os.getenv("GEMINI_API_KEY"))
   ```

### API Rate Limit エラー

**症状**: 「API rate limit exceeded」

**解決方法**:

1. **リクエスト頻度の調整**
   - 設定で自動スキャンの間隔を長くする
   - 手動スキャンに切り替える

2. **APIキーの確認**
   - 無料枠の上限を確認
   - 必要に応じて有料プランへアップグレード

---

## パフォーマンス問題

### システムが遅い

**症状**: ページの読み込みや処理が遅い

**診断と解決**:

1. **メモリ使用量の確認**
   ```bash
   # Windowsの場合
   tasklist | findstr python
   
   # Linux/Macの場合
   ps aux | grep python
   ```

2. **不要なプロセスの終了**
   - 使用していないタブを閉じる
   - ブラウザを再起動

3. **データベースの最適化**
   ```bash
   # SQLiteデータベースの最適化
   sqlite3 data/agstock.db "VACUUM;"
   ```

4. **ログファイルのクリーンアップ**
   ```bash
   # 古いログファイルの削除
   find logs/ -name "*.log" -mtime +30 -delete
   ```

### メモリ不足エラー

**症状**: 「MemoryError」または突然のクラッシュ

**解決方法**:

1. **メモリ使用量の削減**
   - バックテスト期間を短くする
   - 同時分析する銘柄数を減らす

2. **スワップメモリの増加** (Linux)
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

---

## 取引実行の問題

### 取引が実行されない

**症状**: 推奨された取引が実行されない

**チェックリスト**:

1. **取引モードの確認**
   - 設定 → ペーパートレードモードになっていないか確認

2. **証券口座の認証**
   - 楽天証券のログイン情報が正しいか確認
   - 2段階認証が必要な場合は対応

3. **取引時間の確認**
   - 日本株: 9:00-11:30, 12:30-15:00 (JST)
   - 米国株: 23:30-06:00 (JST, 夏時間は22:30-05:00)

4. **資金の確認**
   - 十分な買付余力があるか確認

### 注文がエラーになる

**症状**: 「注文の送信に失敗しました」

**原因別の対処**:

1. **単元未満株エラー**
   - 設定で単元株取引を有効化
   - または単元未満株対応の証券会社を使用

2. **値幅制限エラー**
   - ストップ高/ストップ安の銘柄は取引不可
   - 指値価格を調整

3. **銘柄停止**
   - 売買停止中の銘柄でないか確認

---

## UI/表示の問題

### グラフが表示されない

**症状**: チャートやグラフが空白

**解決方法**:

1. **JavaScriptの有効化**
   - ブラウザでJavaScriptが有効か確認

2. **ブラウザの互換性**
   - Chrome, Firefox, Edgeの最新版を使用
   - Internet Explorerは非対応

3. **アドブロッカーの無効化**
   - 一時的にアドブロッカーを無効化して確認

### レイアウトが崩れる

**症状**: UIのレイアウトが正しく表示されない

**解決方法**:

1. **ブラウザキャッシュのクリア**
   ```
   Ctrl + Shift + Delete (Windows/Linux)
   Cmd + Shift + Delete (Mac)
   ```

2. **CSSファイルの確認**
   ```bash
   # CSSファイルが存在するか確認
   ls assets/style*.css
   ```

3. **ブラウザの拡大率**
   - 100%に設定されているか確認 (Ctrl + 0)

---

## ログの確認方法

### ログファイルの場所

```
logs/
├── agstock.log          # メインログ
├── trading.log          # 取引ログ
├── error.log            # エラーログ
└── debug.log            # デバッグログ
```

### ログの確認コマンド

```bash
# 最新のエラーを確認
tail -n 50 logs/error.log

# リアルタイムでログを監視
tail -f logs/agstock.log

# 特定のエラーを検索
grep "ERROR" logs/agstock.log

# 日付でフィルタ
grep "2024-12-29" logs/trading.log
```

### ログレベルの変更

`src/logger_config.py`で設定:

```python
# より詳細なログ
logging.basicConfig(level=logging.DEBUG)

# 警告以上のみ
logging.basicConfig(level=logging.WARNING)
```

---

## 高度なトラブルシューティング

### データベースの修復

```bash
# SQLiteデータベースの整合性チェック
sqlite3 data/agstock.db "PRAGMA integrity_check;"

# 破損している場合の修復
sqlite3 data/agstock.db ".recover" | sqlite3 data/agstock_recovered.db
```

### 設定のリセット

```bash
# 設定ファイルのバックアップ
cp config.json config.json.backup

# デフォルト設定に戻す
git checkout config.json
```

### 完全なクリーンインストール

```bash
# 仮想環境の削除と再作成
deactivate
rm -rf venv/
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## サポートへの問い合わせ

問題が解決しない場合、以下の情報を添えてGitHub Issuesに報告してください:

1. **環境情報**
   ```bash
   python --version
   pip list > installed_packages.txt
   ```

2. **エラーログ**
   - 関連するエラーメッセージ
   - スタックトレース

3. **再現手順**
   - 問題が発生する具体的な手順

4. **スクリーンショット**
   - エラー画面のキャプチャ

---

**最終更新**: 2024年12月29日
