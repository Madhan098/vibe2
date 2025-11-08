"""
GitHub integration to fetch repositories and code files
"""
import requests
from typing import List, Dict, Optional
import time
import os
from dotenv import load_dotenv
from language_detector import get_language_from_extension

load_dotenv()

def get_github_token() -> Optional[str]:
    """Get GitHub token from environment variables"""
    token = os.getenv('GITHUB_TOKEN') or os.getenv('GITHUB_PAT')
    if token and not os.getenv('GITHUB_TOKEN_LOADED'):
        print("[OK] GitHub token found - authenticated requests enabled")
        token_type = 'Fine-grained PAT' if token.startswith('github_pat_') else 'Classic token'
        print(f"   Token type: {token_type}")
        os.environ['GITHUB_TOKEN_LOADED'] = '1'  # Prevent repeated messages
    return token

def get_github_headers() -> Dict[str, str]:
    """Get headers for GitHub API requests with authentication"""
    token = get_github_token()
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'CodeMind/1.0'
    }
    if token:
        # GitHub fine-grained PATs (github_pat_*) use Bearer, classic tokens use token
        if token.startswith('github_pat_'):
            headers['Authorization'] = f'Bearer {token}'
        else:
            headers['Authorization'] = f'token {token}'
    return headers


def fetch_user_repositories(username: str) -> List[Dict]:
    """
    Fetch all repositories for a GitHub user (public and private if authenticated and token belongs to user)
    
    Returns:
        List of dicts with 'html_url', 'name', 'default_branch', and 'owner'
    """
    try:
        headers = get_github_headers()
        token = get_github_token()
        
        # If authenticated, try to get current user first to see if we can access private repos
        current_user = None
        if token:
            try:
                user_response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
                if user_response.status_code == 200:
                    current_user = user_response.json().get('login', '').lower()
                    print(f"Authenticated as: {current_user}")
            except:
                pass  # Continue with public repos if user endpoint fails
        
        # Use authenticated endpoint if token belongs to requested user, otherwise use public endpoint
        if token and current_user and current_user == username.lower():
            # Token belongs to the requested user - can access private repos
            # Note: Can't use both 'type' and 'affiliation' together - use 'affiliation' only
            url = "https://api.github.com/user/repos"
            params = {
                'per_page': 100,
                'sort': 'updated',
                'affiliation': 'owner,collaborator,organization_member'  # Include all repos user has access to
            }
            print(f"Using authenticated endpoint - will include private repositories")
        else:
            # Public endpoint or different user
            url = f"https://api.github.com/users/{username}/repos"
            params = {
                'per_page': 100,
                'sort': 'updated',
                'type': 'all'  # all, owner, member
            }
        
        all_repos = []
        page = 1
        per_page = 100
        
        # Fetch all pages of repositories
        while True:
            params['page'] = page
            response = requests.get(url, timeout=30, headers=headers, params=params)
            
            if response.status_code == 404:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('message', 'User not found')
                print(f"User {username} not found: {error_msg}")
                return []
            elif response.status_code == 403:
                error_msg = response.json().get('message', '')
                if 'rate limit' in error_msg.lower():
                    print(f"Rate limit exceeded. Please wait or use authentication for higher limits.")
                else:
                    print(f"Access denied: {error_msg}")
                return []
            elif response.status_code == 422:
                # Bad request - usually means invalid parameters
                error_data = response.json()
                error_msg = error_data.get('message', 'Invalid request parameters')
                print(f"GitHub API error (422): {error_msg}")
                print(f"   Documentation: {error_data.get('documentation_url', 'N/A')}")
                # Try with simpler parameters
                if 'type' in params and 'affiliation' in params:
                    print("   Retrying with affiliation only (removing type)...")
                    params.pop('type', None)
                    continue
                break
            elif response.status_code != 200:
                print(f"GitHub API returned status {response.status_code}: {response.text[:200]}")
                break
            
            repos = response.json()
            if not repos:
                break
            
            all_repos.extend(repos)
            
            # If we got fewer than per_page, we're on the last page
            if len(repos) < per_page:
                break
            
            page += 1
            # Limit to first page for faster results (most recent repos)
            if page > 1:
                break
        
        if not all_repos:
            print(f"⚠️ No repositories found for {username}")
            print(f"   This could mean:")
            print(f"   - User doesn't exist")
            print(f"   - User has no public repositories")
            print(f"   - All repositories are private (requires GitHub token)")
            return []
        
        # Include all repos (not filtering forks) and get default branch
        repo_info = []
        for repo in all_repos:
            repo_info.append({
                'html_url': repo['html_url'],
                'name': repo['name'],
                'owner': repo['owner']['login'],
                'default_branch': repo.get('default_branch', 'main'),
                'is_fork': repo.get('fork', False),
                'private': repo.get('private', False),
                'size': repo.get('size', 0),  # Size in KB
                'language': repo.get('language', None)
            })
        
        # Log repository details
        print(f"✅ Found {len(repo_info)} repositories for {username}")
        for repo in repo_info[:5]:
            fork_status = " (fork)" if repo['is_fork'] else ""
            private_status = " (private)" if repo['private'] else " (public)"
            lang_status = f" - {repo['language']}" if repo['language'] else ""
            print(f"   - {repo['name']}{fork_status}{private_status}{lang_status}")
        
        # Limit to 5 most recent repos for faster analysis
        print(f"Processing up to 5 most recent repositories...")
        return repo_info[:5]
        
    except requests.exceptions.Timeout:
        print(f"Timeout fetching repositories for {username}")
        return []
    except Exception as e:
        print(f"Error fetching repositories: {e}")
        import traceback
        traceback.print_exc()
        return []


def fetch_github_repo_files(owner: str, repo: str, default_branch: str = 'main', file_extensions: List[str] = None) -> List[Dict[str, str]]:
    """
    Fetch code files from a GitHub repository using recursive directory traversal
    Supports ALL programming languages
    
    Args:
        owner: Repository owner username
        repo: Repository name
        default_branch: Default branch name (e.g., 'main', 'master')
        file_extensions: List of file extensions to fetch. If None, fetches all common code files
    
    Returns:
        List of dicts with 'filename' and 'content' keys
    """
    # Define all common programming language extensions if not provided
    if file_extensions is None:
        file_extensions = [
            # Python
            '.py', '.pyw', '.pyx',
            # JavaScript/TypeScript
            '.js', '.jsx', '.ts', '.tsx', '.mjs',
            # Java
            '.java',
            # C/C++
            '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp',
            # C#
            '.cs',
            # Go
            '.go',
            # Rust
            '.rs',
            # Ruby
            '.rb',
            # PHP
            '.php',
            # Swift
            '.swift',
            # Kotlin
            '.kt', '.kts',
            # Scala
            '.scala',
            # R
            '.r',
            # MATLAB
            '.m',
            # Shell scripts
            '.sh', '.bash', '.zsh',
            # HTML/CSS
            '.html', '.css', '.scss', '.sass', '.less',
            # Other
            '.vue', '.svelte', '.dart', '.lua', '.pl', '.pm', '.sql'
        ]
    """
    Fetch Python files from a GitHub repository using recursive directory traversal
    
    Args:
        owner: Repository owner username
        repo: Repository name
        default_branch: Default branch name (e.g., 'main', 'master')
        file_extensions: List of file extensions to fetch
    
    Returns:
        List of dicts with 'filename' and 'content' keys
    """
    files = []
    
    def fetch_directory(path: str = '', depth: int = 0):
        """Recursively fetch files from a directory"""
        if depth > 4:  # Increased recursion depth to find more files (max 4 levels deep)
            return
        
        try:
            headers = get_github_headers()
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
            response = requests.get(api_url, timeout=15, headers=headers, params={'ref': default_branch})
            
            if response.status_code != 200:
                # Try alternative branch names
                for branch in ['main', 'master', 'develop']:
                    if branch != default_branch:
                        response = requests.get(api_url, timeout=15, headers=headers, params={'ref': branch})
                        if response.status_code == 200:
                            break
                
                if response.status_code != 200:
                    print(f"Could not access {owner}/{repo}/{path} (status {response.status_code})")
                    return
            
            contents = response.json()
            
            # Handle single file response
            if isinstance(contents, dict):
                contents = [contents]
            
            for item in contents:
                if item.get('type') == 'file':
                    file_path = item.get('path', '')
                    # Check if it's a code file
                    if any(file_path.endswith(ext) for ext in file_extensions):
                        # Skip large files and common non-source directories
                        if item.get('size', 0) > 50000:  # 50KB limit (reduced for speed)
                            continue
                        # Skip common non-source directories
                        skip_dirs = ['node_modules', '.git', 'venv', 'env', '__pycache__', '.next', 'dist', 'build']
                        if any(skip_dir in file_path for skip_dir in skip_dirs):
                            continue
                        
                        # Fetch file content
                        try:
                            content = None
                            
                            # Use download_url if available (direct text), otherwise use API
                            headers = get_github_headers()
                            if item.get('download_url'):
                                # Direct download URL - plain text
                                file_response = requests.get(item['download_url'], timeout=10, headers=headers)
                                if file_response.status_code == 200:
                                    content = file_response.text
                            elif item.get('content'):
                                # Content is already in the response (base64 encoded)
                                import base64
                                content = base64.b64decode(item['content']).decode('utf-8', errors='ignore')
                            elif item.get('url'):
                                # Fetch from blob URL
                                file_response = requests.get(item['url'], timeout=10, headers=headers)
                                if file_response.status_code == 200:
                                    file_data = file_response.json()
                                    import base64
                                    content = base64.b64decode(file_data.get('content', '')).decode('utf-8', errors='ignore')
                            
                            if content:
                                files.append({
                                    'filename': f"{repo}/{file_path}",
                                    'content': content,
                                    'language': get_language_from_extension('.' + file_path.split('.')[-1] if '.' in file_path else '')
                                })
                                
                                if len(files) >= 30:  # Increased limit per repo (30 files max per repo)
                                    return
                                
                                # Reduced delay - we have authentication, rate limits are higher
                                # time.sleep(0.1)  # Removed delay for speed
                        except Exception as e:
                            print(f"Error fetching file {file_path}: {e}")
                            continue
                
                elif item.get('type') == 'dir':
                    # Recursively fetch from subdirectory
                    if len(files) < 30:  # Increased limit for faster analysis
                        fetch_directory(item.get('path', ''), depth + 1)
        
        except Exception as e:
            print(f"Error fetching directory {path}: {e}")
    
    try:
        print(f"Fetching code files from {owner}/{repo} (branch: {default_branch})")
        fetch_directory()
        
        if len(files) == 0:
            print(f"⚠️ No code files found in {owner}/{repo}. Repository might be empty or contain only non-code files.")
        else:
            print(f"✅ Successfully fetched {len(files)} code files from {owner}/{repo}")
        
        return files
    except Exception as e:
        print(f"❌ Error fetching files from {owner}/{repo}: {e}")
        import traceback
        traceback.print_exc()
        return []


def fetch_all_user_code_files(username: str, file_extensions: List[str] = None, progress_key: str = None) -> List[Dict[str, str]]:
    """
    Fetch code files from all repositories of a GitHub user (all languages)
    """
    # Import here to avoid circular dependency
    from app import github_progress, progress_lock
    
    try:
        print(f"Fetching repositories for user: {username}")
        if progress_key:
            with progress_lock:
                github_progress[progress_key] = {'percent': 20, 'status': 'Fetching repositories...'}
        
        repos = fetch_user_repositories(username)
        
        if not repos:
            print(f"No repositories found for {username}")
            if progress_key:
                with progress_lock:
                    github_progress.pop(progress_key, None)
            return []
        
        print(f"Processing {len(repos)} repositories...")
        if progress_key:
            with progress_lock:
                github_progress[progress_key] = {'percent': 25, 'status': f'Found {len(repos)} repositories. Fetching files...'}
        
        all_files = []
        
        for i, repo_info in enumerate(repos):
            try:
                owner = repo_info['owner']
                repo_name = repo_info['name']
                default_branch = repo_info['default_branch']
                repo_url = repo_info['html_url']
                
                print(f"[{i+1}/{len(repos)}] Fetching files from: {repo_url} (branch: {default_branch})")
                
                # Update progress before fetching (more granular updates)
                if progress_key:
                    # 25-60% for fetching repos (25% base + 35% for repos)
                    repo_progress = 25 + int((i / max(len(repos), 1)) * 35)
                    with progress_lock:
                        github_progress[progress_key] = {
                            'percent': min(repo_progress, 60),
                            'status': f'Fetching repository {i+1}/{len(repos)}: {repo_name}...'
                        }
                
                files = fetch_github_repo_files(owner, repo_name, default_branch, file_extensions)
                all_files.extend(files)
                
                # Count files by language
                languages = {}
                for file in files:
                    ext = '.' + file['filename'].split('.')[-1] if '.' in file['filename'] else ''
                    lang = get_language_from_extension(ext)
                    languages[lang] = languages.get(lang, 0) + 1
                
                lang_summary = ', '.join([f"{count} {lang}" for lang, count in languages.items()])
                print(f"  -> Found {len(files)} code files ({lang_summary}) - total so far: {len(all_files)}")
                
                # Update progress after each repo (more accurate)
                if progress_key:
                    # Calculate progress based on completed repos
                    repo_progress = 25 + int(((i + 1) / len(repos)) * 35)
                    with progress_lock:
                        github_progress[progress_key] = {
                            'percent': min(repo_progress, 60),
                            'status': f'Fetched {len(all_files)} files from {i+1}/{len(repos)} repositories...'
                        }
                
                # Limit total files to avoid timeout (reduced for faster analysis)
                if len(all_files) >= 40:
                    print(f"Reached file limit (40 files), stopping for faster analysis")
                    break
                
                # Removed delay - authentication provides higher rate limits
                # time.sleep(0.3)
                    
            except Exception as e:
                print(f"Error fetching files from {repo_info.get('html_url', 'unknown')}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"Total files fetched: {len(all_files)}")
        
        # Update progress to 60% when fetching is complete
        if progress_key:
            with progress_lock:
                github_progress[progress_key] = {
                    'percent': 60,
                    'status': f'Fetched {len(all_files)} files. Starting analysis...'
                }
        
        return all_files
        
    except Exception as e:
        print(f"Error fetching user code files: {e}")
        import traceback
        traceback.print_exc()
        return []
