# 🚨 AGStock 災害復旧計画 (Disaster Recovery Plan)

**バージョン**: 1.0  
**最終更新**: 2024年12月29日  
**責任者**: AGStock運用チーム

---

## 📋 目次

1. [概要](#概要)
2. [目標設定](#目標設定)
3. [バックアップ戦略](#バックアップ戦略)
4. [リカバリー手順](#リカバリー手順)
5. [テスト計画](#テスト計画)
6. [連絡体制](#連絡体制)

---

## 概要

### 目的

AGStockシステムの災害時における迅速な復旧を実現し、データ損失を最小限に抑える。

### 適用範囲

- データベース（SQLite）
- アプリケーションコード
- 設定ファイル
- ログファイル
- 学習済みモデル

---

## 目標設定

### RPO (Recovery Point Objective)

**目標**: 最大1時間のデータ損失

| データ種別 | RPO | バックアップ頻度 |
|-----------|-----|----------------|
| 取引データ | 1時間 | 1時間ごと |
| 設定データ | 24時間 | 日次 |
| ログデータ | 24時間 | 日次 |
| モデルデータ | 7日 | 週次 |

### RTO (Recovery Time Objective)

**目標**: 最大4時間でシステム復旧

| システム | RTO | 優先度 |
|---------|-----|--------|
| データベース | 1時間 | 最高 |
| アプリケーション | 2時間 | 高 |
| 分析機能 | 4時間 | 中 |

---

## バックアップ戦略

### 1. 自動バックアップスクリプト

```bash
#!/bin/bash
# backup_agstock.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/agstock"
SOURCE_DIR="/path/to/AGStock"

# データベースバックアップ
echo "Backing up database..."
cp $SOURCE_DIR/data/agstock.db $BACKUP_DIR/db/agstock_$DATE.db

# 設定ファイルバックアップ
echo "Backing up config..."
cp $SOURCE_DIR/config.json $BACKUP_DIR/config/config_$DATE.json
cp $SOURCE_DIR/.env $BACKUP_DIR/config/.env_$DATE

# Eternal Archiveバックアップ
echo "Backing up eternal archive..."
tar -czf $BACKUP_DIR/archive/archive_$DATE.tar.gz $SOURCE_DIR/data/eternal_archive/

# モデルバックアップ
echo "Backing up models..."
tar -czf $BACKUP_DIR/models/models_$DATE.tar.gz $SOURCE_DIR/models/

# ログバックアップ
echo "Backing up logs..."
tar -czf $BACKUP_DIR/logs/logs_$DATE.tar.gz $SOURCE_DIR/logs/

# 古いバックアップの削除（30日以上前）
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### 2. バックアップスケジュール

#### Windowsタスクスケジューラ

```powershell
# 1時間ごとのデータベースバックアップ
schtasks /create /tn "AGStock DB Backup" /tr "powershell.exe -File C:\AGStock\scripts\backup_db.ps1" /sc hourly

# 日次フルバックアップ（午前2時）
schtasks /create /tn "AGStock Full Backup" /tr "powershell.exe -File C:\AGStock\scripts\backup_full.ps1" /sc daily /st 02:00

# 週次モデルバックアップ（日曜午前3時）
schtasks /create /tn "AGStock Model Backup" /tr "powershell.exe -File C:\AGStock\scripts\backup_models.ps1" /sc weekly /d SUN /st 03:00
```

#### Linux Cron

```cron
# 1時間ごとのデータベースバックアップ
0 * * * * /opt/agstock/scripts/backup_db.sh

# 日次フルバックアップ（午前2時）
0 2 * * * /opt/agstock/scripts/backup_full.sh

# 週次モデルバックアップ（日曜午前3時）
0 3 * * 0 /opt/agstock/scripts/backup_models.sh
```

### 3. バックアップ検証

```python
# verify_backup.py
import sqlite3
import os
from datetime import datetime

def verify_database_backup(backup_path):
    """データベースバックアップの整合性を検証."""
    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        
        # 整合性チェック
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        if result[0] == "ok":
            print(f"✅ Database backup verified: {backup_path}")
            return True
        else:
            print(f"❌ Database backup corrupted: {backup_path}")
            return False
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        if conn:
            conn.close()

def verify_archive_backup(backup_path):
    """アーカイブバックアップの整合性を検証."""
    import tarfile
    
    try:
        with tarfile.open(backup_path, 'r:gz') as tar:
            # アーカイブの整合性チェック
            members = tar.getmembers()
            print(f"✅ Archive verified: {len(members)} files in {backup_path}")
            return True
    except Exception as e:
        print(f"❌ Archive verification failed: {e}")
        return False

if __name__ == "__main__":
    # 最新のバックアップを検証
    backup_dir = "data/backups"
    
    # データベース検証
    db_backups = sorted([f for f in os.listdir(f"{backup_dir}/daily") if f.endswith('.db')])
    if db_backups:
        verify_database_backup(f"{backup_dir}/daily/{db_backups[-1]}")
    
    # アーカイブ検証
    archive_backups = sorted([f for f in os.listdir(f"{backup_dir}/daily") if f.endswith('.tar.gz')])
    if archive_backups:
        verify_archive_backup(f"{backup_dir}/daily/{archive_backups[-1]}")
```

---

## リカバリー手順

### シナリオ1: データベース破損

#### 症状
- アプリケーション起動時にデータベースエラー
- データの読み書きができない

#### リカバリー手順

```bash
# 1. システム停止
pkill -f "streamlit run app.py"

# 2. 破損したデータベースをバックアップ
cp data/agstock.db data/agstock.db.corrupted_$(date +%Y%m%d_%H%M%S)

# 3. 最新のバックアップから復元
cp data/backups/daily/agstock_YYYYMMDD_HHMMSS.db data/agstock.db

# 4. 整合性チェック
sqlite3 data/agstock.db "PRAGMA integrity_check;"

# 5. システム再起動
streamlit run app.py

# 6. 動作確認
curl http://localhost:8501
```

**推定復旧時間**: 30分

### シナリオ2: アプリケーション全体の障害

#### 症状
- システムが起動しない
- 重大なエラーが発生

#### リカバリー手順

```bash
# 1. 現在の状態を保存
tar -czf agstock_emergency_$(date +%Y%m%d_%H%M%S).tar.gz /path/to/AGStock

# 2. 最新のフルバックアップから復元
cd /path/to
tar -xzf backups/weekly/full_backup_YYYYWW.tar.gz

# 3. 環境変数の復元
cp backups/config/.env_latest .env

# 4. 依存パッケージの確認
pip install -r requirements.txt

# 5. データベースの復元
cp backups/daily/agstock_latest.db data/agstock.db

# 6. システム起動
streamlit run app.py

# 7. 動作確認
python tests/test_core_functions.py
```

**推定復旧時間**: 2時間

### シナリオ3: データセンター障害

#### 症状
- サーバー全体がアクセス不能
- 物理的な障害

#### リカバリー手順

```bash
# 1. 新しいサーバーを準備
# - OS: Windows/Linux
# - Python 3.9+インストール

# 2. AGStockをクローン
git clone https://github.com/your-repo/AGStock.git
cd AGStock

# 3. クラウドバックアップから復元
# AWS S3の例
aws s3 sync s3://agstock-backup/latest/ ./

# 4. 環境設定
cp backups/.env .env
pip install -r requirements.txt

# 5. データベース復元
cp backups/agstock.db data/agstock.db

# 6. システム起動
streamlit run app.py --server.port=8501

# 7. DNS更新（必要に応じて）
# 新しいIPアドレスに更新
```

**推定復旧時間**: 4時間

---

## テスト計画

### 月次リカバリーテスト

**実施日**: 毎月第1日曜日 午前10時

#### テスト手順

```markdown
1. テスト環境の準備
   - 本番環境とは別のテスト環境を用意
   - 最新のバックアップを使用

2. データベースリカバリーテスト
   - バックアップからデータベースを復元
   - 整合性チェック実施
   - データの完全性確認

3. アプリケーションリカバリーテスト
   - フルバックアップから復元
   - システム起動確認
   - 全機能の動作確認

4. 結果記録
   - 復旧時間の記録
   - 問題点の記録
   - 改善点の特定
```

#### テスト記録フォーマット

```
テスト日: YYYY/MM/DD
テスト担当者: [名前]
テストシナリオ: [シナリオ番号]

結果:
- 復旧開始時刻: HH:MM
- 復旧完了時刻: HH:MM
- 実際の復旧時間: XX分
- 目標RTO: XX分
- 達成状況: ✅/❌

問題点:
- [問題1]
- [問題2]

改善アクション:
- [アクション1]
- [アクション2]
```

---

## 連絡体制

### 緊急連絡先

| 役割 | 担当者 | 連絡先 | 対応時間 |
|------|--------|--------|----------|
| 第一責任者 | [名前] | [電話/Email] | 24/7 |
| 第二責任者 | [名前] | [電話/Email] | 24/7 |
| 技術サポート | [名前] | [電話/Email] | 平日9-18時 |

### エスカレーションフロー

```
障害発生
    ↓
第一責任者に連絡（即座）
    ↓
30分以内に対応開始
    ↓
1時間以内に復旧見込みなし
    ↓
第二責任者にエスカレーション
    ↓
2時間以内に復旧見込みなし
    ↓
経営層に報告
```

---

## チェックリスト

### 日次チェック
- [ ] バックアップが正常に実行されたか確認
- [ ] ディスク容量の確認
- [ ] ログにエラーがないか確認

### 週次チェック
- [ ] バックアップの整合性検証
- [ ] 古いバックアップの削除確認
- [ ] システムリソースの確認

### 月次チェック
- [ ] リカバリーテストの実施
- [ ] DR計画の見直し
- [ ] 連絡先の更新確認

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 承認者 |
|-----------|------|----------|--------|
| 1.0 | 2024/12/29 | 初版作成 | [名前] |

---

**次回レビュー予定**: 2025年3月29日
