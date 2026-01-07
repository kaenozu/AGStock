
import pytest
import os
import json
from src.trading.collective_intelligence import CollectiveIntelligenceManager

@pytest.fixture
def temp_signal_file(tmp_path):
    file_path = tmp_path / "shared_signals.json"
    return str(file_path)

def test_signal_publication(temp_signal_file):
    """シグナル公開のテスト"""
    cim = CollectiveIntelligenceManager(node_id="test_node")
    cim.shared_signals_path = temp_signal_file
    
    cim.publish_signal("7203", "BUY", 0.9, "Test reason")
    
    signals = cim.fetch_collective_signals()
    assert len(signals) == 1
    assert signals[0]["ticker"] == "7203"
    assert signals[0]["node_id"] == "test_node"

def test_consensus_logic(temp_signal_file):
    """合意形成ロジックのテスト"""
    cim = CollectiveIntelligenceManager(node_id="master")
    cim.shared_signals_path = temp_signal_file
    
    # 3つのノードがBUY、1つがSELL
    cim.publish_signal("7203", "BUY", 0.8, "R1")
    cim.publish_signal("7203", "BUY", 0.7, "R2")
    cim.publish_signal("7203", "BUY", 0.9, "R3")
    cim.publish_signal("7203", "SELL", 0.6, "R4")
    
    consensus = cim.get_consensus_signals()
    
    assert len(consensus) == 1
    assert consensus[0]["ticker"] == "7203"
    assert consensus[0]["action"] == "BUY"
    assert consensus[0]["agreement"] == 0.75 # 3/4
    assert consensus[0]["num_nodes"] == 4

def test_no_consensus_below_threshold(temp_signal_file):
    """合意率が低い場合に採用されないことのテスト"""
    cim = CollectiveIntelligenceManager(node_id="master")
    cim.shared_signals_path = temp_signal_file
    
    # 1対1で合意形成不可
    cim.publish_signal("9984", "BUY", 0.8, "R1")
    cim.publish_signal("9984", "SELL", 0.8, "R2")
    
    consensus = cim.get_consensus_signals()
    
    # 閾値 0.6 を下回るため空リスト
    assert len(consensus) == 0
