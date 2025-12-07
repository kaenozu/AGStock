"""
DatabaseMaintenanceの包括的なテスト
"""
import pytest
from unittest.mock import patch, MagicMock
import os
import sqlite3
from src.db_maintenance import DatabaseMaintenance


@pytest.fixture
def mock_sqlite():
    with patch('sqlite3.connect') as mock:
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        mock.return_value = conn
        yield mock


@pytest.fixture
def mock_path():
    with patch('src.db_maintenance.Path') as mock:
        yield mock


@pytest.fixture
def maintenance(mock_path):
    return DatabaseMaintenance(db_path="test.db")


def test_init(maintenance):
    """初期化のテスト"""
    assert maintenance.db_path == "test.db"
    maintenance.backup_dir.mkdir.assert_called_with(exist_ok=True)


def test_create_indexes(maintenance, mock_sqlite):
    """インデックス作成のテスト"""
    result = maintenance.create_indexes()
    
    assert result is True
    conn = mock_sqlite.return_value
    cursor = conn.cursor.return_value
    assert cursor.execute.call_count >= 4 # 4つのインデックス
    conn.commit.assert_called()
    conn.close.assert_called()


def test_create_indexes_error(maintenance, mock_sqlite):
    """インデックス作成エラーのテスト"""
    mock_sqlite.side_effect = Exception("DB Error")
    result = maintenance.create_indexes()
    assert result is False


@patch('src.db_maintenance.shutil.copy2')
@patch('src.db_maintenance.datetime')
def test_backup_database(mock_datetime, mock_copy, maintenance):
    """データベースバックアップのテスト"""
    mock_datetime.now.return_value.strftime.return_value = "20230101_100000"
    
    # Pathオブジェクトのモック動作調整
    maintenance.backup_dir.__truediv__.return_value = MagicMock(__str__=lambda x: "backups/test_20230101_100000.db")
    
    path = maintenance.backup_database()
    
    assert "backups/test_20230101_100000.db" in path
    mock_copy.assert_called()


@patch('src.db_maintenance.shutil.copy2')
def test_backup_database_error(mock_copy, maintenance):
    """バックアップエラーのテスト"""
    mock_copy.side_effect = Exception("IO Error")
    path = maintenance.backup_database()
    assert path == ""


def test_cleanup_old_backups(maintenance):
    """古いバックアップ削除のテスト"""
    # globの戻り値をモック
    file1 = MagicMock()
    file2 = MagicMock()
    file3 = MagicMock()
    
    maintenance.backup_dir.glob.return_value = [file1, file2, file3]
    
    # os.path.getmtimeをモックしてソート順を制御
    with patch('os.path.getmtime', side_effect=[100, 200, 300]):
        # keep=1にするので、2つ削除されるはず
        maintenance._cleanup_old_backups(keep=1)
        
        # 実際にはsortedでreverse=Trueなので、300(file3), 200(file2), 100(file1)の順
        # keep=1なら、file3が残って、file2とfile1が削除される
        
        assert file2.unlink.called
        assert file1.unlink.called
        assert not file3.unlink.called


def test_vacuum_database(maintenance, mock_sqlite):
    """VACUUM実行のテスト"""
    result = maintenance.vacuum_database()
    
    assert result is True
    conn = mock_sqlite.return_value
    conn.execute.assert_called_with("VACUUM")
    conn.close.assert_called()


def test_get_database_stats(maintenance, mock_sqlite):
    """データベース統計取得のテスト"""
    conn = mock_sqlite.return_value
    cursor = conn.cursor.return_value
    
    # テーブル一覧
    cursor.fetchall.return_value = [('orders',), ('positions',)]
    # カウント
    cursor.fetchone.side_effect = [(100,), (50,)]
    
    with patch('os.path.getsize', return_value=1024*1024): # 1MB
        stats = maintenance.get_database_stats()
        
        assert stats['orders_count'] == 100
        assert stats['positions_count'] == 50
        assert stats['file_size_mb'] == 1.0
