"""
BackupManagerのテスト
"""

import os
import sqlite3
import tempfile

import pytest

from src.backup_manager import BackupManager


class TestBackupManager:
    """BackupManagerのテストクラス"""

    @pytest.fixture
    def temp_db(self):
        """テスト用の一時データベース"""
        # 一時DBファイルを作成
        with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
            db_path = f.name

        # テーブルを作成
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)")
        cursor.execute('INSERT INTO test_table (value) VALUES ("test")')
        conn.commit()
        conn.close()

        yield db_path

        # クリーンアップ
        if os.path.exists(db_path):
            os.remove(db_path)

    @pytest.fixture
    def backup_manager(self, temp_db):
        """テスト用のBackupManagerインスタンス"""
        backup_dir = tempfile.mkdtemp()
        bm = BackupManager(source_db=temp_db, backup_dir=backup_dir, max_backups=7)

        yield bm

        # クリーンアップ
        import shutil

        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)

    def test_initialization(self, backup_manager):
        """初期化テスト"""
        assert backup_manager is not None
        assert os.path.exists(backup_manager.backup_dir)

    def test_auto_backup_success(self, backup_manager):
        """バックアップ作成成功テスト"""
        backup_path = backup_manager.auto_backup()

        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert backup_path.endswith(".db")
        assert "paper_trading_" in backup_path

    def test_auto_backup_creates_valid_db(self, backup_manager):
        """バックアップが有効なDBであることをテスト"""
        backup_path = backup_manager.auto_backup()

        # バックアップDBを開いて検証
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()

        assert len(tables) > 0

    def test_auto_backup_nonexistent_source(self):
        """存在しないソースDBでのバックアップテスト"""
        bm = BackupManager(source_db="nonexistent.db")
        backup_path = bm.auto_backup()

        assert backup_path is None

    def test_list_backups(self, backup_manager):
        """バックアップリスト取得テスト"""
        # 既存のバックアップを削除
        for f in os.listdir(backup_manager.backup_dir):
            os.remove(os.path.join(backup_manager.backup_dir, f))

        # バックアップを2つ作成
        backup_manager.auto_backup()
        import time

        time.sleep(1.1)  # タイムスタンプを変えるため(秒単位の可能性がある)
        backup_manager.auto_backup()

        backups = backup_manager.list_backups()

        assert len(backups) == 2
        assert all("filename" in b for b in backups)
        assert all("created" in b for b in backups)
        assert all("size_mb" in b for b in backups)

        # 新しい順にソートされているか確認
        if len(backups) > 1:
            assert backups[0]["created"] >= backups[1]["created"]

    def test_cleanup_old_backups(self, backup_manager):
        """古いバックアップ削除テスト"""
        # バックアップを作成
        backup_path = backup_manager.auto_backup()

        # ファイルの更新日時を古くする
        import time

        old_time = time.time() - (8 * 24 * 60 * 60)  # 8日前
        os.utime(backup_path, (old_time, old_time))

        # クリーンアップ（7日以上を削除）
        deleted_count = backup_manager.cleanup_old_backups(days=7)

        assert deleted_count == 1
        assert not os.path.exists(backup_path)

    def test_restore_backup_success(self, backup_manager, temp_db):
        """バックアップ復元成功テスト"""
        # バックアップを作成
        backup_path = backup_manager.auto_backup()

        # ソースDBを変更
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO test_table (value) VALUES ("modified")')
        conn.commit()
        conn.close()

        # 復元
        result = backup_manager.restore_backup(backup_path, confirm=True)

        assert result == True

        # 復元後のデータを確認
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_table")
        count = cursor.fetchone()[0]
        conn.close()

        # 復元により元の1行に戻っているはず
        assert count == 1

    def test_restore_backup_without_confirmation(self, backup_manager):
        """確認なしでの復元失敗テスト"""
        backup_path = backup_manager.auto_backup()

        result = backup_manager.restore_backup(backup_path, confirm=False)

        assert result == False

    def test_restore_backup_nonexistent_file(self, backup_manager):
        """存在しないバックアップファイルでの復元テスト"""
        result = backup_manager.restore_backup("nonexistent.db", confirm=True)

        assert result == False

    def test_get_latest_backup(self, backup_manager):
        """最新バックアップ取得テスト"""
        # バックアップがない状態
        latest = backup_manager.get_latest_backup()
        assert latest is None

        # バックアップを作成
        backup_manager.auto_backup()
        import time

        time.sleep(0.1)
        backup_path2 = backup_manager.auto_backup()

        # 最新を取得
        latest = backup_manager.get_latest_backup()
        assert latest == backup_path2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
