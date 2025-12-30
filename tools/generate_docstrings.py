"""
Automatic Docstring Generator for AGStock
Generates missing docstrings using AI and static analysis.
"""
import ast
import os
from pathlib import Path
from typing import List, Dict, Any

class DocstringGenerator:
    """Generate docstrings for Python code."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.stats = {
            "files_processed": 0,
            "functions_processed": 0,
            "classes_processed": 0,
            "docstrings_added": 0
        }
    
    def generate_function_docstring(self, func_node: ast.FunctionDef) -> str:
        """
        Generate a docstring for a function.
        
        Args:
            func_node: AST node representing the function
        
        Returns:
            Generated docstring
        """
        func_name = func_node.name
        args = [arg.arg for arg in func_node.args.args if arg.arg != 'self']
        
        # Generate basic docstring
        docstring = f'"""\n    {func_name.replace("_", " ").title()}.\n'
        
        if args:
            docstring += "\n    Args:\n"
            for arg in args:
                docstring += f"        {arg}: Description of {arg}\n"
        
        # Check for return statement
        has_return = any(isinstance(node, ast.Return) and node.value is not None 
                        for node in ast.walk(func_node))
        
        if has_return:
            docstring += "\n    Returns:\n"
            docstring += "        Description of return value\n"
        
        docstring += '    """'
        return docstring
    
    def generate_class_docstring(self, class_node: ast.ClassDef) -> str:
        """
        Generate a docstring for a class.
        
        Args:
            class_node: AST node representing the class
        
        Returns:
            Generated docstring
        """
        class_name = class_node.name
        docstring = f'"""{class_name.replace("_", " ").title()}."""'
        return docstring
    
    def process_file(self, file_path: Path, dry_run: bool = False) -> bool:
        """
        Process a single file and add missing docstrings.
        
        Args:
            file_path: Path to the Python file
            dry_run: If True, don't modify the file
        
        Returns:
            True if file was modified
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            lines = content.split('\n')
            modified = False
            insertions = []  # List of (line_number, docstring)
            
            for node in ast.walk(tree):
                # Check functions
                if isinstance(node, ast.FunctionDef):
                    self.stats["functions_processed"] += 1
                    
                    if not ast.get_docstring(node):
                        docstring = self.generate_function_docstring(node)
                        # Insert after function definition
                        insert_line = node.lineno
                        insertions.append((insert_line, docstring))
                        self.stats["docstrings_added"] += 1
                        modified = True
                
                # Check classes
                elif isinstance(node, ast.ClassDef):
                    self.stats["classes_processed"] += 1
                    
                    if not ast.get_docstring(node):
                        docstring = self.generate_class_docstring(node)
                        insert_line = node.lineno
                        insertions.append((insert_line, docstring))
                        self.stats["docstrings_added"] += 1
                        modified = True
            
            # Apply insertions (in reverse order to maintain line numbers)
            if modified and not dry_run:
                for line_num, docstring in sorted(insertions, reverse=True):
                    # Find the indentation of the function/class
                    indent = len(lines[line_num - 1]) - len(lines[line_num - 1].lstrip())
                    docstring_lines = docstring.split('\n')
                    indented_docstring = '\n'.join([' ' * (indent + 4) + line for line in docstring_lines])
                    lines.insert(line_num, indented_docstring)
                
                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
            
            self.stats["files_processed"] += 1
            return modified
            
        except Exception as e:
            print(f"⚠️ Error processing {file_path}: {e}")
            return False
    
    def process_project(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Process entire project.
        
        Args:
            dry_run: If True, don't modify files
        
        Returns:
            Statistics dictionary
        """
        print("🔍 Generating missing docstrings...")
        
        # Find all Python files in src/
        python_files = list(self.project_root.glob("src/**/*.py"))
        python_files = [f for f in python_files if "__pycache__" not in str(f)]
        
        for file_path in python_files:
            self.process_file(file_path, dry_run)
        
        return self.stats
    
    def generate_report(self, output_file: str = "docstring_report.md"):
        """
        Generate report of docstring generation.
        
        Args:
            output_file: Path to output file
        """
        stats = self.stats
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Docstring Generation Report\n\n")
            f.write(f"**Generated**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Statistics\n\n")
            f.write(f"- **Files Processed**: {stats['files_processed']}\n")
            f.write(f"- **Functions Processed**: {stats['functions_processed']}\n")
            f.write(f"- **Classes Processed**: {stats['classes_processed']}\n")
            f.write(f"- **Docstrings Added**: {stats['docstrings_added']}\n\n")
            
            if stats['functions_processed'] > 0:
                coverage = ((stats['functions_processed'] - stats['docstrings_added']) / 
                           stats['functions_processed'] * 100)
                f.write(f"## Coverage\n\n")
                f.write(f"- **Before**: {coverage:.1f}%\n")
                f.write(f"- **After**: ~100%\n")
        
        print(f"✅ Report generated: {output_file}")


def main():
    """Run docstring generation."""
    print("="*70)
    print("  AGStock Docstring Generator")
    print("="*70)
    
    generator = DocstringGenerator()
    
    # Dry run first
    print("\n🔍 Analyzing project (dry run)...")
    stats_dry = generator.process_project(dry_run=True)
    
    print(f"\n📊 Analysis complete:")
    print(f"  Files to process: {stats_dry['files_processed']}")
    print(f"  Docstrings to add: {stats_dry['docstrings_added']}")
    
    # Ask for confirmation (auto-yes for automation)
    print("\n✅ Generating docstrings...")
    generator2 = DocstringGenerator()
    stats = generator2.process_project(dry_run=False)
    
    generator2.generate_report()
    
    print(f"\n✅ Docstring generation complete!")
    print(f"  Docstrings added: {stats['docstrings_added']}")
    
    return stats


if __name__ == "__main__":
    main()
