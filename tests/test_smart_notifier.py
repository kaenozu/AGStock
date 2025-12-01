"""
SmartNotifierのテスト
"""
import os
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from src.smart_notifier import SmartNotifier


class TestSmartNotifier:
    """SmartNotifierのテストクラス"""
    
    @pytest.fixture
    def notifier(self):
        """テスト用のSmartNotifierインスタンス"""
        # 一時的なコンフィグファイルを使用
        config = {
            "notifications": {
                "min_confidence": 0.7,
                "min_expected_return": 0.03,
                "quiet_hours": "22:00-07:00",
                "line": {
                    "enabled": False,
                    "token": "test_token"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(config, f)
            config_path = f.name
        
        notifier = SmartNotifier(config_path)
        
        yield notifier
        
        # クリーンアップ
        if os.path.exists(config_path):
            os.remove(config_path)
    
    def test_initialization(self, notifier):
        """初期化テスト"""
        assert notifier is not None
        assert notifier.min_confidence == 0.7
        assert notifier.min_expected_return == 0.03
    
    def test_filter_signals_by_confidence(self, notifier):
        """信頼度によるフィルタリングテスト"""
        signals = [
            {"ticker": "TEST1", "confidence": 0.6, "expected_return": 0.05},  # 信頼度低い
            {"ticker": "TEST2", "confidence": 0.85, "expected_return": 0.05}  # OK
        ]
        
        filtered = notifier.filter_signals(signals)
        
        assert len(filtered) == 1
        assert filtered[0]["ticker"] == "TEST2"
    
    def test_filter_signals_by_expected_return(self, notifier):
        """期待リターンによるフィルタリングテスト"""
        signals = [
            {"ticker": "TEST1", "confidence": 0.85, "expected_return": 0.01},  # リターン低い
            {"ticker": "TEST2", "confidence": 0.85, "expected_return": 0.05}   # OK
        ]
        
        filtered = notifier.filter_signals(signals)
        
        assert len(filtered) == 1
        assert filtered[0]["ticker"] == "TEST2"
    
    def test_filter_signals_empty(self, notifier):
        """空のシグナルリストのテスト"""
        signals = []
        filtered = notifier.filter_signals(signals)
        
        assert len(filtered) == 0
    
    @patch('matplotlib.pyplot.savefig')
    @patch('pandas.DataFrame')
    def test_generate_chart(self, mock_df, mock_savefig, notifier):
        """チャート生成テスト"""
        # モックデータ
        mock_data = MagicMock()
        mock_data.empty = False
        
        with patch('src.data_loader.fetch_stock_data', return_value={"TEST": mock_data}):
            chart_path = notifier.generate_chart("TEST", period="30d")
            
            # チャートが生成されたか確認
            assert chart_path is not None
            assert "TEST" in chart_path
            assert chart_path.endswith(".png")
    
    def test_is_quiet_hours(self, notifier):
        """静穏時間判定テスト"""
        from datetime import datetime
        
        # 22:00-07:00が静穏時間
        with patch('src.smart_notifier.datetime') as mock_datetime:
            # 23:00（静穏時間）
            mock_datetime.now.return_value = datetime(2025, 1, 1, 23, 0)
            assert notifier.is_quiet_hours() == True
            
            # 12:00（通常時間）
            mock_datetime.now.return_value = datetime(2025, 1, 1, 12, 0)
            assert notifier.is_quiet_hours() == False
    
    @patch('requests.post')
    def test_send_line_notify_success(self, mock_post, notifier):
        """LINE通知送信成功テスト"""
        mock_post.return_value.status_code = 200
        
        result = notifier.send_line_notify(
            "Test message",
            token="test_token"
        )
        
        assert result == True
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_send_line_notify_failure(self, mock_post, notifier):
        """LINE通知送信失敗テスト"""
        mock_post.return_value.status_code = 400
        
        result = notifier.send_line_notify(
            "Test message",
            token="test_token"
        )
        
        assert result == False
    
    def test_format_signal_message(self, notifier):
        """シグナルメッセージフォーマットテスト"""
        signal = {
            "ticker": "7203.T",
            "action": "BUY",
            "confidence": 0.85,
            "expected_return": 0.05,
            "reason": "LightGBMによる買いシグナル"
        }
        
        message = notifier.format_signal_message(signal)
        
        assert "7203.T" in message
        assert "BUY" in message
        assert "85" in message  # 85%
        assert "5.0" in message  # 5.0%


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
