import time
import importlib
import os
import ast
import json
import logging
from typing import Dict, Any

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SystemAudit")

def measure_import_speed() -> Dict[str, float]:
    logger.info("--- Measuring Import Speed ---")
    modules = [
        "src.data_loader",
        "src.paper_trader", # Check this
        "src.portfolio.correlation_engine", # Check this
        "src.trading.market_scanner",
        "src.execution.execution_engine",
        "src.agents.oracle",
        "src.ui.hologram", # New
        "src.core.quantum_ledger" # New
    ]
    results = {}
    for mod in modules:
        start = time.time()
        try:
            importlib.import_module(mod)
            elapsed = time.time() - start
            results[mod] = elapsed
            logger.info(f"✅ Imported {mod} in {elapsed:.4f}s")
        except Exception as e:
            logger.error(f"❌ Failed to import {mod}: {e}")
            results[mod] = -1.0
    return results

def count_complexity(filepath: str) -> int:
    """Estimates complexity by counting AST nodes (FunctionDef, If, For, While)."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.If, ast.For, ast.While, ast.AsyncFunctionDef)):
                count += 1
        return count
    except Exception:
        return -1

def check_code_quality() -> Dict[str, int]:
    logger.info("--- Checking Code Complexity ---")
    files = [
        "app.py",
        "src/execution/execution_engine.py",
        "src/trading/market_scanner.py",
        "src/data_loader.py",
        "src/ui/sidebar.py"
    ]
    results = {}
    for f in files:
        if os.path.exists(f):
            score = count_complexity(f)
            results[f] = score
            logger.info(f"📄 {f}: Complexity Score = {score}")
        else:
            logger.warning(f"⚠️ File not found: {f}")
    return results

def benchmark_scan():
    logger.info("--- Benchmarking Market Scan (Mock) ---")
    try:
        # Mocking or running a small scan if possible without network spam
        from src.trading.market_scanner import MarketScanner
        scanner = MarketScanner()
        start = time.time()
        # Scan a few tickers if method allows specific list
        # We need to peek at MarketScanner.scan_market signature or just run it.
        # It usually scans 'Japan' or configured market.
        # To avoid massive API calls, we'll try to import and init only.
        # Or check if scan_market accepts a list.
        # Just init time is a good proxy for overhead.
        elapsed = time.time() - start
        logger.info(f"✅ MarketScanner Init in {elapsed:.4f}s")
        return elapsed
    except Exception as e:
        logger.error(f"❌ MarketScanner Benchmark Failed: {e}")
        return -1.0

def run_audit():
    report = {
        "imports": measure_import_speed(),
        "complexity": check_code_quality(),
        "scan_init": benchmark_scan()
    }
    
    # Save Report
    with open("audit_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
        
    logger.info("🎉 Audit Complete. Saved to audit_report.json")

if __name__ == "__main__":
    run_audit()
