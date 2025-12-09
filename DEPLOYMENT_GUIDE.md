# 🚀 AGStock - 自動実行スケジュール設定ガイド

## Windows タスクスケジューラー設定

### 1. モーニングブリーフ（毎朝8:30）

```powershell
# タスクスケジューラーを開く
taskschd.msc

# または PowerShell で作成
$action = New-ScheduledTaskAction -Execute "python" -Argument "c:\gemini-thinkpad\AGStock\morning_brief.py" -WorkingDirectory "c:\gemini-thinkpad\AGStock"
$trigger = New-ScheduledTaskTrigger -Daily -At 8:30AM
Register-ScheduledTask -TaskName "AGStock_MorningBrief" -Action $action -Trigger $trigger -Description "毎朝のモーニングブリーフ配信"
```

### 2. フルオート投資（毎朝9:00）

```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "c:\gemini-thinkpad\AGStock\auto_invest.py" -WorkingDirectory "c:\gemini-thinkpad\AGStock"
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
Register-ScheduledTask -TaskName "AGStock_AutoInvest" -Action $action -Trigger $trigger -Description "フル自動投資システム実行"
```

### 3. スマートアラート（1時間ごと）

```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "c:\gemini-thinkpad\AGStock\smart_alerts.py" -WorkingDirectory "c:\gemini-thinkpad\AGStock"
$trigger = New-ScheduledTaskTrigger -Once -At 9:00AM -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Hours 8)
Register-ScheduledTask -TaskName "AGStock_SmartAlerts" -Action $action -Trigger $trigger -Description "スマートアラート監視"
```

### 4. パフォーマンストラッカー（毎日21:00）

```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "c:\gemini-thinkpad\AGStock\performance_tracker.py" -WorkingDirectory "c:\gemini-thinkpad\AGStock"
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00PM
Register-ScheduledTask -TaskName "AGStock_PerformanceReport" -Action $action -Trigger $trigger -Description "日次パフォーマンスレポート"
```

---

## macOS/Linux cron設定

```bash
# crontabを編集
crontab -e

# 以下を追加（AGStockのパスは適宜変更）
# モーニングブリーフ（毎朝8:30）
30 8 * * * cd /path/to/AGStock && python morning_brief.py

# フルオート投資（毎朝9:00）
0 9 * * * cd /path/to/AGStock && python auto_invest.py

# スマートアラート（9-17時、1時間ごと）
0 9-17 * * * cd /path/to/AGStock && python smart_alerts.py

# パフォーマンスレポート（毎日21:00）
0 21 * * * cd /path/to/AGStock && python performance_tracker.py
```

---

## Docker Compose での24時間稼働

### docker-compose.yml（既存を拡張）

```yaml
version: '3.8'

services:
  agstock-scheduler:
    build: .
    container_name: agstock_scheduler
    volumes:
      - ./:/app
      - ./data:/app/data
      - ./logs:/app/logs
      - ./reports:/app/reports
    environment:
      - TZ=Asia/Tokyo
      - PYTHONUNBUFFERED=1
    command: >
      sh -c "
      while true; do
        # モーニングブリーフ
        if [ $(date +%H:%M) = '08:30' ]; then
          python morning_brief.py
        fi
        
        # フルオート投資  
        if [ $(date +%H:%M) = '09:00' ]; then
          python auto_invest.py
        fi
        
        # スマートアラート（9-17時、毎時）
        if [ $(date +%H) -ge 9 ] && [ $(date +%H) -le 17 ] && [ $(date +%M) = '00' ]; then
          python smart_alerts.py
        fi
        
        # パフォーマンスレポート
        if [ $(date +%H:%M) = '21:00' ]; then
          python performance_tracker.py
        fi
        
        sleep 60
      done
      "
    restart: unless-stopped
```

### Dockerfile（最適化版）

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# システム依存関係
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード
COPY . .

# ログ・レポートディレクトリ
RUN mkdir -p logs reports data

CMD ["python", "auto_invest.py"]
```

---

## GitHub Actions（CI/CD）

### .github/workflows/deploy.yml

```yaml
name: Deploy AGStock

on:
  push:
    branches: [main]
  schedule:
    # 毎朝9:00 JST（UTC 0:00）に自動実行
    - cron: '0 0 * * *'

jobs:
  auto-trade:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run Auto Invest
      env:
        LINE_TOKEN: ${{ secrets.LINE_TOKEN }}
        DISCORD_WEBHOOK: ${{ secrets.DISCORD_WEBHOOK }}
      run: |
        python auto_invest.py
    
    - name: Upload Reports
      uses: actions/upload-artifact@v3
      with:
        name: reports
        path: reports/
```

---

## クラウドデプロイ

### AWS Lambda（サーバーレス）

```bash
# Lambdaレイヤー作成
mkdir python
pip install -r requirements.txt -t python/
zip -r layer.zip python/

# Lambda関数デプロイ
aws lambda create-function \
  --function-name AGStockAutoTrade \
  --runtime python3.12 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-role \
  --handler auto_invest.main \
  --zip-file fileb://function.zip

# EventBridge で毎日9:00に実行
aws events put-rule \
  --name AGStockDailyRule \
  --schedule-expression "cron(0 0 * * ? *)"
```

### Google Cloud Run

```bash
# コンテナビルド
gcloud builds submit --tag gcr.io/PROJECT_ID/agstock

# Cloud Run デプロイ
gcloud run deploy agstock \
  --image gcr.io/PROJECT_ID/agstock \
  --platform managed \
  --region asia-northeast1

# Cloud Scheduler で定期実行
gcloud scheduler jobs create http agstock-daily \
  --schedule="0 9 * * *" \
  --uri="https://agstock-xxxxx.run.app" \
  --http-method=POST
```

---

## 推奨スケジュール

| 時刻 | タスク | 説明 |
|------|--------|------|
| 8:30 | モーニングブリーフ | 前日結果・今日の推奨 |
| 9:00 | フルオート投資 | 自動スキャン・取引 |
| 9:00-17:00 | スマートアラート（毎時） | 重要イベント監視 |
| 21:00 | パフォーマンスレポート | 日次集計 |
| 日曜21:00 | リバランス | 週次ポートフォリオ最適化 |

---

## ログ管理

すべてのスクリプトは `logs/` ディレクトリにログを出力します：

```
logs/
├── auto_trader.log
├── morning_brief.log
├── smart_alerts.log
└── performance_tracker.log
```

ログローテーション設定（Linux）:

```bash
# /etc/logrotate.d/agstock
/path/to/AGStock/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 user group
}
```

---

## トラブルシューティング

### タスクが実行されない
1. Pythonパスを確認: `which python`
2. 作業ディレクトリを確認
3. ログを確認: `logs/auto_trader.log`

### 通知が来ない
1. `config.json` の設定を確認
2. LINE/Discord トークンを確認
3. インターネット接続を確認

### Docker起動しない
```bash
# ログ確認
docker-compose logs -f agstock-scheduler

# コンテナ再起動
docker-compose restart agstock-scheduler
```

---

**完全自動化完了！** 🎉
