"""
AI Engine using Google Gemini API
"""
import google.generativeai as genai
import json
import re
from typing import Dict


class AIEngine:
    def __init__(self, api_key: str):
        """Initialize Gemini AI"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def suggest_improvement(self, code: str, style_profile: Dict) -> Dict:
        """
        Get AI suggestion that matches user's style
        
        Args:
            code: User's code
            style_profile: User's style profile from analysis
        
        Returns:
            Dict with suggestion, explanation, etc.
        """
        # Build style context
        style_context = self._build_style_context(style_profile)
        
        prompt = f"""You are CodeMind, an AI coding assistant that suggests improvements matching the user's coding style.

{style_context}

USER'S CODE:
```python
{code}
```

Analyze this code and suggest an improvement that MATCHES their style patterns.

Respond with JSON only (no markdown):
{{
  "has_suggestion": true or false,
  "improved_code": "improved code matching their style or null",
  "explanation": "why this is better (2-3 sentences)",
  "confidence": 0.0 to 1.0
}}

CRITICAL RULES:
1. Use {style_profile.get('naming_style', 'snake_case')} naming EXACTLY
2. Match their documentation style ({style_profile.get('documentation_percentage', 0):.0f}% usage)
3. {"Include type hints" if style_profile.get('type_hints_percentage', 0) > 50 else "DO NOT add type hints"}
4. Match their error handling style ({style_profile.get('error_handling_style', 'basic')})
5. Code should feel like THEY wrote it, just improved
6. If code is already good, set has_suggestion to false
"""
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Remove markdown code blocks if present
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            
            result = json.loads(text)
            return result
            
        except Exception as e:
            print(f"AI Error: {e}")
            return {
                'has_suggestion': False,
                'improved_code': None,
                'explanation': 'Unable to generate suggestion',
                'confidence': 0.0
            }
    
    def _build_style_context(self, style_profile: Dict) -> str:
        """Build style context string for prompt"""
        if not style_profile:
            return "No style profile available. Use standard Python conventions."
        
        return f"""USER'S CODING STYLE (Extracted from their code):
- Naming Convention: {style_profile.get('naming_style', 'snake_case')} ({style_profile.get('naming_confidence', 0):.0f}% confidence)
- Documentation: {style_profile.get('documentation_percentage', 0):.0f}% of functions have docstrings
- Type Hints: {style_profile.get('type_hints_percentage', 0):.0f}% usage
- Error Handling: {style_profile.get('error_handling_style', 'basic')} style
- Code Quality: {style_profile.get('code_quality_score', 50)}/100

IMPORTANT: Match their style EXACTLY. If they use {style_profile.get('naming_style', 'snake_case')}, use {style_profile.get('naming_style', 'snake_case')}.
If they rarely use type hints ({style_profile.get('type_hints_percentage', 0):.0f}%), don't add them.
"""
