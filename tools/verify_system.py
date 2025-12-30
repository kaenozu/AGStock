import sys
import os

# Add src to path
sys.path.append(os.getcwd())

def verify():
    print("Checking dependencies and imports...")
    try:
        from src.strategies.ensemble import EnsembleStrategy
        from src.paper_trader import PaperTrader
        from src.data_loader import fetch_stock_data
        print("✅ Core imports successful.")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

    print("Checking database connection...")
    try:
        from src.db.manager import DatabaseManager
        db = DatabaseManager()
        # Just check if we can initialize
        print("✅ Database manager initialized.")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        # Not returning False because DB might not be set up in this env
    
    print("Checking for syntax errors in entire src folder...")
    # This is already done by our error_summary.py, but good to double check
    import py_compile
    from pathlib import Path
    
    errors = 0
    for py_file in Path("src").rglob("*.py"):
        try:
            py_compile.compile(str(py_file), doraise=True)
        except Exception as e:
            print(f"❌ Syntax Error in {py_file}: {e}")
            errors += 1
            
    if errors == 0:
        print("✅ No syntax errors found in src/.")
    else:
        print(f"❌ Found {errors} syntax errors.")
        return False

    print("\nSystem verification PASSED!")
    return True

if __name__ == "__main__":
    if verify():
        sys.exit(0)
    else:
        sys.exit(1)
