"""
GitHub integration to fetch repositories and code files
"""
import requests
from typing import List, Dict


def fetch_user_repositories(username: str) -> List[str]:
    """
    Fetch all public repositories for a GitHub user
    
    Returns:
        List of repository URLs
    """
    try:
        url = f"https://api.github.com/users/{username}/repos"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return []
        
        repos = response.json()
        repo_urls = [repo['html_url'] for repo in repos if not repo.get('fork', False)]
        
        # Limit to 20 most recent repos
        return repo_urls[:20]
        
    except Exception as e:
        print(f"Error fetching repositories: {e}")
        return []


def fetch_github_repo_files(repo_url: str, file_extensions: List[str] = ['.py']) -> List[Dict[str, str]]:
    """
    Fetch Python files from a GitHub repository
    
    Args:
        repo_url: GitHub repository URL (e.g., https://github.com/user/repo)
        file_extensions: List of file extensions to fetch
    
    Returns:
        List of dicts with 'filename' and 'content' keys
    """
    try:
        # Convert URL to API format
        # https://github.com/user/repo -> user/repo
        parts = repo_url.replace('https://github.com/', '').split('/')
        if len(parts) < 2:
            return []
        
        owner = parts[0]
        repo = parts[1]
        
        # Get repository tree
        api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code != 200:
            # Try master branch
            api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1"
            response = requests.get(api_url, timeout=10)
            if response.status_code != 200:
                return []
        
        tree = response.json()
        files = []
        
        # Filter Python files
        for item in tree.get('tree', []):
            if item.get('type') == 'blob':
                path = item.get('path', '')
                if any(path.endswith(ext) for ext in file_extensions):
                    # Skip large files
                    if item.get('size', 0) > 100000:
                        continue
                    
                    # Fetch file content
                    file_url = item.get('url')
                    if file_url:
                        file_response = requests.get(file_url, timeout=10)
                        if file_response.status_code == 200:
                            file_data = file_response.json()
                            import base64
                            content = base64.b64decode(file_data.get('content', '')).decode('utf-8', errors='ignore')
                            files.append({
                                'filename': f"{repo}/{path}",
                                'content': content
                            })
        
        return files[:30]  # Limit to 30 files per repo
        
    except Exception as e:
        print(f"GitHub integration error: {e}")
        return []


def fetch_all_user_code_files(username: str, file_extensions: List[str] = ['.py']) -> List[Dict[str, str]]:
    """
    Fetch Python files from all repositories of a GitHub user
    """
    try:
        repo_urls = fetch_user_repositories(username)
        
        if not repo_urls:
            return []
        
        all_files = []
        
        for i, repo_url in enumerate(repo_urls):
            try:
                print(f"Fetching files from repository {i+1}/{len(repo_urls)}: {repo_url}")
                files = fetch_github_repo_files(repo_url, file_extensions)
                all_files.extend(files)
                
                if len(all_files) >= 50:
                    print(f"Reached file limit (50 files)")
                    break
                    
            except Exception as e:
                print(f"Error fetching files from {repo_url}: {e}")
                continue
        
        print(f"Total files fetched: {len(all_files)}")
        return all_files
        
    except Exception as e:
        print(f"Error fetching user code files: {e}")
        return []
