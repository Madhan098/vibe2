"""
Code analyzer using Python AST to extract coding patterns
"""
import ast
import re
from typing import Dict, List, Tuple


def analyze_code(files: List[Dict[str, str]]) -> Dict:
    """Alias for analyze_code_files for backward compatibility"""
    return analyze_code_files(files)


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
        'total_lines': 0,
        'class_names': [],
        'total_classes': 0,
        'has_module_docstring': 0,
        'comment_lines': 0,
        'files_analyzed': 0
    }
    
    for file_data in files:
        try:
            content = file_data.get('content', '')
            if not content or not content.strip():
                continue
                
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
            all_patterns['total_lines'] += patterns['total_lines']
            all_patterns['class_names'].extend(patterns['class_names'])
            all_patterns['total_classes'] += patterns['total_classes']
            all_patterns['has_module_docstring'] += patterns['has_module_docstring']
            all_patterns['comment_lines'] += patterns['comment_lines']
            all_patterns['files_analyzed'] += 1
            
        except SyntaxError as e:
            # Try to extract basic patterns even with syntax errors
            content = file_data.get('content', '')
            if content:
                # Extract variable names using regex as fallback
                import re
                var_pattern = r'\b([a-z_][a-z0-9_]*)\s*='
                matches = re.findall(var_pattern, content)
                all_patterns['variable_names'].extend(matches)
                all_patterns['total_lines'] += len(content.split('\n'))
                all_patterns['files_analyzed'] += 1
            continue
        except Exception as e:
            print(f"Error analyzing {file_data.get('filename', 'unknown')}: {e}")
            # Still count the file
            content = file_data.get('content', '')
            if content:
                all_patterns['total_lines'] += len(content.split('\n'))
                all_patterns['files_analyzed'] += 1
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
        'function_lengths': [],
        'class_names': [],
        'total_classes': 0,
        'has_module_docstring': 0,
        'comment_lines': 0,
        'total_lines': 0
    }
    
    lines = source_code.split('\n')
    patterns['total_lines'] = len(lines)
    
    # Check for module-level docstring
    if ast.get_docstring(tree):
        patterns['has_module_docstring'] = 1
    
    # Count comment lines
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#') and len(stripped) > 1:
            patterns['comment_lines'] += 1
    
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
        
        # Class definitions
        elif isinstance(node, ast.ClassDef):
            patterns['total_classes'] += 1
            patterns['class_names'].append(node.name)
            # Check for class docstring
            if ast.get_docstring(node):
                patterns['has_docstrings'] += 1
        
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
    
    # Filter out very short names and common keywords
    filtered_names = [n for n in names if len(n) > 1 and n not in ['i', 'j', 'k', 'x', 'y', 'z', 'id', 'ok']]
    if not filtered_names:
        filtered_names = names  # Use all names if filtering removed everything
    
    snake_case_count = 0
    camel_case_count = 0
    pascal_case_count = 0
    
    for name in filtered_names:
        if '_' in name and name.islower():
            snake_case_count += 1
        elif name[0].isupper() and '_' not in name:
            pascal_case_count += 1
        elif name[0].islower() and '_' not in name:
            camel_case_count += 1
    
    total = len(filtered_names)
    if total == 0:
        return ('snake_case', 0.0)
    
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
        # Mixed style - return the most common
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
    score = 40  # Base score (lowered to allow for more variation)
    
    # Documentation bonus
    if patterns['total_functions'] > 0:
        doc_coverage = (patterns['has_docstrings'] / patterns['total_functions']) * 100
        score += (doc_coverage / 100) * 20  # Up to 20 points
    elif patterns['has_module_docstring'] > 0:
        # Bonus for module-level docstring even without functions
        score += 10
    
    # Type hints bonus
    if patterns['total_functions'] > 0:
        type_hint_coverage = (patterns['functions_with_type_hints'] / patterns['total_functions']) * 100
        score += (type_hint_coverage / 100) * 15  # Up to 15 points
    
    # Comment coverage bonus (for files without functions)
    if patterns['total_lines'] > 0:
        comment_coverage = (patterns['comment_lines'] / patterns['total_lines']) * 100
        if comment_coverage > 10:  # At least 10% comments
            score += min(15, comment_coverage / 10)  # Up to 15 points
    
    # Error handling bonus
    total_error_handling = patterns['error_handling_style']['try_except'] + patterns['error_handling_style']['if_else']
    if total_error_handling > 0:
        score += 10  # Bonus for having error handling
    
    # Structure bonus (has functions or classes)
    if patterns['total_functions'] > 0 or patterns['total_classes'] > 0:
        score += 10  # Bonus for structured code
    
    # Function length penalty (very long functions reduce score)
    if patterns['function_lengths']:
        avg_length = sum(patterns['function_lengths']) / len(patterns['function_lengths'])
        if avg_length > 50:
            score -= 10
        elif avg_length > 100:
            score -= 20
    
    # Ensure minimum score for any code
    if patterns['total_lines'] > 0:
        score = max(score, 30)  # Minimum 30 for any valid code
    
    return min(100, max(0, int(score)))


def generate_report(patterns: Dict) -> Dict:
    """Generate final style report"""
    # Naming style - include class names too
    all_names = patterns['function_names'] + patterns['variable_names'] + patterns['class_names']
    naming_style, naming_confidence = detect_naming_style(all_names)
    
    # Documentation percentage
    doc_percentage = 0
    if patterns['total_functions'] > 0:
        doc_percentage = (patterns['has_docstrings'] / patterns['total_functions']) * 100
    elif patterns['has_module_docstring'] > 0:
        # If no functions but has module docstring, show some documentation
        doc_percentage = 20.0
    
    # Type hints percentage
    type_hints_percentage = 0
    if patterns['total_functions'] > 0:
        type_hints_percentage = (patterns['functions_with_type_hints'] / patterns['total_functions']) * 100
    
    # Error handling style
    error_style = detect_error_handling_style(patterns)
    
    # Code quality
    quality_score = calculate_code_quality(patterns)
    
    # If no functions found but we have code, adjust naming confidence
    if patterns['total_functions'] == 0 and len(all_names) > 0:
        # Use variable/class names for naming confidence
        naming_confidence = max(naming_confidence, 30.0)  # At least 30% if we have names
    
    return {
        'naming_style': naming_style,
        'naming_confidence': round(naming_confidence, 1),
        'documentation_percentage': round(doc_percentage, 1),
        'type_hints_percentage': round(type_hints_percentage, 1),
        'error_handling_style': error_style,
        'code_quality_score': quality_score,
        'total_functions': patterns['total_functions'],
        'total_classes': patterns['total_classes'],
        'total_lines': patterns['total_lines'],
        'files_analyzed': patterns.get('files_analyzed', 1)
    }
