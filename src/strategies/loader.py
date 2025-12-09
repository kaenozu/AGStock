import os
import sys
import importlib.util
import inspect
from .base import Strategy

def load_custom_strategies() -> list:
    custom_strategies = []
    # Adjust path to find 'custom' directory relative to this file
    # Provided structure is src/strategies/loader.py, so custom dir would be src/strategies/custom
    current_dir = os.path.dirname(__file__)
    custom_dir = os.path.join(current_dir, "custom")
    
    if not os.path.exists(custom_dir):
        # Also check legacy location just in case: src/strategies_legacy.py was in src/
        # so custom might be in src/custom
        legacy_custom_dir = os.path.join(current_dir, "..", "custom")
        if os.path.exists(legacy_custom_dir):
            custom_dir = legacy_custom_dir
        else:
            return custom_strategies
        
    for filename in os.listdir(custom_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            filepath = os.path.join(custom_dir, filename)
            # Module name construction needs to be safe
            module_name = f"src.strategies.custom.{filename[:-3]}"
            
            try:
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, Strategy) and obj is not Strategy:
                            try:
                                strategy_instance = obj()
                                custom_strategies.append(strategy_instance)
                                print(f"Loaded custom strategy: {strategy_instance.name}")
                            except Exception as e:
                                print(f"Failed to instantiate {name}: {e}")
            except Exception as e:
                print(f"Failed to load custom strategy from {filename}: {e}")
                
    return custom_strategies
