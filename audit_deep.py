import time
import importlib
import os
import ast
import json
import logging
import pkgutil
import sys
from typing import Dict, Any

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DeepAudit")

def measure_import_speed(module_name: str) -> float:
    if module_name in sys.modules:
        return 0.0
    start = time.time()
    try:
        importlib.import_module(module_name)
        elapsed = time.time() - start
        return elapsed
    except Exception as e:
        logger.error(f"❌ Failed to import {module_name}: {e}")
        return -1.0

def count_complexity(filepath: str) -> int:
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

def scan_directory(base_path: str, base_module: str) -> Dict[str, Any]:
    results = {}
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, start="c:\\gemini-thinkpad\\AGStock")
                
                # Construct module name
                module_rel = os.path.relpath(full_path, start=base_path)
                module_name = base_module + "." + module_rel.replace(os.sep, ".").replace(".py", "")
                
                # Measure
                complexity = count_complexity(full_path)
                imp_time = measure_import_speed(module_name)
                
                results[module_name] = {
                    "complexity": complexity,
                    "import_time": imp_time,
                    "path": rel_path
                }
                logger.info(f"Checked {module_name}: C={complexity}, T={imp_time:.4f}s")
    return results

def run_deep_audit():
    targets = [
        ("src\\strategies", "src.strategies"),
        ("src\\agents", "src.agents"),
        ("src\\ui", "src.ui"),
        ("src\\data", "src.data"),
        ("src\\rag", "src.rag"),
        ("src\\evolution", "src.evolution"),
        ("src\\execution", "src.execution"),
        ("src\\core", "src.core"),
        ("src\\realtime", "src.realtime"),
        ("src\\oracle", "src.oracle"),
        ("src\\simulation", "src.simulation"),
        ("src\\portfolio", "src.portfolio")
    ]
    
    final_report = {}
    
    for path, mod in targets:
        full_path = os.path.join("c:\\gemini-thinkpad\\AGStock", path)
        if os.path.exists(full_path):
            logger.info(f"--- Scanning {mod} ---")
            report = scan_directory(full_path, mod)
            final_report.update(report)
        else:
            logger.warning(f"Path not found: {full_path}")

    with open("deep_audit_report.json", "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=4)
    
    logger.info("🎉 Deep Audit Complete. Saved to deep_audit_report.json")

if __name__ == "__main__":
    run_deep_audit()
