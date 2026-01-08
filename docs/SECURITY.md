# セキュリティガイド

## APIキーの管理

### 重要な原則
1. **APIキーは絶対にコードにハードコードしない**
2. **APIキーは環境変数または.envファイルで管理**
3. **.envファイルはgitignoreされている**

### 設定方法

1. `.env`ファイルを作成:
```bash
cp .env.example .env
```

2. `.env`ファイルを編集してAPIキーを設定:
```bash
AGSTOCK_GEMINI_API_KEY=your-api-key-here
AGSTOCK_OPENAI_API_KEY=your-openai-key-here
```

3. アプリケーションを起動すると自動的に環境変数が読み込まれる

### APIキーの取得方法

| サービス | 取得URL |
|----------|---------|
| Gemini | https://aistudio.google.com/ |
| OpenAI | https://platform.openai.com/api-keys |

### 既存のAPIキーを無効化する

過去にAPIキーがコミットされた場合:

1. **即座にAPIキーを無効化/再生成**
   - Google Cloud Console / OpenAI Dashboardで該当キーを削除
   - 新しいキーを生成

2. **Git履歴からの削除（オプション）**
```bash
# BFG Repo-Cleanerを使用
bfg --replace-text passwords.txt

# または git filter-branch
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch config.json" \
  --prune-empty --tag-name-filter cat -- --all
```

### セキュリティチェック

```bash
# APIキー漏洩チェック
make security-check
```

## ベストプラクティス

1. **本番環境**: 環境変数をシステムレベルで設定
2. **開発環境**: `.env`ファイルを使用
3. **CI/CD**: GitHub Secrets等のシークレット管理を使用
