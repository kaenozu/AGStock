"""
Automatic Code Quality Improver
Automatically fixes common code quality issues.
"""
import os
import re
import ast
from pathlib import Path
from typing import List, Dict, Any
import autopep8
import black

class CodeQualityImprover:
    """Automatically improve code quality."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.improvements_made = []
    
    def improve_project(self, dry_run: bool = False) -> Dict[str, Any]:
        """Improve code quality across the project."""
        print("🔧 Improving code quality...")
        
        # Find all Python files in src/
        python_files = list(self.project_root.glob("src/**/*.py"))
        
        stats = {
            "files_processed": 0,
            "files_improved": 0,
            "improvements": {
                "formatting": 0,
                "imports": 0,
                "docstrings": 0,
                "type_hints": 0
            }
        }
        
        for file_path in python_files:
            if self._should_skip(file_path):
                continue
            
            improved = self._improve_file(file_path, dry_run)
            stats["files_processed"] += 1
            
            if improved:
                stats["files_improved"] += 1
        
        # Count improvements by type
        for improvement in self.improvements_made:
            imp_type = improvement.get("type", "other")
            if imp_type in stats["improvements"]:
                stats["improvements"][imp_type] += 1
        
        return stats
    
    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = ["__pycache__", ".venv", "venv", "test_", "verify_"]
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _improve_file(self, file_path: Path, dry_run: bool = False) -> bool:
        """Improve a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            improved_content = original_content
            file_improved = False
            
            # 1. Format with Black
            try:
                formatted = black.format_str(original_content, mode=black.Mode())
                if formatted != improved_content:
                    improved_content = formatted
                    file_improved = True
                    self.improvements_made.append({
                        "file": str(file_path),
                        "type": "formatting",
                        "message": "Applied Black formatting"
                    })
            except:
                # If Black fails, try autopep8
                try:
                    formatted = autopep8.fix_code(improved_content)
                    if formatted != improved_content:
                        improved_content = formatted
                        file_improved = True
                        self.improvements_made.append({
                            "file": str(file_path),
                            "type": "formatting",
                            "message": "Applied autopep8 formatting"
                        })
                except:
                    pass
            
            # 2. Optimize imports
            optimized = self._optimize_imports(improved_content)
            if optimized != improved_content:
                improved_content = optimized
                file_improved = True
                self.improvements_made.append({
                    "file": str(file_path),
                    "type": "imports",
                    "message": "Optimized imports"
                })
            
            # 3. Add missing module docstrings
            if not improved_content.strip().startswith('"""') and not improved_content.strip().startswith("'''"):
                module_name = file_path.stem
                docstring = f'"""\n{module_name.replace("_", " ").title()} module.\n"""\n'
                improved_content = docstring + improved_content
                file_improved = True
                self.improvements_made.append({
                    "file": str(file_path),
                    "type": "docstrings",
                    "message": "Added module docstring"
                })
            
            # Write improvements if not dry run
            if file_improved and not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(improved_content)
            
            return file_improved
            
        except Exception as e:
            print(f"⚠️ Error improving {file_path}: {e}")
            return False
    
    def _optimize_imports(self, content: str) -> str:
        """Optimize import statements."""
        lines = content.split('\n')
        
        # Find import block
        import_start = -1
        import_end = -1
        
        for i, line in enumerate(lines):
            if line.startswith(('import ', 'from ')):
                if import_start == -1:
                    import_start = i
                import_end = i
        
        if import_start == -1:
            return content
        
        # Extract imports
        imports = lines[import_start:import_end + 1]
        
        # Sort imports
        stdlib_imports = []
        third_party_imports = []
        local_imports = []
        
        for imp in imports:
            if imp.startswith('from .') or imp.startswith('from src.'):
                local_imports.append(imp)
            elif any(lib in imp for lib in ['os', 'sys', 'json', 'datetime', 're', 'typing', 'pathlib']):
                stdlib_imports.append(imp)
            else:
                third_party_imports.append(imp)
        
        # Rebuild import block
        sorted_imports = []
        if stdlib_imports:
            sorted_imports.extend(sorted(stdlib_imports))
            sorted_imports.append('')
        if third_party_imports:
            sorted_imports.extend(sorted(third_party_imports))
            sorted_imports.append('')
        if local_imports:
            sorted_imports.extend(sorted(local_imports))
        
        # Reconstruct content
        new_lines = lines[:import_start] + sorted_imports + lines[import_end + 1:]
        return '\n'.join(new_lines)
    
    def generate_report(self, stats: Dict[str, Any], output_file: str = "quality_improvements.md"):
        """Generate improvement report."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# AGStock Code Quality Improvements\n\n")
            f.write(f"**Generated**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 📊 Summary\n\n")
            f.write(f"- **Files Processed**: {stats['files_processed']}\n")
            f.write(f"- **Files Improved**: {stats['files_improved']}\n")
            f.write(f"- **Improvement Rate**: {stats['files_improved']/max(stats['files_processed'],1)*100:.1f}%\n\n")
            
            f.write("## 🔧 Improvements by Type\n\n")
            for imp_type, count in stats['improvements'].items():
                f.write(f"- **{imp_type.title()}**: {count}\n")
            
            f.write("\n## 📝 Detailed Changes\n\n")
            for improvement in self.improvements_made[:50]:  # Top 50
                f.write(f"### {improvement['file']}\n")
                f.write(f"- **Type**: {improvement['type']}\n")
                f.write(f"- **Change**: {improvement['message']}\n\n")
        
        print(f"✅ Improvement report generated: {output_file}")


def main():
    """Run quality improvements."""
    print("="*70)
    print("  AGStock Code Quality Improvement")
    print("="*70)
    
    improver = CodeQualityImprover()
    
    # First, dry run to see what would be changed
    print("\n🔍 Analyzing potential improvements (dry run)...")
    stats_dry = improver.improve_project(dry_run=True)
    
    print(f"\n📊 Potential improvements:")
    print(f"  Files to improve: {stats_dry['files_improved']}/{stats_dry['files_processed']}")
    
    # Ask for confirmation (auto-yes for automation)
    print("\n✅ Applying improvements...")
    improver2 = CodeQualityImprover()
    stats = improver2.improve_project(dry_run=False)
    
    improver2.generate_report(stats)
    
    print(f"\n✅ Quality improvements complete!")
    print(f"  Files improved: {stats['files_improved']}")
    print(f"  Total improvements: {sum(stats['improvements'].values())}")
    
    return stats


if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print(f"\n⚠️ Missing dependencies: {e}")
        print("Install with: pip install black autopep8")
        exit(1)
