"""
Context Detection for CodeMind
Detects what the user is working on to provide context-aware suggestions
"""
import re
from typing import Dict


def detect_context(filename: str, code: str) -> Dict:
    """
    Detect what user is working on based on filename and code content
    
    Args:
        filename: Name of the file
        code: Code content
    
    Returns:
        Dict with context type and indicators
    """
    context = {
        'type': 'general',
        'indicators': [],
        'confidence': 0.0
    }
    
    filename_lower = filename.lower()
    code_lower = code.lower()
    
    # File name based detection
    if any(keyword in filename_lower for keyword in ['test', 'spec', 'specs']):
        context['type'] = 'testing'
        context['indicators'].append('Test file detected')
        context['confidence'] += 0.4
    
    if any(keyword in filename_lower for keyword in ['api', 'route', 'endpoint', 'controller']):
        context['type'] = 'api'
        context['indicators'].append('API/Routes file')
        context['confidence'] += 0.4
    
    if any(keyword in filename_lower for keyword in ['model', 'schema', 'db']):
        context['type'] = 'database'
        context['indicators'].append('Database model file')
        context['confidence'] += 0.4
    
    if any(keyword in filename_lower for keyword in ['util', 'helper', 'utils']):
        context['type'] = 'utility'
        context['indicators'].append('Utility functions')
        context['confidence'] += 0.3
    
    if any(keyword in filename_lower for keyword in ['config', 'settings']):
        context['type'] = 'configuration'
        context['indicators'].append('Configuration file')
        context['confidence'] += 0.3
    
    # Code content based detection
    if 'class ' in code and '__init__' in code:
        context['type'] = 'class'
        context['indicators'].append('Class definition')
        context['confidence'] += 0.3
    
    if re.search(r'import\s+(pytest|unittest|nose)', code_lower):
        context['type'] = 'testing'
        context['indicators'].append('Test framework imported')
        context['confidence'] += 0.3
    
    if re.search(r'@app\.(route|get|post|put|delete)', code_lower):
        context['type'] = 'api'
        context['indicators'].append('Flask/API routes detected')
        context['confidence'] += 0.4
    
    if re.search(r'(def\s+test_|def\s+test[A-Z])', code):
        context['type'] = 'testing'
        context['indicators'].append('Test functions found')
        context['confidence'] += 0.3
    
    if 'SQLAlchemy' in code or 'db.Model' in code:
        context['type'] = 'database'
        context['indicators'].append('ORM detected')
        context['confidence'] += 0.3
    
    if 'async def' in code or 'await ' in code:
        context['type'] = 'async'
        context['indicators'].append('Async code detected')
        context['confidence'] += 0.2
    
    # Normalize confidence
    context['confidence'] = min(context['confidence'], 1.0)
    
    # If no strong indicators, keep as general
    if context['confidence'] < 0.3:
        context['type'] = 'general'
        context['indicators'] = ['General Python code']
    
    return context


def get_context_specific_prompt(context: Dict) -> str:
    """
    Get AI prompt adjustments based on context
    
    Args:
        context: Context dict from detect_context
    
    Returns:
        Context-specific prompt string
    """
    prompts = {
        'testing': "Focus on test clarity, descriptive test names, and clear assertion messages. Suggest proper test organization and fixtures.",
        'api': "Prioritize error handling, input validation, proper HTTP status codes, and clear response formats. Suggest security best practices.",
        'database': "Focus on efficient queries, proper indexing, data validation, and relationship handling. Suggest performance optimizations.",
        'class': "Suggest proper encapsulation, method organization, and design patterns. Focus on single responsibility and clear interfaces.",
        'utility': "Focus on reusability, clear function signatures, and comprehensive error handling. Suggest documentation for helper functions.",
        'configuration': "Focus on clear structure, validation, and environment-specific settings. Suggest secure configuration practices.",
        'async': "Focus on proper async/await usage, error handling in async contexts, and avoiding blocking operations.",
        'general': "Focus on code clarity, maintainability, and following best practices."
    }
    
    base_prompt = prompts.get(context['type'], prompts['general'])
    
    if context['indicators']:
        base_prompt += f"\n\nDetected indicators: {', '.join(context['indicators'])}"
    
    return base_prompt
