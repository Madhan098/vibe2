"""
Style DNA Extraction - Core Innovation
Extracts unique coding patterns from user's code
"""
import ast
import re
from collections import Counter
from typing import Dict, List, Any

def extract_style_dna(code_files: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Extract Coding DNA from multiple code files
    This is the core innovation - proprietary style extraction algorithm
    """
    all_patterns = {
        'naming': {'snake_case': 0, 'camelCase': 0, 'PascalCase': 0, 'UPPER_CASE': 0},
        'documentation': {'has_docstrings': 0, 'docstring_style': [], 'docstring_length': []},
        'type_hints': {'has_hints': 0, 'hint_style': 'none'},
        'error_handling': {'try_except': 0, 'error_style': [], 'logging_usage': 0},
        'code_structure': {'avg_function_length': [], 'avg_class_length': [], 'function_count': 0, 'class_count': 0},
        'complexity': {'avg_complexity': [], 'max_complexity': 0},
        'consistency': {'naming_consistency': 0, 'style_consistency': 0}
    }
    
    total_files = len(code_files)
    if total_files == 0:
        return build_dna_profile(all_patterns, 0)
    
    for file_data in code_files:
        code = file_data.get('content', '')
        filename = file_data.get('filename', '')
        
        if not code:
            continue
            
        try:
            tree = ast.parse(code)
            file_patterns = analyze_file_patterns(tree, code)
            aggregate_patterns(all_patterns, file_patterns)
        except SyntaxError:
            continue
        except Exception:
            continue
    
    # Calculate weighted averages and consistency scores
    return build_dna_profile(all_patterns, total_files)

def analyze_file_patterns(tree: ast.AST, code: str) -> Dict[str, Any]:
    """Analyze patterns in a single file"""
    patterns = {
        'naming': Counter(),
        'docstrings': [],
        'type_hints': 0,
        'error_handling': [],
        'function_lengths': [],
        'class_lengths': [],
        'functions': 0,
        'classes': 0,
        'logging': False
    }
    
    for node in ast.walk(tree):
        # Analyze functions
        if isinstance(node, ast.FunctionDef):
            patterns['functions'] += 1
            analyze_function(node, patterns, code)
        
        # Analyze classes
        elif isinstance(node, ast.ClassDef):
            patterns['classes'] += 1
            analyze_class(node, patterns)
    
    return patterns

def analyze_function(node: ast.FunctionDef, patterns: Dict, code: str):
    """Analyze a single function for patterns"""
    # Naming style
    name = node.name
    if name.isupper() and '_' in name:
        patterns['naming']['UPPER_CASE'] += 1
    elif '_' in name:
        patterns['naming']['snake_case'] += 1
    elif name[0].isupper():
        patterns['naming']['PascalCase'] += 1
    else:
        patterns['naming']['camelCase'] += 1
    
    # Docstring analysis
    docstring = ast.get_docstring(node)
    if docstring:
        patterns['docstrings'].append({
            'length': len(docstring),
            'style': detect_docstring_style(docstring),
            'has_params': 'param' in docstring.lower() or 'args' in docstring.lower(),
            'has_returns': 'return' in docstring.lower() or 'returns' in docstring.lower()
        })
    
    # Type hints
    if node.returns or any(arg.annotation for arg in node.args.args):
        patterns['type_hints'] += 1
    
    # Function length
    try:
        func_code = ast.get_source_segment(code, node) or ''
        patterns['function_lengths'].append(len(func_code.split('\n')))
    except:
        pass
    
    # Error handling
    for child in ast.walk(node):
        if isinstance(child, ast.Try):
            patterns['error_handling'].append(analyze_error_handling(child, code))
            # Check for logging
            for stmt in child.body:
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                    if isinstance(stmt.value.func, ast.Attribute):
                        try:
                            func_name = ast.unparse(stmt.value.func).lower()
                        except AttributeError:
                            func_name = str(stmt.value.func).lower()
                        if 'log' in func_name:
                            patterns['logging'] = True

def analyze_class(node: ast.ClassDef, patterns: Dict):
    """Analyze a class for patterns"""
    try:
        try:
            class_code = ast.unparse(node)
        except AttributeError:
            class_code = str(node)
        patterns['class_lengths'].append(len(class_code.split('\n')))
    except:
        pass

def analyze_error_handling(try_node: ast.Try, code: str) -> Dict:
    """Analyze error handling patterns"""
    error_style = {
        'has_specific_exceptions': False,
        'has_generic_except': False,
        'has_finally': len(try_node.finalbody) > 0,
        'logs_error': False
    }
    
    for handler in try_node.handlers:
        if handler.type is None:
            error_style['has_generic_except'] = True
        else:
            error_style['has_specific_exceptions'] = True
    
    return error_style

def detect_docstring_style(docstring: str) -> str:
    """Detect docstring style (Google, NumPy, Sphinx, or simple)"""
    doc_lower = docstring.lower()
    
    if 'args:' in doc_lower or 'returns:' in doc_lower or 'raises:' in doc_lower:
        if ':' in docstring and '\n' in docstring:
            return 'google'
    
    if 'parameters' in doc_lower and '----------' in docstring:
        return 'numpy'
    
    if ':param' in doc_lower or ':return:' in doc_lower:
        return 'sphinx'
    
    return 'simple'

def aggregate_patterns(all_patterns: Dict, file_patterns: Dict):
    """Aggregate patterns from a file into overall patterns"""
    # Naming
    for style, count in file_patterns['naming'].items():
        all_patterns['naming'][style] += count
    
    # Documentation
    if file_patterns['docstrings']:
        all_patterns['documentation']['has_docstrings'] += 1
        all_patterns['documentation']['docstring_style'].extend(
            [d['style'] for d in file_patterns['docstrings']]
        )
        all_patterns['documentation']['docstring_length'].extend(
            [d['length'] for d in file_patterns['docstrings']]
        )
    
    # Type hints
    if file_patterns['type_hints'] > 0:
        all_patterns['type_hints']['has_hints'] += 1
    
    # Error handling
    all_patterns['error_handling']['try_except'] += len(file_patterns['error_handling'])
    all_patterns['error_handling']['error_style'].extend(file_patterns['error_handling'])
    if file_patterns['logging']:
        all_patterns['error_handling']['logging_usage'] += 1
    
    # Code structure
    all_patterns['code_structure']['function_count'] += file_patterns['functions']
    all_patterns['code_structure']['class_count'] += file_patterns['classes']
    all_patterns['code_structure']['avg_function_length'].extend(file_patterns['function_lengths'])
    all_patterns['code_structure']['avg_class_length'].extend(file_patterns['class_lengths'])

def build_dna_profile(patterns: Dict, total_files: int) -> Dict[str, Any]:
    """Build the final Style DNA profile"""
    if total_files == 0:
        return {
            'naming_style': 'snake_case',
            'naming_confidence': 0,
            'documentation_score': 0,
            'docstring_style': 'simple',
            'type_hints_usage': 0,
            'error_handling_score': 0,
            'error_handling_style': 'basic',
            'code_quality_score': 50,
            'consistency_score': 0,
            'skill_level': 'beginner',
            'insights': []
        }
    
    # Calculate naming style dominance
    naming = patterns['naming']
    total_naming = sum(naming.values())
    dominant_naming = max(naming.items(), key=lambda x: x[1])[0] if total_naming > 0 else 'snake_case'
    naming_confidence = (naming[dominant_naming] / total_naming * 100) if total_naming > 0 else 0
    
    # Documentation score
    doc_count = patterns['documentation']['has_docstrings']
    doc_score = (doc_count / total_files * 100) if total_files > 0 else 0
    doc_style = Counter(patterns['documentation']['docstring_style']).most_common(1)
    doc_style_name = doc_style[0][0] if doc_style else 'simple'
    
    # Type hints usage
    type_hints_usage = (patterns['type_hints']['has_hints'] / total_files * 100) if total_files > 0 else 0
    
    # Error handling
    error_score = (patterns['error_handling']['try_except'] / total_files * 100) if total_files > 0 else 0
    error_style = 'logging' if patterns['error_handling']['logging_usage'] > 0 else 'basic'
    
    # Code quality score
    quality_score = calculate_quality_score(patterns, total_files)
    
    # Consistency score
    consistency = calculate_consistency(patterns, total_files)
    
    # Skill level
    skill_level = determine_skill_level(quality_score, type_hints_usage, doc_score)
    
    # Insights
    insights = generate_insights(patterns, total_files, quality_score)
    
    return {
        'naming_style': dominant_naming,
        'naming_confidence': round(naming_confidence, 1),
        'documentation_score': round(doc_score, 1),
        'docstring_style': doc_style_name,
        'type_hints_usage': round(type_hints_usage, 1),
        'error_handling_score': round(error_score, 1),
        'error_handling_style': error_style,
        'code_quality_score': round(quality_score, 1),
        'consistency_score': round(consistency, 1),
        'skill_level': skill_level,
        'total_files_analyzed': total_files,
        'total_functions': patterns['code_structure']['function_count'],
        'total_classes': patterns['code_structure']['class_count'],
        'avg_function_length': round(sum(patterns['code_structure']['avg_function_length']) / len(patterns['code_structure']['avg_function_length']), 1) if patterns['code_structure']['avg_function_length'] else 0,
        'insights': insights
    }

def calculate_quality_score(patterns: Dict, total_files: int) -> float:
    """Calculate overall code quality score (0-100)"""
    score = 50  # Base score
    
    # Documentation (max 20 points)
    doc_score = (patterns['documentation']['has_docstrings'] / total_files * 20) if total_files > 0 else 0
    score += doc_score
    
    # Type hints (max 15 points)
    type_score = (patterns['type_hints']['has_hints'] / total_files * 15) if total_files > 0 else 0
    score += type_score
    
    # Error handling (max 15 points)
    error_score = (patterns['error_handling']['try_except'] / total_files * 15) if total_files > 0 else 0
    score += error_score
    
    return max(0, min(100, score))

def calculate_consistency(patterns: Dict, total_files: int) -> float:
    """Calculate style consistency score"""
    if total_files == 0:
        return 0
    
    # Naming consistency
    naming = patterns['naming']
    total_naming = sum(naming.values())
    if total_naming > 0:
        max_naming = max(naming.values())
        naming_consistency = (max_naming / total_naming) * 100
    else:
        naming_consistency = 0
    
    return naming_consistency

def determine_skill_level(quality_score: float, type_hints: float, doc_score: float) -> str:
    """Determine skill level based on patterns"""
    if quality_score >= 80 and type_hints >= 50:
        return 'advanced'
    elif quality_score >= 60 or doc_score >= 50:
        return 'intermediate'
    else:
        return 'beginner'

def generate_insights(patterns: Dict, total_files: int, quality_score: float) -> List[str]:
    """Generate insights about the coding style"""
    insights = []
    
    naming = patterns['naming']
    total_naming = sum(naming.values())
    if total_naming > 0:
        dominant = max(naming.items(), key=lambda x: x[1])
        insights.append(f"You consistently use {dominant[0]} naming ({dominant[1]}/{total_naming} functions)")
    
    doc_score = (patterns['documentation']['has_docstrings'] / total_files * 100) if total_files > 0 else 0
    if doc_score >= 80:
        insights.append("Excellent documentation habits - you document most of your functions")
    elif doc_score < 50:
        insights.append("Consider adding more docstrings to improve code clarity")
    
    type_hints = (patterns['type_hints']['has_hints'] / total_files * 100) if total_files > 0 else 0
    if type_hints < 20:
        insights.append("Type hints could help catch bugs early - ready to learn?")
    
    if patterns['error_handling']['logging_usage'] > 0:
        insights.append("You use logging with error handling - great practice!")
    
    if quality_score >= 75:
        insights.append("Your code quality is excellent - keep it up!")
    elif quality_score < 60:
        insights.append("There's room for improvement - CodeMind can help!")
    
    return insights

