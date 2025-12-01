import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import src.features
    print(f"src.features file: {src.features.__file__}")
    print("Attributes in src.features:")
    for attr in dir(src.features):
        if not attr.startswith("__"):
            print(f"  {attr}")
            
    from src.features import add_technical_indicators
    print("Successfully imported add_technical_indicators")
except Exception as e:
    print(f"Error: {e}")
