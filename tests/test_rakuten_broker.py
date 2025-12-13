from unittest.mock import MagicMock, patch

import pytest

from src.rakuten_broker import RakutenBroker


class TestRakutenBroker:
    @pytest.fixture
    def broker(self):
        with patch("src.rakuten_broker.RakutenBroker._load_config") as mock_load:
            mock_load.return_value = {
                "login_id": "test_id",
                "password": "test_pass",
                "pin_code": "1234",
                "headless": True,
            }
            # os.makedirsのモックも必要だが、__init__で呼ばれるためここでパッチできない
            # 代わりに__init__呼び出し後に属性を設定するアプローチをとるか、
            # RakutenBrokerのインスタンス化自体をパッチ内で制御する

            with patch("os.makedirs"):
                broker = RakutenBroker()
                broker.driver = MagicMock()
                broker.wait = MagicMock()
                return broker

    def test_login_success(self, broker):
        # モックの設定
        broker.wait.until.return_value = MagicMock()
        broker.driver.find_element.return_value = MagicMock()

        # テスト実行
        result = broker.login()

        # 検証
        assert result is True
        broker.driver.get.assert_called_with(RakutenBroker.BASE_URL)

    def test_get_balance_success(self, broker):
        # モックの設定
        mock_elem = MagicMock()
        mock_elem.text = "¥1,000,000"
        broker.wait.until.return_value = mock_elem
        broker.driver.find_element.return_value = mock_elem

        # テスト実行
        balance = broker.get_balance()

        # 検証
        assert balance["total_equity"] == 1000000.0
        assert balance["cash"] == 1000000.0
        assert balance["invested_amount"] == 0.0

    def test_buy_order_success(self, broker):
        # モックの設定
        broker.wait.until.return_value = MagicMock()
        broker.driver.find_element.return_value = MagicMock()

        # テスト実行
        result = broker.buy_order("7203", 100, 2000)

        # 検証
        assert result is True
        # 注文フローの各ステップが呼ばれたか確認（簡易的）
        assert broker.driver.find_element.call_count >= 1

    def test_parse_currency(self, broker):
        assert broker._parse_currency("¥1,234") == 1234.0
        assert broker._parse_currency("1,234円") == 1234.0
        assert broker._parse_currency("invalid") == 0.0
