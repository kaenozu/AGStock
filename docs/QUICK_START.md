# AGStock - 個人投資家向けクイックガイド

> 🎯 **5分で始める AI株式自動取引**

---

## 🚀 超簡単スタート

### 1. インストール (初回のみ)

```bash
# リポジトリをダウンロード
git clone https://github.com/your-username/AGStock.git
cd AGStock

# ワンクリックセットアップ
python quick_start.py
```

これだけ!自動的に:
- ✅ Python環境チェック
- ✅ 必要なパッケージインストール
- ✅ 設定ファイル作成
- ✅ アプリ起動

---

## 💡 日常の使い方

### 毎日の運用 (完全自動)

**何もしなくてOK!** PCの電源を入れておくだけ。

```
朝 8:00  → 市況レポートがLINEに届く
夕方15:30 → 自動スキャン・取引実行
夜       → 結果確認 (任意)
```

### 手動で確認したい時

```bash
# アプリ起動
streamlit run app.py

# または
python quick_start.py
```

ブラウザで `http://localhost:8501` が開きます

---

## 📊 主要機能

### 1. 市場スキャン
- 全市場から有望銘柄を自動検出
- AI予測 + テクニカル分析
- 信頼度70%以上のみ表示

### 2. 自動取引 (ペーパートレード)
- リスクなしで戦略検証
- 実際の市場データで模擬取引
- 資産推移を記録

### 3. リスク管理
- 日次損失制限 (-5%)
- ポジションサイズ自動調整
- 異常検知アラート

### 4. レポート
- 週次パフォーマンスレポート
- HTML形式で見やすく
- LINE/Discordで受信可能

---

## ⚙️ 設定のカスタマイズ

`config.json`を編集:

```json
{
  "capital": {
    "initial_capital": 1000000,  // 初期資金
    "currency": "JPY"
  },
  "risk": {
    "max_position_size": 0.1,    // 1銘柄の最大比率 (10%)
    "stop_loss_pct": 0.05        // 損切りライン (5%)
  },
  "notifications": {
    "enabled": true,             // 通知ON/OFF
    "line": {
      "enabled": true,
      "token": "あなたのLINEトークン"
    }
  }
}
```

### LINE通知の設定

1. https://notify-bot.line.me/ にアクセス
2. 「マイページ」→「トークンを発行する」
3. トークンをコピーして`config.json`に貼り付け

---

## 📱 便利なコマンド

```bash
# 統合ダッシュボード起動 (推奨)
run_unified_dashboard.bat

# ワンクリック起動 (旧)
python quick_start.py

# 週次レポート生成
python weekly_report_html.py
```

---

## 🎯 推奨ワークフロー

### 初心者向け (完全おまかせ)

1. **初期設定** (1回だけ)
   ```bash
   python setup_wizard.py
   ```

2. **LINE通知設定** (任意)
   - `config.json`でLINEトークン設定

3. **放置**
   - PCの電源を入れておくだけ
   - 毎日自動でスキャン・取引

4. **週1回確認**
   ```bash
   run_weekend_advisor.bat
   ```

### 中級者向け (カスタマイズ)

1. **設定調整**
   - `config.json`でリスク許容度調整
   - 通知条件のカスタマイズ

2. **手動スキャン**
   ```bash
   run_unified_dashboard.bat
   ```
   - 「市場スキャン」タブで銘柄確認
   - 気になる銘柄を個別分析

3. **戦略テスト**
   - 「バックテスト」タブで過去検証
   - パラメータ最適化

---

## 🆘 トラブルシューティング

### Q: アプリが起動しない

```bash
# ポート競合の場合
streamlit run unified_dashboard.py --server.port 8502
```

### Q: データが取得できない

- インターネット接続を確認
- yfinanceのサーバーダウンの可能性 (時間をおいて再試行)

### Q: 通知が来ない

1. `config.json`の`notifications.enabled`が`true`か確認
2. LINEトークンが正しいか確認
3. テスト実行:
   ```bash
   python -c "from src.smart_notifier import SmartNotifier; SmartNotifier().send_notification('テスト')"
   ```

### Q: エラーが出る

ログを確認:
```bash
type logs\auto_trader.log
```

---

## 📈 パフォーマンス目標

個人PC (一般的なスペック) での目安:

- 市場スキャン: 5秒以内
- バックテスト: 10秒以内 (100銘柄 x 1年)
- メモリ使用量: 2GB以下
- UI応答: 1秒以内

---

## 🔐 セキュリティ

個人利用なので、シンプルに:

- ✅ APIキーは`.env`ファイルで管理
- ✅ `.env`は`.gitignore`に追加済み
- ✅ データベースはローカル保存
- ✅ 外部公開しない (localhost のみ)

---

## 📚 さらに詳しく

- [スタートガイド](GETTING_STARTED.md)
- [アーキテクチャ](ARCHITECTURE.md)
- [開発方針](DEVELOPMENT_POLICY.md)

---

## 💬 サポート

- GitHub Issues: バグ報告・機能要望
- Discussions: 質問・情報交換

---

**🎉 これであなたも自動取引デビュー!**

仕事に専念しながら、AIが24時間市場を監視します。

---

*Last Updated: 2025-12-01*
