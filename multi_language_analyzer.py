"""
Multi-Language Code Analyzer
Analyzes coding patterns across different programming languages
"""
import re
from typing import Dict, List
from language_detector import get_language_from_extension, detect_language_from_content, analyze_multi_language_files


def analyze_python_patterns(code: str) -> Dict:
    """Analyze Python-specific patterns"""
    import ast
    try:
        tree = ast.parse(code)
        patterns = {
            'naming_style': detect_naming_style_python(tree),
            'docstrings': count_docstrings_python(tree),
            'type_hints': count_type_hints_python(tree),
            'error_handling': count_error_handling_python(tree),
            'imports_style': detect_imports_style_python(code)
        }
        return patterns
    except:
        return {}


def analyze_javascript_patterns(code: str) -> Dict:
    """Analyze JavaScript/TypeScript patterns"""
    patterns = {
        'naming_style': detect_naming_style_js(code),
        'function_style': detect_function_style_js(code),
        'error_handling': count_error_handling_js(code),
        'async_patterns': count_async_patterns_js(code),
        'module_system': detect_module_system_js(code)
    }
    return patterns


def analyze_java_patterns(code: str) -> Dict:
    """Analyze Java patterns"""
    patterns = {
        'naming_style': detect_naming_style_java(code),
        'access_modifiers': count_access_modifiers_java(code),
        'error_handling': count_error_handling_java(code),
        'documentation': count_javadoc_java(code)
    }
    return patterns


def analyze_all_languages(files: List[Dict[str, str]]) -> Dict:
    """
    Analyze coding patterns across all languages
    
    Args:
        files: List of dicts with 'filename', 'content', and 'language'
    
    Returns:
        Comprehensive analysis report
    """
    # Ensure files have language detected
    for file_data in files:
        if 'language' not in file_data or file_data.get('language') == 'Unknown':
            filename = file_data.get('filename', '')
            content = file_data.get('content', '')
            file_data['language'] = detect_language_from_content(filename, content)
    
    # Check if all files are Python (use Python analyzer)
    python_count = sum(1 for f in files if f.get('language') == 'Python')
    if python_count == len(files) and len(files) > 0:
        # All Python - use Python analyzer but add language info
        try:
            from code_analyzer import analyze_code_files
            report = analyze_code_files(files)
            report['languages_detected'] = ['Python']
            report['primary_language'] = 'Python'
            report['language_distribution'] = {'Python': {'file_count': len(files)}}
            report['all_patterns'] = {'Python': {
                'naming_style': report.get('naming_style'),
                'documentation_percentage': report.get('documentation_percentage'),
                'type_hints_percentage': report.get('type_hints_percentage'),
                'error_handling_style': report.get('error_handling_style')
            }}
            return report
        except:
            pass  # Fall through to multi-language analysis
    
    # Group by language
    lang_analysis = analyze_multi_language_files(files)
    
    all_patterns = {
        'languages_used': list(lang_analysis['files_by_language'].keys()),
        'language_stats': lang_analysis['language_stats'],
        'primary_language': lang_analysis['primary_language'],
        'patterns_by_language': {},
        'files_analyzed': files
    }
    
    # Analyze each language
    for language, lang_files in lang_analysis['files_by_language'].items():
        patterns = {}
        
        if language == 'Python':
            # Use Python AST analyzer for better accuracy
            try:
                from code_analyzer import analyze_code_files
                python_report = analyze_code_files(lang_files[:10])
                patterns = {
                    'naming_style': python_report.get('naming_style', 'snake_case'),
                    'documentation_percentage': python_report.get('documentation_percentage', 0),
                    'type_hints_percentage': python_report.get('type_hints_percentage', 0),
                    'error_handling_style': python_report.get('error_handling_style', 'basic'),
                    'code_quality': python_report.get('code_quality_score', 50)
                }
            except:
                # Fallback to pattern-based analysis
                for file_data in lang_files[:10]:
                    file_patterns = analyze_python_patterns(file_data.get('content', ''))
                    patterns = merge_patterns(patterns, file_patterns)
        
        elif language in ['JavaScript', 'TypeScript']:
            for file_data in lang_files[:10]:
                file_patterns = analyze_javascript_patterns(file_data.get('content', ''))
                patterns = merge_patterns(patterns, file_patterns)
        
        elif language == 'Java':
            for file_data in lang_files[:10]:
                file_patterns = analyze_java_patterns(file_data.get('content', ''))
                patterns = merge_patterns(patterns, file_patterns)
        
        else:
            # Generic analysis for other languages
            patterns = analyze_generic_patterns(lang_files)
        
        all_patterns['patterns_by_language'][language] = patterns
    
    # Generate overall report
    return generate_multi_language_report(all_patterns)


# Helper functions for pattern detection

def detect_naming_style_python(tree) -> str:
    """Detect Python naming style"""
    import ast
    snake_case = 0
    camel_case = 0
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.Name)):
            name = node.name if hasattr(node, 'name') else ''
            if '_' in name:
                snake_case += 1
            elif name and name[0].islower():
                camel_case += 1
    
    return 'snake_case' if snake_case > camel_case else 'camelCase'


def detect_naming_style_js(code: str) -> str:
    """Detect JavaScript naming style"""
    camel_case = len(re.findall(r'\b[a-z][a-zA-Z0-9]+\s*[:=]', code))
    snake_case = len(re.findall(r'\b[a-z_]+[a-z0-9_]*\s*[:=]', code))
    
    return 'camelCase' if camel_case > snake_case else 'snake_case'


def detect_naming_style_java(code: str) -> str:
    """Java uses camelCase by convention"""
    return 'camelCase'


def count_docstrings_python(tree) -> Dict:
    """Count Python docstrings"""
    import ast
    functions = 0
    with_docs = 0
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions += 1
            if ast.get_docstring(node):
                with_docs += 1
    
    return {
        'total_functions': functions,
        'with_docstrings': with_docs,
        'percentage': (with_docs / functions * 100) if functions > 0 else 0
    }


def count_type_hints_python(tree) -> Dict:
    """Count Python type hints"""
    import ast
    functions = 0
    with_hints = 0
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions += 1
            if node.returns or any(arg.annotation for arg in node.args.args):
                with_hints += 1
    
    return {
        'total_functions': functions,
        'with_hints': with_hints,
        'percentage': (with_hints / functions * 100) if functions > 0 else 0
    }


def count_error_handling_python(tree) -> Dict:
    """Count Python error handling"""
    import ast
    try_blocks = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Try))
    return {'try_except_count': try_blocks, 'style': 'try_except' if try_blocks > 0 else 'basic'}


def count_error_handling_js(code: str) -> Dict:
    """Count JavaScript error handling"""
    try_blocks = len(re.findall(r'\btry\s*\{', code))
    promises = len(re.findall(r'\.catch\s*\(|\.then\s*\(', code))
    return {'try_catch_count': try_blocks, 'promise_count': promises}


def count_error_handling_java(code: str) -> Dict:
    """Count Java error handling"""
    try_blocks = len(re.findall(r'\btry\s*\{', code))
    return {'try_catch_count': try_blocks}


def detect_function_style_js(code: str) -> Dict:
    """Detect JavaScript function styles"""
    arrow_functions = len(re.findall(r'=>\s*\{|=>\s*[^{]', code))
    function_keyword = len(re.findall(r'\bfunction\s+', code))
    return {
        'arrow_functions': arrow_functions,
        'function_keyword': function_keyword,
        'preferred_style': 'arrow' if arrow_functions > function_keyword else 'function'
    }


def detect_imports_style_python(code: str) -> str:
    """Detect Python import style"""
    if re.search(r'from\s+\w+\s+import', code):
        return 'from_import'
    elif re.search(r'import\s+\w+', code):
        return 'direct_import'
    return 'mixed'


def detect_module_system_js(code: str) -> str:
    """Detect JavaScript module system"""
    if re.search(r'require\s*\(', code):
        return 'CommonJS'
    elif re.search(r'import\s+.*from|export\s+', code):
        return 'ES6'
    return 'unknown'


def count_access_modifiers_java(code: str) -> Dict:
    """Count Java access modifiers"""
    public = len(re.findall(r'\bpublic\s+', code))
    private = len(re.findall(r'\bprivate\s+', code))
    protected = len(re.findall(r'\bprotected\s+', code))
    return {'public': public, 'private': private, 'protected': protected}


def count_javadoc_java(code: str) -> int:
    """Count JavaDoc comments"""
    return len(re.findall(r'/\*\*[\s\S]*?\*/', code))


def count_async_patterns_js(code: str) -> Dict:
    """Count async patterns in JavaScript"""
    async_functions = len(re.findall(r'\basync\s+function|\basync\s*\(', code))
    await_usage = len(re.findall(r'\bawait\s+', code))
    return {'async_functions': async_functions, 'await_usage': await_usage}


def analyze_generic_patterns(files: List[Dict[str, str]]) -> Dict:
    """Generic pattern analysis for any language"""
    total_files = len(files)
    total_lines = sum(len(f.get('content', '').split('\n')) for f in files)
    
    return {
        'total_files': total_files,
        'total_lines': total_lines,
        'avg_file_size': total_lines / total_files if total_files > 0 else 0
    }


def merge_patterns(base: Dict, new: Dict) -> Dict:
    """Merge pattern dictionaries"""
    result = base.copy()
    for key, value in new.items():
        if key in result:
            if isinstance(value, dict) and isinstance(result[key], dict):
                result[key] = merge_patterns(result[key], value)
            elif isinstance(value, (int, float)) and isinstance(result[key], (int, float)):
                result[key] = result[key] + value
        else:
            result[key] = value
    return result


def generate_multi_language_report(patterns: Dict) -> Dict:
    """Generate comprehensive multi-language report"""
    languages = patterns['languages_used']
    primary_lang = patterns['primary_language']
    
    # Get primary language patterns
    primary_patterns = patterns['patterns_by_language'].get(primary_lang, {})
    
    # Extract naming style (handle different pattern structures)
    naming_style = 'mixed'
    if isinstance(primary_patterns, dict):
        naming_style = primary_patterns.get('naming_style', 'mixed')
        if not naming_style or naming_style == 'mixed':
            # Try to infer from language
            if primary_lang == 'Python':
                naming_style = 'snake_case'
            elif primary_lang in ['Java', 'JavaScript', 'TypeScript', 'C++', 'C#']:
                naming_style = 'camelCase'
    
    # Extract documentation percentage
    doc_percentage = 0
    if isinstance(primary_patterns, dict):
        if 'documentation_percentage' in primary_patterns:
            doc_percentage = primary_patterns['documentation_percentage']
        elif 'docstrings' in primary_patterns and isinstance(primary_patterns['docstrings'], dict):
            doc_percentage = primary_patterns['docstrings'].get('percentage', 0)
    
    # Extract error handling style
    error_style = 'basic'
    if isinstance(primary_patterns, dict):
        if 'error_handling_style' in primary_patterns:
            error_style = primary_patterns['error_handling_style']
        elif 'error_handling' in primary_patterns and isinstance(primary_patterns['error_handling'], dict):
            error_style = primary_patterns['error_handling'].get('style', 'basic')
    
    # Build report (consistent with Python analyzer format)
    report = {
        'languages_detected': languages,
        'primary_language': primary_lang,
        'total_languages': len(languages),
        'language_distribution': patterns['language_stats'],
        'primary_language_patterns': primary_patterns,
        'all_patterns': patterns['patterns_by_language'],
        # Overall metrics (from primary language) - consistent format
        'naming_style': naming_style,
        'naming_confidence': 85.0,  # Default confidence for detected style
        'documentation_percentage': round(doc_percentage, 1),
        'type_hints_percentage': primary_patterns.get('type_hints_percentage', 0) if isinstance(primary_patterns, dict) else 0,
        'error_handling_style': error_style,
        'code_quality_score': calculate_overall_quality(patterns),
        'total_functions': sum(stats.get('file_count', 0) for stats in patterns['language_stats'].values()),
        'total_files': len(patterns.get('files_analyzed', []))
    }
    
    return report


def calculate_overall_quality(patterns: Dict) -> int:
    """Calculate overall code quality score"""
    score = 50  # Base score
    
    # Bonus for multiple languages (shows versatility)
    lang_count = len(patterns['languages_used'])
    score += min(lang_count * 5, 20)  # Up to 20 points
    
    # Check primary language patterns
    primary_lang = patterns['primary_language']
    primary_patterns = patterns['patterns_by_language'].get(primary_lang, {})
    
    # Documentation bonus
    if 'docstrings' in primary_patterns:
        doc_pct = primary_patterns['docstrings'].get('percentage', 0)
        score += (doc_pct / 100) * 15
    
    # Error handling bonus
    if 'error_handling' in primary_patterns:
        error_style = primary_patterns['error_handling']
        if isinstance(error_style, dict) and error_style.get('style') != 'basic':
            score += 10
    
    return min(100, max(0, int(score)))

