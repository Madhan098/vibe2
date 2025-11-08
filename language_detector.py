"""
Language Detection for CodeMind
Detects programming languages from file extensions and content
"""
from typing import Dict, List, Tuple
import re


# Language definitions with file extensions
LANGUAGE_EXTENSIONS = {
    'Python': ['.py', '.pyw', '.pyx'],
    'JavaScript': ['.js', '.jsx', '.mjs'],
    'TypeScript': ['.ts', '.tsx'],
    'Java': ['.java'],
    'C': ['.c', '.h'],
    'C++': ['.cpp', '.cc', '.cxx', '.hpp', '.hxx'],
    'C#': ['.cs'],
    'Go': ['.go'],
    'Rust': ['.rs'],
    'Ruby': ['.rb'],
    'PHP': ['.php'],
    'Swift': ['.swift'],
    'Kotlin': ['.kt', '.kts'],
    'Scala': ['.scala'],
    'R': ['.r'],
    'MATLAB': ['.m'],
    'Shell': ['.sh', '.bash', '.zsh'],
    'HTML': ['.html', '.htm'],
    'CSS': ['.css', '.scss', '.sass', '.less'],
    'Vue': ['.vue'],
    'Svelte': ['.svelte'],
    'Dart': ['.dart'],
    'Lua': ['.lua'],
    'Perl': ['.pl', '.pm'],
    'SQL': ['.sql']
}


def get_language_from_extension(extension: str) -> str:
    """
    Get programming language from file extension
    
    Args:
        extension: File extension (e.g., '.py', '.js')
    
    Returns:
        Language name or 'Unknown'
    """
    extension = extension.lower()
    for language, extensions in LANGUAGE_EXTENSIONS.items():
        if extension in extensions:
            return language
    return 'Unknown'


def detect_language_from_content(filename: str, content: str) -> str:
    """
    Detect programming language from file content (fallback)
    
    Args:
        filename: File name
        content: File content
    
    Returns:
        Detected language
    """
    # First try extension
    if '.' in filename:
        ext = '.' + filename.split('.')[-1].lower()
        lang = get_language_from_extension(ext)
        if lang != 'Unknown':
            return lang
    
    # Fallback to content-based detection
    content_lower = content[:500].lower()  # Check first 500 chars
    
    # Python indicators
    if re.search(r'\b(import|from|def|class|if __name__)', content_lower):
        if '#!/usr/bin/env python' in content_lower or '#!/usr/bin/python' in content_lower:
            return 'Python'
    
    # JavaScript indicators
    if re.search(r'\b(function|const|let|var|=>|require\(|import\s)', content_lower):
        return 'JavaScript'
    
    # Java indicators
    if re.search(r'\b(public\s+class|import\s+java\.|package\s+)', content_lower):
        return 'Java'
    
    # C/C++ indicators
    if re.search(r'#include\s*[<"]', content_lower):
        return 'C++' if 'namespace' in content_lower or 'std::' in content_lower else 'C'
    
    # HTML indicators
    if re.search(r'<!DOCTYPE\s+html|<html|<head>', content_lower):
        return 'HTML'
    
    # CSS indicators
    if re.search(r'@(media|import|keyframes)|^\s*[.#][\w-]+\s*\{', content):
        return 'CSS'
    
    return 'Unknown'


def analyze_multi_language_files(files: List[Dict[str, str]]) -> Dict:
    """
    Analyze files across multiple programming languages
    
    Args:
        files: List of dicts with 'filename', 'content', and optionally 'language'
    
    Returns:
        Dict with analysis per language and overall patterns
    """
    # Group files by language
    files_by_language = {}
    language_stats = {}
    
    for file_data in files:
        filename = file_data.get('filename', '')
        content = file_data.get('content', '')
        
        # Detect language
        language = file_data.get('language')
        if not language or language == 'Unknown':
            language = detect_language_from_content(filename, content)
        
        if language not in files_by_language:
            files_by_language[language] = []
            language_stats[language] = {
                'file_count': 0,
                'total_lines': 0,
                'total_size': 0
            }
        
        files_by_language[language].append(file_data)
        language_stats[language]['file_count'] += 1
        language_stats[language]['total_lines'] += len(content.split('\n'))
        language_stats[language]['total_size'] += len(content)
    
    return {
        'files_by_language': files_by_language,
        'language_stats': language_stats,
        'total_languages': len(files_by_language),
        'primary_language': max(language_stats.items(), key=lambda x: x[1]['file_count'])[0] if language_stats else 'Unknown'
    }

