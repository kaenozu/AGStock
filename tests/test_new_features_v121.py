import pytest
import sys
import os

# パスを通す
sys.path.append(os.getcwd())

from src.optimization.genetic_breeder import GeneticStrategyBreeder, StrategyDNA
from src.mobile.commander import MobileCommander
from src.ui.war_room import render_war_room

class TestGeneticBreeder:
    """遺伝的アルゴリズムエンジンのテスト"""
    
    def test_initialization(self):
        """初期個体群の生成テスト"""
        breeder = GeneticStrategyBreeder(population_size=10)
        breeder.initialize_population()
        
        assert len(breeder.population) == 10
        assert isinstance(breeder.population[0], StrategyDNA)
        assert breeder.population[0].generation == 0
        print("\n✅ Genetic Population initialized successfully.")

    def test_evolution_cycle(self):
        """交配・変異・世代交代のサイクルテスト"""
        breeder = GeneticStrategyBreeder(population_size=10)
        breeder.initialize_population()
        
        # 1世代進める
        breeder.run_generation()
        
        assert breeder.generation_count == 1
        assert len(breeder.population) == 10
        
        # 最良個体の適応度が計算されているか
        best_fitness = breeder.population[0].fitness
        assert best_fitness >= 0
        print(f"\n✅ Evolution cycle completed. Best Fitness: {best_fitness}")

class TestMobileCommander:
    """モバイル司令官の応答テスト"""
    
    def setup_method(self):
        self.commander = MobileCommander()
    
    def test_status_command(self):
        res = self.commander.process_command("Admin", "/status")
        assert "SYSTEM ONLINE" in res
        print("\n✅ Mobile Command '/status' verified.")
        
    def test_emergency_stop(self):
        res = self.commander.process_command("Admin", "/stop")
        assert "EMERGENCY STOP" in res
        print("\n✅ Mobile Command '/stop' verified.")
        
    def test_order_execution(self):
        res = self.commander.process_command("Admin", "/buy 7203.T")
        assert "Order Received" in res
        assert "7203.T" in res
        print("\n✅ Mobile Command '/buy' verified.")

def test_ui_integrity():
    """UIコンポーネントの整合性テスト"""
    # Streamlit関数はレンダリングせずに存在確認のみ
    assert callable(render_war_room)
    print("\n✅ War Room UI component loaded successfully.")
