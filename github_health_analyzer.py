"""
GitHub Repository Health Analyzer
Analyzes repositories based on good/bad patterns and generates health reports
"""
import requests
import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import os
from dotenv import load_dotenv

load_dotenv()

# Good Patterns (Signs of Healthy Repository)
GOOD_PATTERNS = {
    'documentation': {
        'README.md': {'weight': 10, 'description': 'README.md file exists'},
        'CONTRIBUTING.md': {'weight': 8, 'description': 'CONTRIBUTING.md file exists'},
        'CODE_OF_CONDUCT.md': {'weight': 5, 'description': 'CODE_OF_CONDUCT.md file exists'},
        'LICENSE': {'weight': 10, 'description': 'LICENSE file exists'},
        'LICENSE.md': {'weight': 10, 'description': 'LICENSE.md file exists'},
        'SECURITY.md': {'weight': 7, 'description': 'SECURITY.md file exists'},
        'docs/': {'weight': 5, 'description': 'Documentation directory exists'},
    },
    'automation': {
        '.github/workflows/': {'weight': 10, 'description': 'GitHub Actions workflows exist'},
        'ci.yml': {'weight': 8, 'description': 'CI configuration file exists'},
        'test': {'weight': 8, 'description': 'Test files/directories exist'},
        'tests/': {'weight': 8, 'description': 'Tests directory exists'},
        '__tests__/': {'weight': 8, 'description': 'Tests directory exists'},
        'pytest': {'weight': 5, 'description': 'Pytest configuration exists'},
        'jest': {'weight': 5, 'description': 'Jest configuration exists'},
    },
    'code_quality': {
        '.eslintrc': {'weight': 6, 'description': 'ESLint configuration exists'},
        '.flake8': {'weight': 6, 'description': 'Flake8 configuration exists'},
        '.pylintrc': {'weight': 6, 'description': 'Pylint configuration exists'},
        '.prettierrc': {'weight': 5, 'description': 'Prettier configuration exists'},
        '.editorconfig': {'weight': 4, 'description': 'EditorConfig exists'},
        'pyproject.toml': {'weight': 5, 'description': 'PyProject.toml exists'},
        'setup.py': {'weight': 4, 'description': 'Setup.py exists'},
        'requirements.txt': {'weight': 5, 'description': 'Requirements.txt exists'},
        'package.json': {'weight': 5, 'description': 'Package.json exists'},
    },
    'security': {
        '.gitignore': {'weight': 8, 'description': '.gitignore file exists'},
        'dependabot': {'weight': 7, 'description': 'Dependabot configuration exists'},
        'codeql': {'weight': 6, 'description': 'CodeQL configuration exists'},
        'secret-scanning': {'weight': 6, 'description': 'Secret scanning enabled'},
    },
    'structure': {
        'src/': {'weight': 4, 'description': 'Source directory structure exists'},
        'lib/': {'weight': 3, 'description': 'Library directory exists'},
        'config/': {'weight': 3, 'description': 'Configuration directory exists'},
    }
}

# Bad Patterns (Red Flags)
BAD_PATTERNS = {
    'secrets': {
        'api_key': {'weight': 20, 'description': 'API key found in code'},
        'password': {'weight': 20, 'description': 'Password found in code'},
        'secret': {'weight': 15, 'description': 'Secret found in code'},
        'token': {'weight': 15, 'description': 'Token found in code'},
        'sk_live': {'weight': 25, 'description': 'Stripe live key found'},
        'sk_test': {'weight': 15, 'description': 'Stripe test key found'},
        'aws_secret': {'weight': 20, 'description': 'AWS secret found'},
    },
    'large_files': {
        'node_modules/': {'weight': 15, 'description': 'node_modules committed'},
        '__pycache__/': {'weight': 10, 'description': '__pycache__ committed'},
        '.zip': {'weight': 12, 'description': 'ZIP files in repository'},
        '.exe': {'weight': 12, 'description': 'Executable files in repository'},
        '.mp4': {'weight': 10, 'description': 'Video files in repository'},
        '.db': {'weight': 10, 'description': 'Database files in repository'},
    },
    'code_smells': {
        'god_file': {'weight': 10, 'description': 'Very large files (>1000 lines)'},
        'duplicated_code': {'weight': 8, 'description': 'Duplicated code blocks'},
        'commented_out': {'weight': 5, 'description': 'Large blocks of commented code'},
        'dead_code': {'weight': 6, 'description': 'Unused functions/variables'},
    },
    'missing_files': {
        'no_readme': {'weight': 15, 'description': 'No README.md file'},
        'no_license': {'weight': 15, 'description': 'No LICENSE file'},
        'no_gitignore': {'weight': 10, 'description': 'No .gitignore file'},
    }
}

def get_github_headers() -> Dict[str, str]:
    """Get headers for GitHub API requests"""
    token = os.getenv('GITHUB_TOKEN') or os.getenv('GITHUB_PAT')
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'CodeMind/1.0'
    }
    if token:
        if token.startswith('github_pat_'):
            headers['Authorization'] = f'Bearer {token}'
        else:
            headers['Authorization'] = f'token {token}'
    return headers

def analyze_repository_structure(owner: str, repo: str, default_branch: str = 'main') -> Dict:
    """
    Analyze repository structure for good/bad patterns
    
    Returns:
        Dict with good_patterns, bad_patterns, scores, and details
    """
    headers = get_github_headers()
    good_found = []
    bad_found = []
    good_score = 0
    bad_score = 0
    
    def check_directory(path: str = '', depth: int = 0):
        """Recursively check repository structure"""
        if depth > 3:  # Limit depth
            return
        
        try:
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
            response = requests.get(api_url, timeout=10, headers=headers, params={'ref': default_branch})
            
            if response.status_code != 200:
                return
            
            contents = response.json()
            if isinstance(contents, dict):
                contents = [contents]
            
            for item in contents:
                item_path = item.get('path', '')
                item_name = item.get('name', '')
                item_type = item.get('type', '')
                
                # Check for good patterns
                for category, patterns in GOOD_PATTERNS.items():
                    for pattern, info in patterns.items():
                        if pattern in item_path or pattern in item_name:
                            if pattern not in [p['pattern'] for p in good_found]:
                                good_found.append({
                                    'pattern': pattern,
                                    'path': item_path,
                                    'category': category,
                                    'weight': info['weight'],
                                    'description': info['description']
                                })
                                good_score += info['weight']
                
                # Check for bad patterns in file names
                for category, patterns in BAD_PATTERNS.items():
                    for pattern, info in patterns.items():
                        if pattern in item_path.lower() or pattern in item_name.lower():
                            if pattern not in [p['pattern'] for p in bad_found]:
                                bad_found.append({
                                    'pattern': pattern,
                                    'path': item_path,
                                    'category': category,
                                    'weight': info['weight'],
                                    'description': info['description']
                                })
                                bad_score += info['weight']
                
                # Recursively check subdirectories
                if item_type == 'dir' and depth < 3:
                    check_directory(item_path, depth + 1)
        
        except Exception as e:
            print(f"Error checking directory {path}: {e}")
    
    # Check root directory
    check_directory()
    
    # Check for missing critical files
    file_names = [item.get('pattern', '') for item in good_found + bad_found]
    if 'README.md' not in str(file_names):
        bad_found.append({
            'pattern': 'no_readme',
            'path': 'root',
            'category': 'missing_files',
            'weight': BAD_PATTERNS['missing_files']['no_readme']['weight'],
            'description': BAD_PATTERNS['missing_files']['no_readme']['description']
        })
        bad_score += BAD_PATTERNS['missing_files']['no_readme']['weight']
    
    if 'LICENSE' not in str(file_names) and 'LICENSE.md' not in str(file_names):
        bad_found.append({
            'pattern': 'no_license',
            'path': 'root',
            'category': 'missing_files',
            'weight': BAD_PATTERNS['missing_files']['no_license']['weight'],
            'description': BAD_PATTERNS['missing_files']['no_license']['description']
        })
        bad_score += BAD_PATTERNS['missing_files']['no_license']['weight']
    
    return {
        'good_patterns': good_found,
        'bad_patterns': bad_found,
        'good_score': good_score,
        'bad_score': bad_score,
        'total_good_weight': sum(GOOD_PATTERNS[cat][pat]['weight'] for cat in GOOD_PATTERNS for pat in GOOD_PATTERNS[cat]),
        'total_bad_weight': sum(BAD_PATTERNS[cat][pat]['weight'] for cat in BAD_PATTERNS for pat in BAD_PATTERNS[cat])
    }

def analyze_code_content(files: List[Dict[str, str]]) -> Dict:
    """
    Analyze code content for bad patterns (secrets, code smells)
    
    Args:
        files: List of dicts with 'filename' and 'content' keys
    
    Returns:
        Dict with bad patterns found in code
    """
    bad_found = []
    bad_score = 0
    
    # Patterns to detect secrets in code
    secret_patterns = {
        r'api[_-]?key\s*[:=]\s*["\']([^"\']+)["\']': {'weight': 20, 'description': 'API key in code'},
        r'password\s*[:=]\s*["\']([^"\']+)["\']': {'weight': 20, 'description': 'Password in code'},
        r'secret\s*[:=]\s*["\']([^"\']+)["\']': {'weight': 15, 'description': 'Secret in code'},
        r'sk_live_[A-Za-z0-9]{24,}': {'weight': 25, 'description': 'Stripe live key'},
        r'sk_test_[A-Za-z0-9]{24,}': {'weight': 15, 'description': 'Stripe test key'},
    }
    
    # Check for large files
    for file_data in files:
        content = file_data.get('content', '')
        filename = file_data.get('filename', '')
        lines = content.split('\n')
        
        # Check for very large files (god files)
        if len(lines) > 1000:
            bad_found.append({
                'pattern': 'god_file',
                'path': filename,
                'category': 'code_smells',
                'weight': 10,
                'description': f'Very large file: {len(lines)} lines'
            })
            bad_score += 10
        
        # Check for secrets
        for pattern, info in secret_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                bad_found.append({
                    'pattern': pattern,
                    'path': filename,
                    'category': 'secrets',
                    'weight': info['weight'],
                    'description': f"{info['description']} in {filename}"
                })
                bad_score += info['weight']
                break  # Only count once per file
    
    return {
        'bad_patterns': bad_found,
        'bad_score': bad_score
    }

def calculate_language_percentages(files: List[Dict[str, str]]) -> Dict[str, float]:
    """
    Calculate language percentages from files
    
    Args:
        files: List of dicts with 'language' key
    
    Returns:
        Dict with language names as keys and percentages as values
    """
    language_counts = defaultdict(int)
    total_files = len(files)
    
    if total_files == 0:
        return {}
    
    for file_data in files:
        language = file_data.get('language', 'Unknown')
        language_counts[language] += 1
    
    # Calculate percentages
    language_percentages = {}
    for language, count in language_counts.items():
        percentage = (count / total_files) * 100
        language_percentages[language] = round(percentage, 1)
    
    return language_percentages

def analyze_github_profile_health(username: str, repos: List[Dict]) -> Dict:
    """
    Analyze GitHub profile health across all repositories
    
    Args:
        username: GitHub username
        repos: List of repository info dicts
    
    Returns:
        Comprehensive health analysis report
    """
    all_good_patterns = []
    all_bad_patterns = []
    total_good_score = 0
    total_bad_score = 0
    repo_analyses = []
    
    headers = get_github_headers()
    
    for repo_info in repos:
        owner = repo_info['owner']
        repo_name = repo_info['name']
        default_branch = repo_info.get('default_branch', 'main')
        
        # Analyze repository structure
        repo_analysis = analyze_repository_structure(owner, repo_name, default_branch)
        repo_analyses.append({
            'repo': repo_name,
            'url': repo_info.get('html_url', ''),
            'analysis': repo_analysis
        })
        
        all_good_patterns.extend(repo_analysis['good_patterns'])
        all_bad_patterns.extend(repo_analysis['bad_patterns'])
        total_good_score += repo_analysis['good_score']
        total_bad_score += repo_analysis['bad_score']
    
    # Calculate percentages
    max_possible_good = len(repos) * 100  # Approximate max score per repo
    max_possible_bad = len(repos) * 100
    
    good_percentage = min(100, (total_good_score / max_possible_good * 100)) if max_possible_good > 0 else 0
    bad_percentage = min(100, (total_bad_score / max_possible_bad * 100)) if max_possible_bad > 0 else 0
    
    # Normalize percentages (they should add up to show relative health)
    total_score = total_good_score + total_bad_score
    if total_score > 0:
        good_percentage = (total_good_score / total_score) * 100
        bad_percentage = (total_bad_score / total_score) * 100
    else:
        good_percentage = 50
        bad_percentage = 50
    
    return {
        'username': username,
        'repositories_analyzed': len(repos),
        'good_patterns': all_good_patterns,
        'bad_patterns': all_bad_patterns,
        'good_score': total_good_score,
        'bad_score': total_bad_score,
        'good_percentage': round(100 - bad_percentage, 1),  # Invert: more good = higher percentage
        'bad_percentage': round(bad_percentage, 1),
        'health_score': round(100 - bad_percentage, 1),  # Overall health score
        'repo_analyses': repo_analyses,
        'summary': {
            'total_good_patterns': len(all_good_patterns),
            'total_bad_patterns': len(all_bad_patterns),
            'health_status': 'excellent' if bad_percentage < 20 else 'good' if bad_percentage < 40 else 'needs_improvement' if bad_percentage < 60 else 'poor'
        }
    }

