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
        # Groq models (updated 2025):
        # - llama-3.1-8b-instant (fast, 8192 tokens) - good for simple code
        # - llama-3.1-70b-versatile (powerful, 8192 tokens) - reliable for complex code
        # - llama-3.3-70b-versatile (newer, 8192 tokens) - may not be available yet
        # - mixtral-8x7b-32768 (decommissioned - no longer available)
        # Using llama-3.1-70b-versatile as primary model (proven reliable)
        # Fallback to llama-3.1-8b-instant if 70b is not available
        self.model = "llama-3.1-70b-versatile"
        self.fallback_model = "llama-3.1-8b-instant"
        self.instant_model = "llama-3.1-8b-instant"
        print(f"✅ Using Groq model: {self.model} (supports up to 8,192 tokens)")
    
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
            # Try primary model first, fallback if it fails
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2048
                )
            except Exception as e:
                # If primary model fails (e.g., decommissioned), try fallback
                if "model" in str(e).lower() or "decommissioned" in str(e).lower() or "400" in str(e):
                    print(f"⚠️ Primary model {self.model} failed, trying fallback {self.fallback_model}")
                    response = self.client.chat.completions.create(
                        model=self.fallback_model,
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=2048
                    )
                else:
                    raise
            
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
            # Try primary model first, fallback if it fails
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1024
                )
            except Exception as e:
                # If primary model fails (e.g., decommissioned), try fallback
                if "model" in str(e).lower() or "decommissioned" in str(e).lower() or "400" in str(e):
                    print(f"⚠️ Primary model {self.model} failed, trying fallback {self.fallback_model}")
                    response = self.client.chat.completions.create(
                        model=self.fallback_model,
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1024
                    )
                else:
                    raise
            
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
        
        # If HTML is detected or selected, ensure it's used
        if detected_language.lower() == 'html' or preferred_language and preferred_language.lower() == 'html':
            primary_language = 'HTML'
        else:
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
        
        # Determine if multi-file generation is needed (for large applications)
        # Always generate multiple files when addressing GitHub health issues (agent mode)
        large_app_keywords = [
            'website', 'web app', 'web application', 'application', 'app', 'project',
            'full stack', 'fullstack', 'full-stack', 'ecommerce', 'e-commerce',
            'dashboard', 'admin panel', 'cms', 'blog', 'portfolio', 'landing page',
            'api', 'backend', 'frontend', 'react app', 'vue app', 'angular app',
            'django', 'flask', 'express', 'next.js', 'nuxt', 'multiple files',
            'complete', 'production', 'enterprise', 'github health', 'health issues',
            'fix issues', 'address issues', 'fix errors', 'address errors',
            'webpage', 'web page', 'page', 'login', 'form', 'button', 'input',
            'html', 'css', 'javascript', 'js', 'static site', 'static website'
        ]
        
        # Check if request mentions GitHub health issues
        has_health_issues = any(keyword in enhanced_request.lower() for keyword in [
            'github health', 'health issues', 'bad patterns', 'fix issues',
            'address issues', 'github health issues'
        ])
        
        # For HTML/CSS/JS requests, always generate multiple files
        is_html_request = (
            primary_language.lower() == 'html' or
            'html' in user_request.lower() or
            'webpage' in user_request.lower() or
            'web page' in user_request.lower() or
            'login page' in user_request.lower() or
            'landing page' in user_request.lower()
        )
        
        is_multi_file = (
            has_health_issues or  # Always multi-file when addressing health issues
            is_html_request or  # Always multi-file for HTML/webpage requests
            template in ['web-app', 'flask-app', 'static-site', 'rest-api', 'cli-tool', 'data-analysis'] or
            any(keyword in user_request.lower() for keyword in large_app_keywords) or
            'multiple files' in user_request.lower() or
            'project' in user_request.lower() or
            len(user_request.split()) > 5  # Shorter threshold - most requests need multiple files
        )
        
        if is_multi_file:
            # Determine number of files needed based on request complexity
            if is_html_request:
                # For HTML requests, always generate HTML, CSS, and JS files
                file_count_hint = "3-5 files (HTML, CSS, JavaScript)"
            elif any(kw in enhanced_request.lower() for kw in ['website', 'web app', 'application', 'full stack', 'complete']):
                file_count_hint = "5-15 files"
            else:
                file_count_hint = "3-8 files"
            
            prompt = f"""You are CodeMind, an AI coding assistant that writes code matching the user's unique coding style.

{style_context}

LANGUAGES USER USES: {', '.join(languages_used) if languages_used else 'Python'}
PRIMARY LANGUAGE: {primary_language}
LANGUAGE PATTERNS: {lang_patterns if lang_patterns else 'Standard patterns'}

USER REQUEST:
"{enhanced_request}"

{"For HTML/webpage requests, generate a COMPLETE webpage with HTML, CSS, and JavaScript files. " if is_html_request else ""}Generate a COMPLETE, PRODUCTION-READY {primary_language} application/project with MULTIPLE FILES ({file_count_hint}) that:
1. Fulfills the user's request completely and comprehensively
2. MATCHES their coding style EXACTLY (naming, documentation, error handling)
3. Is production-ready, well-structured, and scalable
4. Follows their patterns and conventions throughout ALL files
5. Uses {primary_language} best practices and modern patterns
6. Includes ALL necessary files:
   - Main application files (app.py, main.py, index.js, etc.)
   - Configuration files (config.py, .env.example, package.json, requirements.txt, etc.)
   - Utility/helper modules (utils.py, helpers.js, etc.)
   - Route/controller files (routes.py, controllers/, etc.)
   - Model/data files (models.py, schema.js, etc.)
   - Static assets structure (if web app: HTML, CSS, JS files)
   - README.md with setup instructions
   - Any other files needed for a complete, working application
   {"For HTML/webpage requests: MUST include index.html (or main.html), styles.css (or style.css), and script.js (or main.js) files. The HTML file should be complete with proper structure, the CSS should style all elements, and the JavaScript should handle all interactions." if is_html_request else ""}

IMPORTANT FOR LARGE APPLICATIONS:
- Generate COMPLETE, FULLY FUNCTIONAL code for each file
- Include proper imports, dependencies, and file structure
- Make it ready to run immediately after setup
- Include error handling, validation, and best practices
- For web apps: Include frontend (HTML/CSS/JS) AND backend files
- For APIs: Include routes, models, middleware, and configuration
- For full-stack: Include both frontend and backend with proper integration

Respond with JSON only (no markdown):
{{
  "files": [
    {{
      "filename": "{'index.html' if is_html_request else 'main.py'}",
      "code": "COMPLETE, FULLY IMPLEMENTED code for this file matching their style - include all imports, functions, classes, and logic"
    }}{f', {{ "filename": "styles.css", "code": "COMPLETE CSS styling for all elements in the HTML file - include responsive design, colors, fonts, layout, and all visual styling" }}, {{ "filename": "script.js", "code": "COMPLETE JavaScript code for all interactions, event handlers, form validation, and dynamic functionality" }}' if is_html_request else ''},
    {{
      "filename": "{'README.md' if is_html_request else 'config.py'}",
      "code": "{'Complete setup and usage instructions for the webpage' if is_html_request else 'COMPLETE configuration file with all settings'}"
    }}{f', {{ "filename": "requirements.txt", "code": "All required dependencies" }}' if not is_html_request else ''}
    // Add more files as needed for a complete application
  ],
  "explanation": "Brief explanation of the application structure and how to run it (3-4 sentences)",
  "language": "{primary_language}",
  "confidence": 0.0 to 1.0
}}

CRITICAL RULES:
1. Use {style_profile.get('naming_style', 'snake_case' if primary_language == 'Python' else 'camelCase')} naming EXACTLY in ALL files
2. {"Include type hints" if style_profile.get('type_hints_percentage', 0) > 50 and primary_language == 'Python' else "Match their documentation style"}
3. {"Add docstrings/comments" if style_profile.get('documentation_percentage', 0) > 50 else "Minimal documentation"}
4. Use {style_profile.get('error_handling_style', 'basic')} error handling style consistently across ALL files
5. ALL code should look like THEY wrote it in {primary_language}
6. Make it COMPLETE and FUNCTIONAL - every file must be fully implemented
7. Use {primary_language} best practices, modern patterns, and production-ready code
8. Generate {file_count_hint} as needed for a complete, working application
9. Include ALL necessary files for the application to run (config, dependencies, README, etc.)
10. For large applications: Break code into logical modules/files for maintainability
"""
        else:
            prompt = f"""You are CodeMind, an AI coding assistant that writes code matching the user's unique coding style.

{style_context}

LANGUAGES USER USES: {', '.join(languages_used) if languages_used else 'Python'}
PRIMARY LANGUAGE: {primary_language}
LANGUAGE PATTERNS: {lang_patterns if lang_patterns else 'Standard patterns'}

USER REQUEST:
"{enhanced_request}"

IMPORTANT: Focus on fixing errors found by the AI recommender. The generated code should:
1. Fix all errors and issues identified in the user's code
2. Address common problems like syntax errors, type errors, logic errors, and style issues
3. Be error-free and production-ready
4. MATCH their coding style EXACTLY (naming, documentation, error handling)
5. Follow their patterns and conventions
6. Use the {primary_language} language and its best practices
7. Include the FULL implementation - every function must have a complete body with all logic
8. Prevent future errors by following best practices

IMPORTANT: Generate the COMPLETE code implementation. Do NOT just write function signatures or incomplete code. Every function must have its full body with all the logic implemented.

Respond with JSON only (no markdown):
{{
  "code": "COMPLETE, FULLY IMPLEMENTED {primary_language} code matching their style - include full function bodies, not just signatures",
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
6. Make it COMPLETE and FUNCTIONAL - include full implementations, not just signatures
7. Use {primary_language} best practices and idioms
8. NEVER return incomplete code - always include the full function body with all logic
"""
        
        try:
            # Use higher token limit for large applications
            # Current models support up to 8,192 tokens
            # For large applications, we'll use the maximum available
            if is_multi_file:
                # For large applications, use maximum tokens available (8,192)
                max_tokens_for_request = 8192  # Maximum for current models
            else:
                max_tokens_for_request = 8192  # Standard limit for single files
            
            # Try primary model first, fallback if it fails
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=max_tokens_for_request
                )
            except Exception as e:
                # If primary model fails (e.g., decommissioned), try fallback
                if "model" in str(e).lower() or "decommissioned" in str(e).lower() or "400" in str(e):
                    print(f"⚠️ Primary model {self.model} failed, trying fallback {self.fallback_model}")
                    response = self.client.chat.completions.create(
                        model=self.fallback_model,
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=max_tokens_for_request
                    )
                else:
                    raise
            
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
                # Verify that code field exists and is not empty
                if 'code' in result and result['code']:
                    code_length = len(result['code'])
                    print(f"✅ Successfully parsed JSON response (code length: {code_length} chars)")
                    # Check if code looks incomplete (just a function signature)
                    if code_length < 50 and 'def ' in result['code'] and ':' in result['code'] and result['code'].count('\n') < 2:
                        print(f"⚠️ Warning: Code appears incomplete (only {code_length} chars). Response may be truncated.")
                elif 'files' in result and result['files']:
                    print(f"✅ Successfully parsed JSON response (multi-file with {len(result['files'])} files)")
                else:
                    print(f"⚠️ Warning: JSON parsed but no code or files found")
            except json.JSONDecodeError as json_err:
                print(f"JSON Parse Error: {json_err}")
                print(f"Response text (first 1000 chars): {text[:1000]}")
                print(f"Response text (last 500 chars): {text[-500:]}")
                
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
                    # Try multiple extraction methods
                    extracted_code = None
                    
                    # Method 1: Try triple-quoted strings (for multi-line code)
                    code_match = re.search(r'"code"\s*:\s*"""([\s\S]*?)"""', text)
                    if code_match:
                        extracted_code = code_match.group(1).strip()
                    
                    # Method 2: Try single-quoted strings with escaped newlines
                    if not extracted_code:
                        code_match = re.search(r'"code"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
                        if code_match:
                            # Unescape the string
                            extracted_code = code_match.group(1).replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace("\\'", "'").strip()
                    
                    # Method 3: Try markdown code blocks (might be outside JSON)
                    if not extracted_code:
                        code_match = re.search(r'```(?:python|javascript|typescript|java|html|css|json)?\s*\n(.*?)```', text, re.DOTALL)
                        if code_match:
                            extracted_code = code_match.group(1).strip()
                            # If it's JSON, try to parse it
                            try:
                                json_result = json.loads(extracted_code)
                                if 'code' in json_result:
                                    extracted_code = json_result['code']
                            except:
                                pass
                    
                    # Method 4: Try to find code after "code": in JSON (even if malformed)
                    if not extracted_code:
                        # Look for "code": followed by text until next key or end
                        code_match = re.search(r'"code"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', text, re.DOTALL)
                        if code_match:
                            extracted_code = code_match.group(1).replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').strip()
                    
                    if extracted_code:
                        # Try to extract explanation too
                        explanation_match = re.search(r'"explanation"\s*:\s*"([^"]*)"', text)
                        explanation = explanation_match.group(1) if explanation_match else 'Code generated (parsed from response)'
                        
                        print(f"✅ Extracted code from response (length: {len(extracted_code)} chars)")
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
            'HTML': ['html', 'webpage', 'web page', 'website', 'web site', 'login page', 'landing page', 'form', 'button', 'input', 'div', 'span'],
            'CSS': ['css', 'stylesheet', 'styling', 'design', 'layout', 'responsive'],
            'JavaScript': ['javascript', 'js', 'node', 'react', 'vue', 'angular', 'script', 'function', 'event'],
            'Python': ['python', 'py', 'django', 'flask', 'pandas', 'numpy'],
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
        
        # Check HTML first (most common for web requests)
        if any(keyword in request_lower for keyword in language_keywords['HTML']):
            return 'HTML'
        
        for lang, keywords in language_keywords.items():
            if lang != 'HTML' and any(keyword in request_lower for keyword in keywords):
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
