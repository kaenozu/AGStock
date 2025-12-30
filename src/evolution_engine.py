
"""
Hyper-Evolution Engine
Implements an automated genetic evolution loop for trading strategies.
Can be run as a cron job or scheduled task.
"""

import logging
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
from copy import deepcopy

from src.strategies.base import Strategy
from src.config import settings
from src.data_loader import fetch_stock_data
# Import strategies dynamically or via registry (simplified for now)
# from src.strategies.registry import get_all_strategies

logger = logging.getLogger("EvolutionEngine")

class Gene:
    """Represents a tunable parameter in a strategy."""
    def __init__(self, name: str, value: Any, min_val: float, max_val: float, is_int: bool = False):
        self.name = name
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.is_int = is_int

    def mutate(self, mutation_rate: float = 0.1, mutation_scale: float = 0.2):
        """Mutate the gene value."""
        if random.random() < mutation_rate:
            change = (self.max_val - self.min_val) * mutation_scale * random.uniform(-1, 1)
            self.value += change
            # Clip
            self.value = max(self.min_val, min(self.max_val, self.value))
            if self.is_int:
                self.value = int(round(self.value))

class Genome:
    """A collection of genes representing a strategy configuration."""
    def __init__(self, strategy_name: str, genes: List[Gene]):
        self.strategy_name = strategy_name
        self.genes = genes
        self.fitness = 0.0

    def to_config(self) -> Dict[str, Any]:
        return {g.name: g.value for g in self.genes}

class EvolutionEngine:
    def __init__(self, population_size: int = 20):
        self.population_size = population_size
        self.generation = 0
        self.population: List[Genome] = []
        
    def initialize_population(self):
        """Create initial random population based on known strategies."""
        # For prototype, we focus on a 'GenericStrategy' with common params
        # In a full version, this would reflect specific strategy classes.
        for _ in range(self.population_size):
            genes = [
                Gene("rsi_period", random.randint(5, 30), 5, 30, True),
                Gene("rsi_oversold", random.uniform(20, 40), 10, 50, False),
                Gene("rsi_overbought", random.uniform(60, 80), 50, 90, False),
                Gene("ma_short", random.randint(5, 50), 5, 100, True),
                Gene("ma_long", random.randint(20, 200), 20, 300, True),
                Gene("stop_loss_pct", random.uniform(0.01, 0.10), 0.01, 0.20, False),
            ]
            self.population.append(Genome("AdaptiveHybrid", genes))
            
    def evaluate_fitness(self, genome: Genome, data_map: Dict[str, pd.DataFrame]) -> float:
        """
        Run a backtest for the genome configuration and return a fitness score.
        Fitness = Returns / MaxDrawdown (Sharpe-like)
        """
        # This is a SIMULATED simplified backtest for performance speed.
        # In production, this would call the actual Backtester class.
        
        try:
            config = genome.to_config()
            total_pnl = 0.0
            
            # Very rough heuristic simulation of the strategy logic
            # (Just to demonstrate the mechanics of the engine)
            for ticker, df in data_map.items():
                if df.empty: continue
                
                # Calculate indicators
                close = df['Close']
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=int(config["rsi_period"])).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=int(config["rsi_period"])).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                
                ma_s = close.rolling(window=int(config["ma_short"])).mean()
                ma_l = close.rolling(window=int(config["ma_long"])).mean()
                
                # Logic: Buy if RSI < Oversold AND MA_S > MA_L (Golden Cross-ish)
                # Sell if RSI > Overbought
                
                position = 0
                entry_price = 0.0
                pnl = 0.0
                
                for i in range(len(df)):
                    if i < 50: continue
                    
                    price = float(close.iloc[i])
                    r = float(rsi.iloc[i])
                    mas = float(ma_s.iloc[i])
                    mal = float(ma_l.iloc[i])
                    
                    if position == 0:
                        if r < config["rsi_oversold"] and mas > mal:
                            position = 1
                            entry_price = price
                    elif position == 1:
                        # Exit trigger
                        details_sl = entry_price * (1 - config["stop_loss_pct"])
                        if r > config["rsi_overbought"] or price < details_sl:
                            position = 0
                            pnl += (price - entry_price) / entry_price
                
                total_pnl += pnl
                
            return total_pnl
            
        except Exception as e:
            logger.error(f"Eval Error: {e}")
            return -999.0

    def evolve(self, data_map: Dict[str, pd.DataFrame]):
        """Run one generation of evolution."""
        # 1. Evaluate
        for genome in self.population:
            genome.fitness = self.evaluate_fitness(genome, data_map)
            
        # 2. Sort by fitness
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        
        best = self.population[0]
        logger.info(f"Gen {self.generation} Best: {best.fitness:.4f} params={best.to_config()}")
        
        # 3. Selection (Elitism)
        retain_count = int(self.population_size * settings.system.elite_retention_pct)
        new_pop = self.population[:retain_count]
        
        # 4. Crossover & Mutation
        while len(new_pop) < self.population_size:
            parent_a = random.choice(self.population[:retain_count])
            parent_b = random.choice(self.population[:retain_count]) # Simple tournament
            
            child_genes = []
            for ga, gb in zip(parent_a.genes, parent_b.genes):
                # Crossover
                val = ga.value if random.random() > 0.5 else gb.value
                gene = Gene(ga.name, val, ga.min_val, ga.max_val, ga.is_int)
                # Mutation
                gene.mutate()
                child_genes.append(gene)
                
            new_pop.append(Genome(parent_a.strategy_name, child_genes))
            
        self.population = new_pop
        self.generation += 1

    def run_evolution_cycle(self, tickers: List[str], generations: int = 5):
        """Main entry point for the evolution task."""
        logger.info("🦕 Starting Hyper-Evolution Cycle...")
        
        # Fetch data once (Parquet cached)
        data_map = fetch_stock_data(tickers, period="6mo") # Shorter period for speed in loop
        
        if not self.population:
            self.initialize_population()
            
        for i in range(generations):
            self.evolve(data_map)
            
        best = self.population[0]
        self.save_best_genome(best)
        logger.info("✅ Evolution Cycle Complete.")
        
    def save_best_genome(self, genome: Genome):
        """Save the best configuration to disk."""
        import json
        out_path = settings.system.data_dir / "best_strategy_params.json"
        with open(out_path, "w") as f:
            json.dump(genome.to_config(), f, indent=4)
        logger.info(f"💾 Saved best params to {out_path}")

if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    engine = EvolutionEngine(population_size=10)
    engine.run_evolution_cycle(settings.tickers_jp, generations=3)
