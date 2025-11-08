"""
Detect coding context based on time, file path, etc.
"""
from datetime import datetime

def detect_context(file_name='untitled.py', time=None):
    """
    Detect coding context
    Returns context mode and indicators
    """
    if time is None:
        time = datetime.now()
    
    context = {
        'mode': 'professional',
        'indicators': [],
        'confidence': 0.8
    }
    
    hour = time.hour
    
    # Time-based detection
    if 22 <= hour or hour <= 6:
        context['mode'] = 'late_night'
        context['indicators'].append('🌙 Late night coding')
        context['confidence'] = 0.9
    
    # File path based detection
    file_lower = file_name.lower()
    
    if 'test' in file_lower or 'demo' in file_lower:
        context['mode'] = 'experimental'
        context['indicators'].append('🧪 Test/Demo file')
    elif 'prototype' in file_lower or 'draft' in file_lower:
        context['mode'] = 'experimental'
        context['indicators'].append('🚧 Prototype mode')
    elif 'client' in file_lower or 'prod' in file_lower:
        context['mode'] = 'professional'
        context['indicators'].append('💼 Production code')
    elif 'personal' in file_lower or 'practice' in file_lower:
        context['mode'] = 'personal'
        context['indicators'].append('🏠 Personal project')
    
    return context

def get_context_suggestions(mode):
    """Get suggestion style based on context"""
    styles = {
        'professional': {
            'verbosity': 'detailed',
            'documentation': 'comprehensive',
            'error_handling': 'robust'
        },
        'experimental': {
            'verbosity': 'concise',
            'documentation': 'minimal',
            'error_handling': 'basic'
        },
        'late_night': {
            'verbosity': 'clear',
            'documentation': 'helpful',
            'error_handling': 'extra_careful'
        },
        'personal': {
            'verbosity': 'flexible',
            'documentation': 'optional',
            'error_handling': 'moderate'
        }
    }
    return styles.get(mode, styles['professional'])

