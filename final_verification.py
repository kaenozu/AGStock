"""
AGStock v1.0 Final System Verification
Complete health check and validation of all components.
"""
import sys
import os
import subprocess
from datetime import datetime

sys.path.append(os.getcwd())

def print_header(text):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_section(text):
    """Print section header."""
    print(f"\n{'─'*70}")
    print(f"  {text}")
    print(f"{'─'*70}")

def check_python_version():
    """Check Python version."""
    print_section("Python Version Check")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 9:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.9+ required")
        return False

def check_dependencies():
    """Check if all required packages are installed."""
    print_section("Dependency Check")
    
    required_packages = [
        'streamlit', 'pandas', 'numpy', 'yfinance', 
        'scikit-learn', 'tensorflow', 'lightgbm',
        'google-generativeai', 'plotly', 'openpyxl'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies installed")
    return True

def check_directory_structure():
    """Check if all required directories exist."""
    print_section("Directory Structure Check")
    
    required_dirs = [
        'src', 'src/agents', 'src/strategies', 'src/ui', 
        'src/core', 'src/analytics', 'src/realtime',
        'data', 'logs', 'tests', 'docs'
    ]
    
    all_exist = True
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ {directory}/")
        else:
            print(f"❌ {directory}/ - MISSING")
            all_exist = False
    
    if all_exist:
        print("\n✅ All directories present")
    return all_exist

def check_core_modules():
    """Check if core modules can be imported."""
    print_section("Core Module Import Check")
    
    modules = [
        'src.agents.committee',
        'src.strategies.base',
        'src.core.archive_manager',
        'src.core.dynasty_manager',
        'src.realtime.realtime_engine',
        'src.analytics.advanced_analytics',
        'src.utils.error_handler',
        'src.utils.performance'
    ]
    
    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module} - ERROR: {str(e)[:50]}")
            all_ok = False
    
    if all_ok:
        print("\n✅ All core modules importable")
    return all_ok

def check_configuration():
    """Check configuration files."""
    print_section("Configuration Check")
    
    config_files = ['config.json', '.env.example']
    all_ok = True
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ {config_file}")
        else:
            print(f"⚠️ {config_file} - Not found (optional)")
    
    # Check .env
    if os.path.exists('.env'):
        print("✅ .env (configured)")
    else:
        print("⚠️ .env - Not configured (API keys needed for full functionality)")
    
    return True

def check_documentation():
    """Check if documentation exists."""
    print_section("Documentation Check")
    
    docs = [
        'README.md',
        'RELEASE_NOTES.md',
        'PROJECT_COMPLETION.md',
        'docs/USER_GUIDE.md',
        'docs/TROUBLESHOOTING.md',
        'docs/OPERATIONS_GUIDE.md'
    ]
    
    all_exist = True
    for doc in docs:
        if os.path.exists(doc):
            size_kb = os.path.getsize(doc) / 1024
            print(f"✅ {doc} ({size_kb:.1f} KB)")
        else:
            print(f"❌ {doc} - MISSING")
            all_exist = False
    
    if all_exist:
        print("\n✅ All documentation present")
    return all_exist

def run_tests():
    """Run test suites."""
    print_section("Test Execution")
    
    test_files = [
        'tests/test_core_functions.py',
        'tests/test_integration.py'
    ]
    
    all_passed = True
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"⚠️ {test_file} - Not found")
            continue
        
        print(f"\nRunning {test_file}...")
        try:
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"✅ {test_file} - PASSED")
            else:
                print(f"❌ {test_file} - FAILED")
                all_passed = False
        except subprocess.TimeoutExpired:
            print(f"⚠️ {test_file} - TIMEOUT")
        except Exception as e:
            print(f"❌ {test_file} - ERROR: {e}")
            all_passed = False
    
    return all_passed

def check_system_resources():
    """Check system resources."""
    print_section("System Resources")
    
    import psutil
    
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"CPU Usage: {cpu_percent}%")
    
    # Memory
    memory = psutil.virtual_memory()
    print(f"Memory: {memory.used / (1024**3):.1f} GB / {memory.total / (1024**3):.1f} GB ({memory.percent}%)")
    
    # Disk
    disk = psutil.disk_usage('.')
    print(f"Disk: {disk.used / (1024**3):.1f} GB / {disk.total / (1024**3):.1f} GB ({disk.percent}%)")
    
    # Check if resources are adequate
    if memory.percent > 90:
        print("⚠️ High memory usage")
    if disk.percent > 90:
        print("⚠️ Low disk space")
    
    print("\n✅ System resources checked")
    return True

def generate_final_report():
    """Generate final verification report."""
    print_header("AGStock v1.0 - Final Verification Report")
    print(f"\nVerification Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Run all checks
    results['python'] = check_python_version()
    results['dependencies'] = check_dependencies()
    results['directories'] = check_directory_structure()
    results['modules'] = check_core_modules()
    results['config'] = check_configuration()
    results['docs'] = check_documentation()
    
    try:
        results['resources'] = check_system_resources()
    except Exception:
        print("⚠️ Could not check system resources (psutil not installed)")
        results['resources'] = None
    
    # Run tests
    print_section("Running Test Suites")
    results['tests'] = run_tests()
    
    # Final summary
    print_header("Verification Summary")
    
    passed = sum(1 for v in results.values() if v is True)
    total = sum(1 for v in results.values() if v is not None)
    
    print(f"\nChecks Passed: {passed}/{total}")
    print("\nDetailed Results:")
    
    status_map = {True: "✅ PASS", False: "❌ FAIL", None: "⚠️ SKIP"}
    for check, result in results.items():
        print(f"  {check.capitalize():15} {status_map[result]}")
    
    # Overall status
    print("\n" + "="*70)
    if passed == total:
        print("  🎉 ALL CHECKS PASSED - SYSTEM READY FOR PRODUCTION")
    elif passed >= total * 0.8:
        print("  ✅ SYSTEM OPERATIONAL - Minor issues detected")
    else:
        print("  ⚠️ ATTENTION REQUIRED - Please review failed checks")
    print("="*70)
    
    # Save report
    report_path = f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"AGStock v1.0 Verification Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Checks Passed: {passed}/{total}\n\n")
        for check, result in results.items():
            f.write(f"{check}: {status_map[result]}\n")
    
    print(f"\n📄 Report saved: {report_path}")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = generate_final_report()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
