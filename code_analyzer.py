"""
Code analyzer using Python AST to extract coding patterns
"""
import ast
import re
from typing import Dict, List, Tuple


def analyze_code_files(files: List[Dict[str, str]]) -> Dict:
    """
    Analyze multiple code files and extract aggregated patterns
    
    Args:
        files: List of dicts with 'filename' and 'content' keys
    
    Returns:
        Dict with style patterns
    """
    all_patterns = {
        'function_names': [],
        'variable_names': [],
        'has_docstrings': 0,
        'total_functions': 0,
        'has_type_hints': 0,
        'functions_with_type_hints': 0,
        'error_handling_style': {'try_except': 0, 'if_else': 0},
        'function_lengths': [],
        'total_lines': 0
    }
    
    for file_data in files:
        try:
            content = file_data.get('content', '')
            tree = ast.parse(content)
            patterns = analyze_ast(tree, content)
            
            # Aggregate patterns
            all_patterns['function_names'].extend(patterns['function_names'])
            all_patterns['variable_names'].extend(patterns['variable_names'])
            all_patterns['has_docstrings'] += patterns['has_docstrings']
            all_patterns['total_functions'] += patterns['total_functions']
            all_patterns['has_type_hints'] += patterns['has_type_hints']
            all_patterns['functions_with_type_hints'] += patterns['functions_with_type_hints']
            all_patterns['error_handling_style']['try_except'] += patterns['error_handling_style']['try_except']
            all_patterns['error_handling_style']['if_else'] += patterns['error_handling_style']['if_else']
            all_patterns['function_lengths'].extend(patterns['function_lengths'])
            all_patterns['total_lines'] += len(content.split('\n'))
            
        except SyntaxError:
            # Skip files with syntax errors
            continue
        except Exception as e:
            print(f"Error analyzing {file_data.get('filename', 'unknown')}: {e}")
            continue
    
    return generate_report(all_patterns)


def analyze_ast(tree: ast.AST, source_code: str) -> Dict:
    """Analyze a single AST tree"""
    patterns = {
        'function_names': [],
        'variable_names': [],
        'has_docstrings': 0,
        'total_functions': 0,
        'has_type_hints': 0,
        'functions_with_type_hints': 0,
        'error_handling_style': {'try_except': 0, 'if_else': 0},
        'function_lengths': []
    }
    
    lines = source_code.split('\n')
    
    for node in ast.walk(tree):
        # Function definitions
        if isinstance(node, ast.FunctionDef):
            patterns['total_functions'] += 1
            patterns['function_names'].append(node.name)
            
            # Check for docstring
            if ast.get_docstring(node):
                patterns['has_docstrings'] += 1
            
            # Check for type hints
            if node.returns or any(arg.annotation for arg in node.args.args):
                patterns['has_type_hints'] += 1
                patterns['functions_with_type_hints'] += 1
            
            # Calculate function length
            if node.lineno and node.end_lineno:
                func_length = node.end_lineno - node.lineno
                patterns['function_lengths'].append(func_length)
        
        # Variable assignments
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    patterns['variable_names'].append(target.id)
        
        # Try/except blocks
        elif isinstance(node, ast.Try):
            patterns['error_handling_style']['try_except'] += 1
        
        # If statements (potential error handling)
        elif isinstance(node, ast.If):
            # Check if it's error handling (checking for None, checking conditions)
            if node.test:
                patterns['error_handling_style']['if_else'] += 1
    
    return patterns


def detect_naming_style(names: List[str]) -> Tuple[str, float]:
    """
    Detect naming style (snake_case, camelCase, PascalCase)
    Returns: (style, confidence %)
    """
    if not names:
        return ('snake_case', 0.0)
    
    snake_case_count = 0
    camel_case_count = 0
    pascal_case_count = 0
    
    for name in names:
        if '_' in name and name.islower():
            snake_case_count += 1
        elif name[0].isupper() and not '_' in name:
            pascal_case_count += 1
        elif name[0].islower() and not '_' in name:
            camel_case_count += 1
    
    total = len(names)
    snake_pct = (snake_case_count / total) * 100
    camel_pct = (camel_case_count / total) * 100
    pascal_pct = (pascal_case_count / total) * 100
    
    # Determine dominant style
    if snake_pct >= 50:
        return ('snake_case', snake_pct)
    elif camel_pct >= 50:
        return ('camelCase', camel_pct)
    elif pascal_pct >= 50:
        return ('PascalCase', pascal_pct)
    else:
        # Mixed style
        max_pct = max(snake_pct, camel_pct, pascal_pct)
        if max_pct == snake_pct:
            return ('snake_case', snake_pct)
        elif max_pct == camel_pct:
            return ('camelCase', camel_pct)
        else:
            return ('PascalCase', pascal_pct)


def detect_error_handling_style(patterns: Dict) -> str:
    """Detect error handling style"""
    try_except = patterns['error_handling_style']['try_except']
    if_else = patterns['error_handling_style']['if_else']
    
    total = try_except + if_else
    if total == 0:
        return 'basic'
    
    if try_except > if_else * 2:
        return 'try_except'
    elif if_else > try_except * 2:
        return 'if_else'
    else:
        return 'mixed'


def calculate_code_quality(patterns: Dict) -> int:
    """Calculate code quality score (0-100)"""
    score = 50  # Base score
    
    # Documentation bonus
    if patterns['total_functions'] > 0:
        doc_coverage = (patterns['has_docstrings'] / patterns['total_functions']) * 100
        score += (doc_coverage / 100) * 20  # Up to 20 points
    
    # Type hints bonus
    if patterns['total_functions'] > 0:
        type_hint_coverage = (patterns['functions_with_type_hints'] / patterns['total_functions']) * 100
        score += (type_hint_coverage / 100) * 15  # Up to 15 points
    
    # Error handling bonus
    total_error_handling = patterns['error_handling_style']['try_except'] + patterns['error_handling_style']['if_else']
    if total_error_handling > 0:
        score += 10  # Bonus for having error handling
    
    # Function length penalty (very long functions reduce score)
    if patterns['function_lengths']:
        avg_length = sum(patterns['function_lengths']) / len(patterns['function_lengths'])
        if avg_length > 50:
            score -= 10
        elif avg_length > 100:
            score -= 20
    
    return min(100, max(0, int(score)))


def generate_report(patterns: Dict) -> Dict:
    """Generate final style report"""
    # Naming style
    all_names = patterns['function_names'] + patterns['variable_names']
    naming_style, naming_confidence = detect_naming_style(all_names)
    
    # Documentation percentage
    doc_percentage = 0
    if patterns['total_functions'] > 0:
        doc_percentage = (patterns['has_docstrings'] / patterns['total_functions']) * 100
    
    # Type hints percentage
    type_hints_percentage = 0
    if patterns['total_functions'] > 0:
        type_hints_percentage = (patterns['functions_with_type_hints'] / patterns['total_functions']) * 100
    
    # Error handling style
    error_style = detect_error_handling_style(patterns)
    
    # Code quality
    quality_score = calculate_code_quality(patterns)
    
    return {
        'naming_style': naming_style,
        'naming_confidence': round(naming_confidence, 1),
        'documentation_percentage': round(doc_percentage, 1),
        'type_hints_percentage': round(type_hints_percentage, 1),
        'error_handling_style': error_style,
        'code_quality_score': quality_score,
        'total_functions': patterns['total_functions'],
        'total_files': len(patterns.get('files_analyzed', [1]))
    }
