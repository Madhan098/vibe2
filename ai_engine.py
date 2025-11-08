"""
AI Engine using Groq API
"""
from groq import Groq
import json
import re
from typing import Dict
from context_detector import detect_context, get_context_specific_prompt


class AIEngine:
    def __init__(self, api_key: str):
        """Initialize Groq AI"""
        self.client = Groq(api_key=api_key)
        # Groq models: llama-3.1-8b-instant (fast), llama-3.1-70b-versatile (powerful), mixtral-8x7b-32768
        self.model = "llama-3.1-8b-instant"  # Fast and efficient model (replacement for decommissioned llama3-8b-8192)
        print(f"✅ Using Groq model: {self.model}")
    
    def suggest_improvement(self, code: str, style_profile: Dict, filename: str = 'untitled.py') -> Dict:
        """
        Get AI suggestion that matches user's style
        
        Args:
            code: User's code
            style_profile: User's style profile from analysis
            filename: Name of the file (for context detection)
        
        Returns:
            Dict with suggestion, explanation, etc.
        """
        # Detect context
        context = detect_context(filename, code)
        context_prompt = get_context_specific_prompt(context)
        
        # Build style context
        style_context = self._build_style_context(style_profile)
        
        prompt = f"""You are CodeMind, an AI coding assistant that suggests improvements matching the user's coding style.

{style_context}

CONTEXT DETECTION:
Type: {context['type']}
Indicators: {', '.join(context['indicators'])}

{context_prompt}

USER'S CODE:
```python
{code}
```

Analyze this code and suggest an improvement that MATCHES their style patterns and fits the detected context.

Respond with JSON only (no markdown):
{{
  "has_suggestion": true or false,
  "improved_code": "improved code matching their style or null",
  "explanation": "why this is better (2-3 sentences)",
  "teaching": {{
    "what": "what the improvement does",
    "why": "why it's better",
    "when_to_use": "when to use this pattern",
    "tips": "helpful tips"
  }},
  "confidence": 0.0 to 1.0,
  "context": "{context['type']}"
}}

CRITICAL RULES:
1. Use {style_profile.get('naming_style', 'snake_case')} naming EXACTLY
2. Match their documentation style ({style_profile.get('documentation_percentage', 0):.0f}% usage)
3. {"Include type hints" if style_profile.get('type_hints_percentage', 0) > 50 else "DO NOT add type hints"}
4. Match their error handling style ({style_profile.get('error_handling_style', 'basic')})
5. Code should feel like THEY wrote it, just improved
6. Consider the context ({context['type']}) when making suggestions
7. If code is already good, set has_suggestion to false
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2048
            )
            
            text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            
            result = json.loads(text)
            return result
            
        except Exception as e:
            print(f"AI Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'has_suggestion': False,
                'improved_code': None,
                'explanation': 'Unable to generate suggestion',
                'confidence': 0.0
            }
    
    def generate_teaching_moment(self, code: str, style_profile: Dict, suggestion: str = None) -> Dict:
        """
        Generate educational content about the suggestion
        
        Args:
            code: Original code
            style_profile: User's style profile
            suggestion: Suggested improvement (optional)
        
        Returns:
            Dict with teaching content
        """
        prompt = f"""You're a coding mentor. Explain this improvement in simple, friendly terms.

USER'S STYLE: {style_profile}
ORIGINAL CODE: {code}
{"SUGGESTED IMPROVEMENT: " + suggestion if suggestion else ""}

Generate a teaching moment:
1. What the improvement does (simple explanation)
2. Why it's better
3. When to use this pattern
4. Common mistakes to avoid

Keep it friendly, encouraging, and concise (3-4 sentences max per section).

Format as JSON:
{{
  "what": "brief explanation of what changed",
  "why": "why this is better",
  "when_to_use": "when to use this pattern",
  "tips": "helpful tips and common mistakes to avoid"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1024
            )
            
            text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            
            result = json.loads(text)
            return result
        except Exception as e:
            print(f"Teaching moment generation error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'what': 'Code improvement',
                'why': 'Makes code more maintainable',
                'when_to_use': 'In similar situations',
                'tips': 'Keep practicing!'
            }
    
    def generate_code(self, user_request: str, style_profile: Dict, preferred_language: str = None, template: str = None, tech_stack: str = None) -> Dict:
        """
        Generate code based on user request matching their style
        
        Args:
            user_request: What the user wants (e.g., "Create a function to calculate factorial")
            style_profile: User's style profile from analysis
        
        Returns:
            Dict with generated code, explanation, etc.
        """
        # Build style context
        style_context = self._build_style_context(style_profile)
        
        # Detect language from request or use preferred language
        detected_language = preferred_language or self._detect_language_from_request(user_request)
        primary_language = style_profile.get('primary_language', detected_language or 'Python')
        
        # Get language-specific patterns
        languages_used = style_profile.get('languages_detected', [primary_language])
        all_patterns = style_profile.get('all_patterns', {})
        lang_patterns = all_patterns.get(primary_language, {})
        
        # Build enhanced request with template and tech stack
        enhanced_request = user_request
        if template:
            template_context = {
                'web-app': 'a complete modern web application with HTML, CSS, and JavaScript',
                'flask-app': 'a complete Flask web application with routes, templates, and proper structure',
                'static-site': 'a complete static website with HTML, CSS, and JavaScript files',
                'rest-api': 'a complete REST API with multiple endpoints, proper error handling, and documentation',
                'cli-tool': 'a complete command-line tool with argument parsing and proper structure',
                'data-analysis': 'a complete data analysis script with data loading, processing, and visualization'
            }
            enhanced_request = f"{template_context.get(template, template)}: {user_request}"
        
        if tech_stack:
            enhanced_request += f" using {tech_stack}"
        
        # Determine if multi-file generation is needed
        is_multi_file = template in ['web-app', 'flask-app', 'static-site', 'rest-api'] or 'multiple files' in user_request.lower() or 'project' in user_request.lower()
        
        if is_multi_file:
            prompt = f"""You are CodeMind, an AI coding assistant that writes code matching the user's unique coding style.

{style_context}

LANGUAGES USER USES: {', '.join(languages_used) if languages_used else 'Python'}
PRIMARY LANGUAGE: {primary_language}
LANGUAGE PATTERNS: {lang_patterns if lang_patterns else 'Standard patterns'}

USER REQUEST:
"{enhanced_request}"

Generate a complete {primary_language} project with MULTIPLE FILES that:
1. Fulfills the user's request completely
2. MATCHES their coding style EXACTLY (naming, documentation, error handling)
3. Is production-ready and well-structured
4. Follows their patterns and conventions
5. Uses the {primary_language} language and its best practices
6. Includes all necessary files (main files, config files, etc.)

Respond with JSON only (no markdown):
{{
  "files": [
    {{
      "filename": "main.py",
      "code": "complete code for this file matching their style"
    }},
    {{
      "filename": "config.py",
      "code": "complete code for this file matching their style"
    }}
  ],
  "explanation": "brief explanation of the project structure (2-3 sentences)",
  "language": "{primary_language}",
  "confidence": 0.0 to 1.0
}}

CRITICAL RULES:
1. Use {style_profile.get('naming_style', 'snake_case' if primary_language == 'Python' else 'camelCase')} naming EXACTLY in ALL files
2. {"Include type hints" if style_profile.get('type_hints_percentage', 0) > 50 and primary_language == 'Python' else "Match their documentation style"}
3. {"Add docstrings/comments" if style_profile.get('documentation_percentage', 0) > 50 else "Minimal documentation"}
4. Use {style_profile.get('error_handling_style', 'basic')} error handling style consistently
5. ALL code should look like THEY wrote it in {primary_language}
6. Make it complete and functional with proper file structure
7. Use {primary_language} best practices and idioms
8. Generate 2-5 files as needed for a complete project
"""
        else:
            prompt = f"""You are CodeMind, an AI coding assistant that writes code matching the user's unique coding style.

{style_context}

LANGUAGES USER USES: {', '.join(languages_used) if languages_used else 'Python'}
PRIMARY LANGUAGE: {primary_language}
LANGUAGE PATTERNS: {lang_patterns if lang_patterns else 'Standard patterns'}

USER REQUEST:
"{enhanced_request}"

Generate {primary_language} code that:
1. Fulfills the user's request completely
2. MATCHES their coding style EXACTLY (naming, documentation, error handling)
3. Is production-ready and well-structured
4. Follows their patterns and conventions
5. Uses the {primary_language} language and its best practices

Respond with JSON only (no markdown):
{{
  "code": "complete {primary_language} code matching their style",
  "explanation": "brief explanation of what the code does (2-3 sentences)",
  "language": "{primary_language}",
  "confidence": 0.0 to 1.0
}}

CRITICAL RULES:
1. Use {style_profile.get('naming_style', 'snake_case' if primary_language == 'Python' else 'camelCase')} naming EXACTLY
2. {"Include type hints" if style_profile.get('type_hints_percentage', 0) > 50 and primary_language == 'Python' else "Match their documentation style"}
3. {"Add docstrings/comments" if style_profile.get('documentation_percentage', 0) > 50 else "Minimal documentation"}
4. Use {style_profile.get('error_handling_style', 'basic')} error handling style
5. Code should look like THEY wrote it in {primary_language}
6. Make it complete and functional
7. Use {primary_language} best practices and idioms
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4096
            )
            
            if not response or not response.choices or len(response.choices) == 0:
                print("AI Generation Error: No response or invalid response")
                return {
                    'code': None,
                    'files': None,
                    'explanation': 'AI service returned an invalid response. Please try again.',
                    'confidence': 0.0
                }
            
            text = response.choices[0].message.content.strip()
            
            if not text:
                print("AI Generation Error: Empty response")
                return {
                    'code': None,
                    'files': None,
                    'explanation': 'AI service returned an empty response. Please try again.',
                    'confidence': 0.0
                }
            
            # Remove markdown code blocks if present
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            text = text.strip()
            
            # Try to parse JSON
            try:
                result = json.loads(text)
            except json.JSONDecodeError as json_err:
                print(f"JSON Parse Error: {json_err}")
                print(f"Response text (first 1000 chars): {text[:1000]}")
                
                # Try to fix common JSON issues
                # 1. Try to extract JSON from the response if it's wrapped in other text
                json_match = re.search(r'\{[\s\S]*\}', text)
                if json_match:
                    try:
                        fixed_json = json_match.group(0)
                        result = json.loads(fixed_json)
                        print("✅ Successfully parsed JSON after extraction")
                    except:
                        pass
                
                # 2. If still failing, try to extract code directly from response
                if 'result' not in locals() or not result:
                    # Try to extract code from JSON-like structure even if invalid
                    code_match = re.search(r'"code"\s*:\s*"""([\s\S]*?)"""', text)
                    if not code_match:
                        code_match = re.search(r'"code"\s*:\s*"([\s\S]*?)"', text)
                    if not code_match:
                        # Try markdown code blocks
                        code_match = re.search(r'```(?:python|javascript|typescript|java|html|css)?\s*\n(.*?)```', text, re.DOTALL)
                    
                    if code_match:
                        extracted_code = code_match.group(1).strip()
                        # Try to extract explanation too
                        explanation_match = re.search(r'"explanation"\s*:\s*"([^"]*)"', text)
                        explanation = explanation_match.group(1) if explanation_match else 'Code generated (parsed from response)'
                        
                        return {
                            'code': extracted_code,
                            'explanation': explanation,
                            'confidence': 0.7
                        }
                
                # 3. Last resort: return error
                if 'result' not in locals() or not result:
                    return {
                        'code': None,
                        'files': None,
                        'explanation': 'Unable to parse AI response. The response may be incomplete or malformed.',
                        'confidence': 0.0
                    }
            
            return result
            
        except Exception as e:
            print(f"AI Generation Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'code': None,
                'files': None,
                'explanation': f'Error generating code: {str(e)}. Please try again.',
                'confidence': 0.0
            }
    
    def _detect_language_from_request(self, request: str) -> str:
        """Detect programming language from user request"""
        request_lower = request.lower()
        
        language_keywords = {
            'Python': ['python', 'py', 'django', 'flask', 'pandas', 'numpy'],
            'JavaScript': ['javascript', 'js', 'node', 'react', 'vue', 'angular'],
            'TypeScript': ['typescript', 'ts', 'tsx'],
            'Java': ['java', 'spring', 'maven'],
            'C++': ['c++', 'cpp', 'cplusplus'],
            'C#': ['c#', 'csharp', '.net'],
            'Go': ['go', 'golang'],
            'Rust': ['rust'],
            'Ruby': ['ruby', 'rails'],
            'PHP': ['php', 'laravel'],
            'Swift': ['swift', 'ios'],
            'Kotlin': ['kotlin', 'android']
        }
        
        for lang, keywords in language_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                return lang
        
        return 'Python'  # Default
    
    def _build_style_context(self, style_profile: Dict) -> str:
        """Build style context string for prompt"""
        if not style_profile:
            return "No style profile available. Use standard conventions."
        
        languages = style_profile.get('languages_detected', [])
        primary_lang = style_profile.get('primary_language', 'Python')
        
        context = f"""USER'S CODING STYLE (Extracted from their code):
- Languages Used: {', '.join(languages) if languages else primary_lang}
- Primary Language: {primary_lang}
- Naming Convention: {style_profile.get('naming_style', 'snake_case' if primary_lang == 'Python' else 'camelCase')}
- Documentation: {style_profile.get('documentation_percentage', 0):.0f}% coverage
- Error Handling: {style_profile.get('error_handling_style', 'basic')} style
- Code Quality: {style_profile.get('code_quality_score', 50)}/100
"""
        
        # Add language-specific patterns
        all_patterns = style_profile.get('all_patterns', {})
        if all_patterns:
            context += "\nLanguage-Specific Patterns:\n"
            for lang, patterns in list(all_patterns.items())[:3]:  # Top 3 languages
                context += f"- {lang}: {patterns}\n"
        
        return context
