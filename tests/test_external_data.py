"""
外部データ取得のテスト
"""

import pytest
from src.data_loader import DataLoader

def test_fetch_external_data():
    """外部データ取得のテスト"""
    loader = DataLoader()
    data = loader.fetch_external_data(period="1mo")
    
    # 期待されるキーが存在するか
    expected_keys = ['VIX', 'USDJPY', 'SP500', 'NIKKEI']
    
    # 少なくともいくつか取れているか（ネットワーク依存なので厳密にはしない）
    found_keys = [k for k in expected_keys if k in data]
    assert len(found_keys) > 0
    
    # データフレームの中身確認
    for key in found_keys:
        df = data[key]
        assert not df.empty
        assert 'Close' in df.columns
