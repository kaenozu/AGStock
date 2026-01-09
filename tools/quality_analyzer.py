"""
Code Quality Analyzer for AGStock
Analyzes code quality and suggests improvements.
"""
import os
import ast
import re
from typing import Dict, List, Any
from pathlib import Path

class CodeQualityAnalyzer:
    """Analyze Python code quality."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.issues = []
        self.metrics = {
            "total_files": 0,
            "total_lines": 0,
            "total_functions": 0,
            "total_classes": 0,
            "docstring_coverage": 0,
            "type_hint_coverage": 0,
            "complexity_issues": 0
        }
    
    def analyze_project(self) -> Dict[str, Any]:
        """Analyze entire project."""
        print("🔍 Analyzing code quality...")
        
        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if "venv" not in str(f) and ".venv" not in str(f)]
        
        self.metrics["total_files"] = len(python_files)
        
        for file_path in python_files:
            self._analyze_file(file_path)
        
        # Calculate coverage percentages
        if self.metrics["total_functions"] > 0:
            self.metrics["docstring_coverage"] = (
                self.metrics.get("documented_functions", 0) / 
                self.metrics["total_functions"] * 100
            )
        
        return {
            "metrics": self.metrics,
            "issues": self.issues,
            "recommendations": self._generate_recommendations()
        }
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            self.metrics["total_lines"] += len(lines)
            
            # Parse AST
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree, file_path)
            except SyntaxError:
                self.issues.append({
                    "file": str(file_path),
                    "type": "SYNTAX_ERROR",
                    "severity": "HIGH",
                    "message": "File has syntax errors"
                })
            
            # Check for common issues
            self._check_code_style(content, file_path)
            
        except Exception as e:
            self.issues.append({
                "file": str(file_path),
                "type": "READ_ERROR",
                "severity": "HIGH",
                "message": f"Could not read file: {e}"
            })
    
    def _analyze_ast(self, tree: ast.AST, file_path: Path):
        """Analyze AST for quality metrics."""
        for node in ast.walk(tree):
            # Count functions
            if isinstance(node, ast.FunctionDef):
                self.metrics["total_functions"] += 1
                
                # Check docstring
                if ast.get_docstring(node):
                    self.metrics["documented_functions"] = self.metrics.get("documented_functions", 0) + 1
                else:
                    self.issues.append({
                        "file": str(file_path),
                        "line": node.lineno,
                        "type": "MISSING_DOCSTRING",
                        "severity": "LOW",
                        "message": f"Function '{node.name}' missing docstring"
                    })
                
                # Check type hints
                has_return_hint = node.returns is not None
                has_arg_hints = all(arg.annotation is not None for arg in node.args.args)
                
                if not (has_return_hint and has_arg_hints):
                    self.issues.append({
                        "file": str(file_path),
                        "line": node.lineno,
                        "type": "MISSING_TYPE_HINTS",
                        "severity": "LOW",
                        "message": f"Function '{node.name}' missing type hints"
                    })
                
                # Check complexity
                complexity = self._calculate_complexity(node)
                if complexity > 10:
                    self.metrics["complexity_issues"] += 1
                    self.issues.append({
                        "file": str(file_path),
                        "line": node.lineno,
                        "type": "HIGH_COMPLEXITY",
                        "severity": "MEDIUM",
                        "message": f"Function '{node.name}' has high complexity ({complexity})"
                    })
            
            # Count classes
            elif isinstance(node, ast.ClassDef):
                self.metrics["total_classes"] += 1
                
                if not ast.get_docstring(node):
                    self.issues.append({
                        "file": str(file_path),
                        "line": node.lineno,
                        "type": "MISSING_DOCSTRING",
                        "severity": "LOW",
                        "message": f"Class '{node.name}' missing docstring"
                    })
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _check_code_style(self, content: str, file_path: Path):
        """Check code style issues."""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 120:
                self.issues.append({
                    "file": str(file_path),
                    "line": i,
                    "type": "LINE_TOO_LONG",
                    "severity": "LOW",
                    "message": f"Line exceeds 120 characters ({len(line)} chars)"
                })
            
            # Check for print statements (should use logging)
            if re.search(r'\bprint\s*\(', line) and 'logger' not in content:
                self.issues.append({
                    "file": str(file_path),
                    "line": i,
                    "type": "PRINT_STATEMENT",
                    "severity": "LOW",
                    "message": "Use logging instead of print()"
                })
    
    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        # Docstring coverage
        if self.metrics.get("docstring_coverage", 0) < 80:
            recommendations.append(
                f"📝 Improve docstring coverage: Currently {self.metrics.get('docstring_coverage', 0):.1f}%, "
                f"target is 80%+"
            )
        
        # Complexity
        if self.metrics.get("complexity_issues", 0) > 0:
            recommendations.append(
                f"🔧 Refactor {self.metrics['complexity_issues']} complex functions "
                f"(complexity > 10)"
            )
        
        # Type hints
        type_hint_issues = sum(1 for issue in self.issues if issue["type"] == "MISSING_TYPE_HINTS")
        if type_hint_issues > 0:
            recommendations.append(
                f"🏷️ Add type hints to {type_hint_issues} functions for better IDE support"
            )
        
        # High severity issues
        high_severity = sum(1 for issue in self.issues if issue["severity"] == "HIGH")
        if high_severity > 0:
            recommendations.append(
                f"🚨 Fix {high_severity} high-severity issues immediately"
            )
        
        return recommendations
    
    def generate_report(self, output_file: str = "quality_report.md"):
        """Generate quality report."""
        analysis = self.analyze_project()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# AGStock Code Quality Report\n\n")
            f.write(f"**Generated**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Metrics
            f.write("## 📊 Metrics\n\n")
            f.write(f"- **Total Files**: {analysis['metrics']['total_files']}\n")
            f.write(f"- **Total Lines**: {analysis['metrics']['total_lines']:,}\n")
            f.write(f"- **Total Functions**: {analysis['metrics']['total_functions']}\n")
            f.write(f"- **Total Classes**: {analysis['metrics']['total_classes']}\n")
            f.write(f"- **Docstring Coverage**: {analysis['metrics'].get('docstring_coverage', 0):.1f}%\n")
            f.write(f"- **Complexity Issues**: {analysis['metrics'].get('complexity_issues', 0)}\n\n")
            
            # Issues by severity
            f.write("## ⚠️ Issues by Severity\n\n")
            for severity in ["HIGH", "MEDIUM", "LOW"]:
                count = sum(1 for issue in analysis['issues'] if issue['severity'] == severity)
                f.write(f"- **{severity}**: {count}\n")
            
            f.write("\n## 💡 Recommendations\n\n")
            for rec in analysis['recommendations']:
                f.write(f"- {rec}\n")
            
            # Top issues
            f.write("\n## 🔍 Top Issues\n\n")
            high_issues = [i for i in analysis['issues'] if i['severity'] in ['HIGH', 'MEDIUM']][:10]
            
            for issue in high_issues:
                f.write(f"### {issue['type']} ({issue['severity']})\n")
                f.write(f"- **File**: `{issue['file']}`\n")
                if 'line' in issue:
                    f.write(f"- **Line**: {issue['line']}\n")
                f.write(f"- **Message**: {issue['message']}\n\n")
        
        print(f"✅ Quality report generated: {output_file}")
        return output_file


def main():
    """Run quality analysis."""
    print("="*70)
    print("  AGStock Code Quality Analysis")
    print("="*70)
    
    analyzer = CodeQualityAnalyzer()
    report_file = analyzer.generate_report()
    
    # Print summary
    analysis = analyzer.analyze_project()
    
    print(f"\n📊 Summary:")
    print(f"  Files analyzed: {analysis['metrics']['total_files']}")
    print(f"  Total lines: {analysis['metrics']['total_lines']:,}")
    print(f"  Issues found: {len(analysis['issues'])}")
    print(f"  Docstring coverage: {analysis['metrics'].get('docstring_coverage', 0):.1f}%")
    
    print(f"\n📄 Full report: {report_file}")
    
    return analysis


if __name__ == "__main__":
    main()
