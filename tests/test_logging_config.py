"""
logging_configのテスト
"""
import pytest
import logging
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.logging_config import JSONFormatter, setup_logging, get_logger


def test_json_formatter_basic():
    """JSONフォーマッターの基本テスト"""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    result = formatter.format(record)
    data = json.loads(result)
    
    assert data['level'] == 'INFO'
    assert data['logger'] == 'test_logger'
    assert data['message'] == 'Test message'
    assert data['module'] == 'test'
    assert data['line'] == 10


def test_json_formatter_with_user_id():
    """ユーザーID付きログのテスト"""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None
    )
    record.user_id = 123
    
    result = formatter.format(record)
    data = json.loads(result)
    
    assert data['user_id'] == 123


def test_json_formatter_with_request_id():
    """リクエストID付きログのテスト"""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None
    )
    record.request_id = "req-123"
    
    result = formatter.format(record)
    data = json.loads(result)
    
    assert data['request_id'] == "req-123"


def test_json_formatter_with_exception():
    """例外情報付きログのテスト"""
    formatter = JSONFormatter()
    
    try:
        1 / 0
    except ZeroDivisionError:
        import sys
        exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert 'exception' in data
        assert 'ZeroDivisionError' in data['exception']


def test_setup_logging_creates_directory(tmp_path):
    """ログディレクトリが作成されることを確認"""
    log_dir = tmp_path / "test_logs"
    
    # 実際にディレクトリ作成とログファイル作成を行わせる
    setup_logging(log_dir=str(log_dir))
    
    assert log_dir.exists()
    assert (log_dir / "agstock.log").exists()


def test_setup_logging_returns_logger():
    """setup_loggingがロガーを返すことを確認"""
    logger = setup_logging(log_level="DEBUG")
    assert isinstance(logger, logging.Logger)


def test_setup_logging_log_level():
    """ログレベルが正しく設定されることを確認"""
    logger = setup_logging(log_level="WARNING")
    assert logger.level == logging.WARNING


def test_get_logger():
    """get_loggerが名前付きロガーを返すことを確認"""
    logger = get_logger("test_module")
    assert logger.name == "test_module"
    assert isinstance(logger, logging.Logger)


def test_get_logger_different_names():
    """異なる名前のロガーが取得できることを確認"""
    logger1 = get_logger("module1")
    logger2 = get_logger("module2")
    
    assert logger1.name == "module1"
    assert logger2.name == "module2"
    assert logger1 is not logger2
