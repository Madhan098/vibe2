"""
CodeMind Flask Backend
"""
from flask import Flask, request, jsonify, render_template, send_from_directory, Response
from flask_cors import CORS
import os
from dotenv import load_dotenv
import requests
import subprocess
import tempfile
import shutil
import re
from code_analyzer import analyze_code_files, analyze_code
from github_integration import fetch_all_user_code_files, fetch_user_repositories, get_github_headers
from github_health_analyzer import analyze_github_profile_health, calculate_language_percentages, analyze_code_content
import threading

# Global progress tracking for GitHub analysis
github_progress = {}
# Global progress tracking for file upload analysis
file_upload_progress = {}
progress_lock = threading.Lock()
from ai_engine import AIEngine
from multi_language_analyzer import analyze_all_languages
from language_detector import get_language_from_extension, detect_language_from_content
from models import (
    create_user, get_user_by_email, get_user_by_id,
    create_session, get_session, delete_session, cleanup_expired_sessions,
    get_user_profile, save_style_profile, get_style_profile,
    update_style_profile_from_feedback
)

load_dotenv()

# Initialize Flask app with templates and static folders
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static',
            static_url_path='')

# Disable caching in development
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
if app.config.get('DEBUG'):
    app.config['TEMPLATES_AUTO_RELOAD'] = True

# CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize AI engine
groq_key = os.getenv('GROQ_API_KEY')
if not groq_key:
    print("WARNING: GROQ_API_KEY not found in environment variables!")
    print("AI features will not work. Please set GROQ_API_KEY in .env file.")
ai_engine = AIEngine(api_key=groq_key) if groq_key else None

# Clean up expired sessions periodically
import time
import random

def periodic_cleanup():
    """Periodically clean up expired sessions"""
    while True:
        time.sleep(3600)  # Run every hour
        try:
            cleaned = cleanup_expired_sessions()
            if cleaned > 0:
                print(f"Cleaned up {cleaned} expired sessions")
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()

@app.before_request
def before_request():
    """Run before each request - cleanup expired sessions occasionally"""
    # Clean up expired sessions every 100 requests (to avoid overhead)
    if random.randint(1, 100) == 1:  # 1% chance per request
        try:
            cleanup_expired_sessions()
        except:
            pass


# ==========================================
# API ROUTES
# ==========================================

# Authentication routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not name or not email or not password:
            return jsonify({'error': 'Name, email, and password are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        user, error = create_user(email, name, password)
        if error:
            return jsonify({'error': error}), 400
        
        # Create session (30 days expiration)
        token = create_session(user.id, expires_in_days=30)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': user.to_dict(),
            'expires_in_days': 30
        }), 201
        
    except Exception as e:
        print(f"Error registering user: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.json
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = get_user_by_email(email)
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Create session (30 days expiration)
        token = create_session(user.id, expires_in_days=30)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': user.to_dict(),
            'expires_in_days': 30
        }), 200
        
    except Exception as e:
        print(f"Error logging in: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token:
            delete_session(token)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Error logging out: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/firebase', methods=['POST'])
def firebase_auth():
    """Authenticate user with Firebase ID token"""
    try:
        data = request.json
        id_token = data.get('idToken', '').strip()
        
        if not id_token:
            return jsonify({'error': 'Firebase ID token is required'}), 400
        
        # Verify Firebase ID token
        try:
            import firebase_admin
            from firebase_admin import auth, credentials
            
            # Initialize Firebase Admin if not already initialized
            if not firebase_admin._apps:
                # Use default credentials or service account
                cred = credentials.Certificate({
                    "type": "service_account",
                    "project_id": "codemind-372a6",
                    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID', ''),
                    "private_key": os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
                    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL', ''),
                    "client_id": os.getenv('FIREBASE_CLIENT_ID', ''),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL', '')
                }) if os.getenv('FIREBASE_PRIVATE_KEY') else credentials.ApplicationDefault()
                
                firebase_admin.initialize_app(cred)
            
            # Verify the ID token
            decoded_token = auth.verify_id_token(id_token)
            firebase_uid = decoded_token['uid']
            firebase_email = decoded_token.get('email', '').lower().strip()
            firebase_name = decoded_token.get('name', '').strip() or firebase_email.split('@')[0]
            
            if not firebase_email:
                return jsonify({'error': 'Could not get email from Firebase token'}), 400
            
            # Check if user exists in our database
            user = get_user_by_email(firebase_email)
            
            if not user:
                # Create new user
                import secrets
                random_password = secrets.token_urlsafe(32)
                user, error = create_user(firebase_email, firebase_name, random_password)
                if error:
                    return jsonify({'error': f'Failed to create user: {error}'}), 500
            
            # Create session
            token = create_session(user.id)
            
            return jsonify({
                'success': True,
                'token': token,
                'user': user.to_dict()
            }), 200
            
        except ImportError:
            # Fallback: Verify token using Firebase REST API
            firebase_api_key = "AIzaSyDGTGU6WcGclC9GOQMIPYlG0_xU_K1Yn-c"
            verify_url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={firebase_api_key}"
            
            verify_response = requests.post(verify_url, json={'idToken': id_token}, timeout=10)
            
            if verify_response.status_code != 200:
                return jsonify({'error': 'Invalid Firebase token'}), 401
            
            firebase_user = verify_response.json().get('users', [{}])[0]
            firebase_email = firebase_user.get('email', '').lower().strip()
            firebase_name = firebase_user.get('displayName', '').strip() or firebase_email.split('@')[0]
            
            if not firebase_email:
                return jsonify({'error': 'Could not get email from Firebase'}), 400
            
            # Check if user exists
            user = get_user_by_email(firebase_email)
            
            if not user:
                import secrets
                random_password = secrets.token_urlsafe(32)
                user, error = create_user(firebase_email, firebase_name, random_password)
                if error:
                    return jsonify({'error': f'Failed to create user: {error}'}), 500
            
            # Create session
            token = create_session(user.id)
            
            return jsonify({
                'success': True,
                'token': token,
                'user': user.to_dict()
            }), 200
        
    except Exception as e:
        print(f"Error with Firebase auth: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    """Authenticate user with Google OAuth (Direct OAuth, no Firebase)"""
    try:
        data = request.json
        google_token = data.get('token', '').strip()
        user_info = data.get('userInfo', {})
        
        if not google_token and not user_info:
            return jsonify({'error': 'Google token or user info is required'}), 400
        
        # If user info is provided directly, use it
        if user_info and user_info.get('email'):
            google_email = user_info.get('email', '').lower().strip()
            google_name = user_info.get('name', '').strip() or user_info.get('given_name', '').strip() or google_email.split('@')[0]
        else:
            # Verify Google token and get user info
            google_user_info_url = f'https://www.googleapis.com/oauth2/v2/userinfo?access_token={google_token}'
            response = requests.get(google_user_info_url, timeout=10)
            
            if response.status_code != 200:
                # Try JWT token verification (ID token)
                tokeninfo_url = f'https://oauth2.googleapis.com/tokeninfo?id_token={google_token}'
                token_response = requests.get(tokeninfo_url, timeout=10)
                if token_response.status_code == 200:
                    token_data = token_response.json()
                    google_email = token_data.get('email', '').lower().strip()
                    google_name = token_data.get('name', '').strip() or token_data.get('given_name', '').strip() or google_email.split('@')[0]
                else:
                    return jsonify({'error': 'Invalid Google token'}), 401
            else:
                google_user = response.json()
                google_email = google_user.get('email', '').lower().strip()
                google_name = google_user.get('name', '').strip() or google_user.get('given_name', '').strip() or google_email.split('@')[0]
        
        if not google_email:
            return jsonify({'error': 'Could not get email from Google'}), 400
        
        # Check if user exists
        user = get_user_by_email(google_email)
        
        if not user:
            # Create new user with Google account
            import secrets
            random_password = secrets.token_urlsafe(32)
            user, error = create_user(google_email, google_name, random_password)
            if error:
                return jsonify({'error': f'Failed to create user: {error}'}), 500
        
        # Create session (30 days expiration)
        token = create_session(user.id, expires_in_days=30)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': user.to_dict(),
            'expires_in_days': 30
        }), 200
        
    except requests.exceptions.RequestException as e:
        print(f"Google API error: {e}")
        return jsonify({'error': 'Failed to verify Google token'}), 500
    except Exception as e:
        print(f"Error with Google auth: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def get_user_from_request():
    """Helper function to get current user from request token"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            # Try to get from request body or query params
            if request.is_json:
                token = request.json.get('token', '')
            if not token:
                token = request.args.get('token', '')
        
        if not token:
            return None
        
        session = get_session(token)
        if not session:
            return None
        
        user = get_user_by_id(session['user_id'])
        return user
    except:
        return None

def require_auth():
    """Decorator to require authentication for routes"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            user = get_user_from_request()
            if not user:
                # Check if it's an API request
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentication required', 'redirect': '/login.html'}), 401
                # For HTML pages, redirect to login
                return render_template('login.html', error='Please log in to access this page'), 401
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current authenticated user"""
    try:
        user = get_user_from_request()
        if not user:
            # Return 200 with success: false instead of 401 for better frontend handling
            return jsonify({
                'success': False,
                'error': 'Not authenticated',
                'user': None
            }), 200
        
        # Include style profile (DNA) if available
        style_profile = get_style_profile(user.id)
        
        # Get user profile (stats)
        user_profile = get_user_profile(user.id)
        profile_dict = None
        if user_profile:
            profile_dict = user_profile.to_dict()
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'has_style_profile': style_profile is not None,
            'style_profile': style_profile,  # Style DNA data
            'user_profile': profile_dict  # User stats (interactions, acceptance rate, etc.)
        }), 200
        
    except Exception as e:
        print(f"Error getting current user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-style-profile', methods=['GET'])
def get_style_profile_endpoint():
    """Get user's stored style profile (DNA)"""
    try:
        user = get_user_from_request()
        if not user:
            # Return 200 with success: false instead of 401 for better frontend handling
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'style_profile': None
            }), 200
        
        style_profile = get_style_profile(user.id)
        if not style_profile:
            # Return 200 with success: false instead of 404 for better frontend handling
            return jsonify({
                'success': False,
                'error': 'No style profile found. Please upload code first to analyze your style.',
                'style_profile': None
            }), 200
        
        return jsonify({
            'success': True,
            'style_profile': style_profile
        }), 200
        
    except Exception as e:
        print(f"Error getting style profile: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/save-style-profile', methods=['POST'])
def save_style_profile_endpoint():
    """Save or update user's style profile (DNA) - authentication optional"""
    try:
        user = get_user_from_request()
        data = request.json
        style_profile = data.get('style_profile', {})
        
        if not style_profile:
            return jsonify({'error': 'Style profile is required'}), 400
        
        # Save to database if authenticated
        if user:
            save_style_profile(user.id, style_profile)
            return jsonify({
                'success': True,
                'message': 'Style profile saved successfully to your account'
            }), 200
        else:
            # Not authenticated - just return success (frontend will save to localStorage)
            return jsonify({
                'success': True,
                'message': 'Style profile saved to local storage'
            }), 200
        
    except Exception as e:
        print(f"Error saving style profile: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/file-upload-progress', methods=['GET'])
def get_file_upload_progress():
    """Get progress of file upload analysis"""
    with progress_lock:
        # Use a session ID or default key
        session_id = request.args.get('session_id', 'default')
        progress = file_upload_progress.get(session_id, {'percent': 0, 'status': 'Starting...'})
    return jsonify(progress), 200

@app.route('/api/analyze-files', methods=['POST'])
def analyze_files():
    """Analyze uploaded code files (all languages) - authentication optional"""
    import time as time_module
    import uuid
    
    session_id = str(uuid.uuid4())[:8]  # Generate session ID for progress tracking
    
    try:
        # Initialize progress
        with progress_lock:
            file_upload_progress[session_id] = {'percent': 5, 'status': 'Reading files...'}
        
        # Authentication optional - get user if available
        user = get_user_from_request()
        
        files = request.files.getlist('files')
        
        if not files:
            with progress_lock:
                file_upload_progress.pop(session_id, None)
            return jsonify({'error': 'No files uploaded'}), 400
        
        with progress_lock:
            file_upload_progress[session_id] = {'percent': 10, 'status': f'Processing {len(files)} files...'}
        
        code_files = []
        # Common code file extensions (all languages)
        code_extensions = [
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
            '.m', '.sh', '.bash', '.html', '.css', '.scss', '.vue', '.svelte',
            '.dart', '.lua', '.pl', '.pm', '.sql'
        ]
        
        total_files = len(files)
        for idx, file in enumerate(files):
            filename = file.filename
            # Check if it's a code file
            if any(filename.lower().endswith(ext) for ext in code_extensions):
                try:
                    content = file.read().decode('utf-8')
                    language = get_language_from_extension('.' + filename.split('.')[-1] if '.' in filename else '')
                    if language == 'Unknown':
                        language = detect_language_from_content(filename, content)
                    
                    code_files.append({
                        'filename': filename,
                        'content': content,
                        'language': language
                    })
                    
                    # Update progress
                    progress_percent = 10 + int((idx + 1) / total_files * 30)  # 10-40% for reading files
                    with progress_lock:
                        file_upload_progress[session_id] = {
                            'percent': progress_percent,
                            'status': f'Reading file {idx + 1}/{total_files}: {filename}'
                        }
                except UnicodeDecodeError:
                    # Skip binary files
                    continue
        
        if not code_files:
            with progress_lock:
                file_upload_progress.pop(session_id, None)
            return jsonify({'error': 'No code files found. Please upload files with code file extensions.'}), 400
        
        with progress_lock:
            file_upload_progress[session_id] = {'percent': 45, 'status': 'Analyzing code patterns...'}
        
        # Analyze code (multi-language)
        if len(code_files) == 1 and code_files[0]['language'] == 'Python':
            # Use Python-specific analyzer for single Python file
            report = analyze_code_files(code_files)
        else:
            # Use multi-language analyzer
            report = analyze_all_languages(code_files)
        
        with progress_lock:
            file_upload_progress[session_id] = {'percent': 90, 'status': 'Finalizing results...'}
        
        # Save style profile to database if user is authenticated
        if user:
            save_style_profile(user.id, report)
            print(f"Style profile saved for user: {user.email}")
        
        with progress_lock:
            file_upload_progress[session_id] = {'percent': 100, 'status': 'Complete!'}
        
        # Clean up progress after a delay
        def cleanup_progress():
            time_module.sleep(2)
            with progress_lock:
                file_upload_progress.pop(session_id, None)
        
        import threading
        threading.Thread(target=cleanup_progress, daemon=True).start()
        
        return jsonify({
            'success': True,
            'report': report,
            'saved_to_profile': user is not None,
            'session_id': session_id  # Return session ID for progress tracking
        }), 200
        
    except Exception as e:
        print(f"Error analyzing files: {e}")
        import traceback
        traceback.print_exc()
        with progress_lock:
            file_upload_progress.pop(session_id, None)
        return jsonify({'error': str(e)}), 500


@app.route('/api/github-progress/<username>', methods=['GET'])
def get_github_progress(username):
    """Get progress of GitHub analysis for a username"""
    with progress_lock:
        progress = github_progress.get(username, {'percent': 0, 'status': 'Starting...'})
    return jsonify(progress), 200

@app.route('/api/analyze-github', methods=['POST'])
def analyze_github():
    """Analyze GitHub repositories (optimized for speed) - authentication optional"""
    import time as time_module
    start_time = time_module.time()
    
    try:
        # Authentication optional - get user if available
        user = get_user_from_request()
        
        data = request.json
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'error': 'GitHub username required'}), 400
        
        # Initialize progress
        with progress_lock:
            github_progress[username] = {'percent': 0, 'status': 'Starting analysis...'}
        
        print(f"Starting GitHub analysis for user: {username}")
        
        # Fetch repositories first for health analysis
        print(f"Fetching repositories for {username}...")
        with progress_lock:
            github_progress[username] = {'percent': 2, 'status': 'Connecting to GitHub...'}
        
        repos = fetch_user_repositories(username)
        
        # Check if user exists (repos will be empty if user not found)
        if not repos:
            with progress_lock:
                github_progress.pop(username, None)
            
            # Try to verify if user exists by checking GitHub API directly
            try:
                headers = get_github_headers()
                user_check_url = f"https://api.github.com/users/{username}"
                print(f"Checking if user exists: {user_check_url}")
                
                user_response = requests.get(user_check_url, timeout=10, headers=headers)
                print(f"User check response status: {user_response.status_code}")
                
                if user_response.status_code == 404:
                    error_data = user_response.json() if user_response.content else {}
                    error_msg = error_data.get('message', 'User not found')
                    print(f"User {username} not found: {error_msg}")
                    return jsonify({
                        'error': f'User "{username}" not found on GitHub.',
                        'details': {
                            'message': error_msg,
                            'url': f'https://github.com/{username}'
                        },
                        'suggestions': [
                            'Verify the GitHub username is correct (case-sensitive)',
                            'Check the username spelling',
                            f'Visit https://github.com/{username} to verify the account exists',
                            'GitHub usernames are case-sensitive - check capitalization'
                        ]
                    }), 404
                elif user_response.status_code == 200:
                    user_data = user_response.json()
                    public_repos = user_data.get('public_repos', 0)
                    total_repos = user_data.get('public_repos', 0) + user_data.get('total_private_repos', 0)
                    print(f"User {username} found: {public_repos} public repos, {total_repos} total repos")
                    
                    # Check if user has any repositories at all
                    if total_repos == 0:
                        return jsonify({
                            'error': f'User "{username}" found but has no repositories.',
                            'details': {
                                'username': username,
                                'public_repos_count': public_repos,
                                'total_repos_count': total_repos,
                                'account_url': user_data.get('html_url', f'https://github.com/{username}')
                            },
                            'suggestions': [
                                'The account exists but has no repositories yet',
                                f'Visit https://github.com/{username}?tab=repositories to check',
                                'Create a repository with code files to analyze'
                            ]
                        }), 404
                    elif public_repos == 0:
                        return jsonify({
                            'error': f'User "{username}" found but has no public repositories.',
                            'details': {
                                'username': username,
                                'public_repos_count': public_repos,
                                'total_repos_count': total_repos,
                                'account_url': user_data.get('html_url', f'https://github.com/{username}')
                            },
                            'suggestions': [
                                'The account only has private repositories',
                                'Add GITHUB_TOKEN to .env file to access private repositories',
                                'Make at least one repository public to analyze without a token',
                                f'Visit https://github.com/{username}?tab=repositories to check repositories'
                            ]
                        }), 404
                    else:
                        # User has public repos but we couldn't fetch them - might be an API issue
                        return jsonify({
                            'error': f'User "{username}" found with {public_repos} public repositories, but unable to fetch them.',
                            'details': {
                                'username': username,
                                'public_repos_count': public_repos,
                                'account_url': user_data.get('html_url', f'https://github.com/{username}')
                            },
                            'suggestions': [
                                'This might be a temporary GitHub API issue',
                                'Try again in a few moments',
                                f'Visit https://github.com/{username}?tab=repositories to verify repositories exist',
                                'Check if repositories are empty or contain only non-code files'
                            ]
                        }), 500
                elif user_response.status_code == 403:
                    error_data = user_response.json() if user_response.content else {}
                    error_msg = error_data.get('message', 'Access denied')
                    print(f"Access denied for user check: {error_msg}")
                    
                    # Check if it's a rate limit issue
                    rate_limit_info = {}
                    if 'X-RateLimit-Remaining' in user_response.headers:
                        remaining = user_response.headers.get('X-RateLimit-Remaining', '0')
                        limit = user_response.headers.get('X-RateLimit-Limit', '60')
                        reset_time = user_response.headers.get('X-RateLimit-Reset', '0')
                        rate_limit_info = {
                            'remaining': int(remaining),
                            'limit': int(limit),
                            'reset_time': int(reset_time)
                        }
                    
                    suggestions = []
                    if 'rate limit' in error_msg.lower() or rate_limit_info.get('remaining', 1) == 0:
                        suggestions = [
                            'GitHub API rate limit exceeded (60 requests/hour without token)',
                            'Add GITHUB_TOKEN to Render environment variables for 5000 requests/hour',
                            f'Rate limit resets at: {rate_limit_info.get("reset_time", "unknown")}',
                            'Wait a few minutes and try again',
                            'See RENDER_ENV_VARIABLES.md for setup instructions'
                        ]
                    else:
                        suggestions = [
                            'GitHub API access denied',
                            'Add GITHUB_TOKEN to Render environment variables',
                            'Wait a few minutes and try again',
                            'Check your internet connection'
                        ]
                    
                    return jsonify({
                        'error': f'Access denied when checking user "{username}".',
                        'details': {
                            'message': error_msg,
                            'status_code': 403,
                            'rate_limit': rate_limit_info
                        },
                        'suggestions': suggestions
                    }), 403
                else:
                    error_data = user_response.json() if user_response.content else {}
                    error_msg = error_data.get('message', 'Unknown error')
                    print(f"Unexpected status code {user_response.status_code}: {error_msg}")
                    return jsonify({
                        'error': f'Unable to verify user "{username}" on GitHub.',
                        'details': {
                            'status_code': user_response.status_code,
                            'message': error_msg,
                            'response_text': user_response.text[:200] if user_response.text else 'No response'
                        },
                        'suggestions': [
                            'Check your internet connection',
                            'Verify the GitHub username is correct',
                            'Try again in a few moments',
                            'GitHub API might be experiencing issues'
                        ]
                    }), 500
            except requests.exceptions.Timeout:
                print(f"Timeout checking user {username}")
                return jsonify({
                    'error': f'Request timed out while checking user "{username}".',
                    'suggestions': [
                        'Check your internet connection',
                        'Try again in a few moments',
                        'GitHub API might be slow or unavailable'
                    ]
                }), 504
            except requests.exceptions.RequestException as e:
                print(f"Request error checking user existence: {e}")
                return jsonify({
                    'error': f'Network error while checking user "{username}".',
                    'details': {
                        'error': str(e)
                    },
                    'suggestions': [
                        'Check your internet connection',
                        'Verify the GitHub username is correct',
                        'Try again in a few moments'
                    ]
                }), 500
            except Exception as e:
                print(f"Error checking user existence: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'error': f'Unable to verify user "{username}" on GitHub.',
                    'details': {
                        'error': str(e),
                        'error_type': type(e).__name__
                    },
                    'suggestions': [
                        'Verify the GitHub username is correct',
                        'Ensure the account has public repositories',
                        'If using a private account, make sure you\'re authenticated with a GitHub token',
                        'Check your internet connection',
                        'Try again in a few moments'
                    ]
                }), 500
        
        # Analyze repository health (good/bad patterns)
        health_report = None
        if repos:
            with progress_lock:
                github_progress[username] = {'percent': 5, 'status': 'Analyzing repository health...'}
            
            # Update progress during health analysis
            total_repos = len(repos)
            for i, repo_info in enumerate(repos):
                with progress_lock:
                    # 5% to 20% for health analysis (5% base + 15% for repos)
                    progress_pct = 5 + int((i / total_repos) * 15)
                    github_progress[username] = {
                        'percent': min(progress_pct, 20),
                        'status': f'Analyzing repository {i+1}/{total_repos}: {repo_info.get("name", "unknown")}...'
                    }
            
            health_report = analyze_github_profile_health(username, repos)
            print(f"Health analysis: {health_report['good_percentage']:.1f}% good, {health_report['bad_percentage']:.1f}% bad")
            
            with progress_lock:
                github_progress[username] = {'percent': 20, 'status': 'Health analysis complete. Fetching code files...'}
        
        # Fetch code files
        code_files = fetch_all_user_code_files(username, progress_key=username)
        
        fetch_time = time_module.time() - start_time
        print(f"Found {len(code_files)} code files to analyze (fetched in {fetch_time:.1f}s)")
        
        # Log repository details for debugging
        if repos:
            print(f"Repositories checked: {[repo.get('name', 'unknown') for repo in repos]}")
            print(f"Total repositories: {len(repos)}")
        
        if not code_files and not health_report:
            with progress_lock:
                github_progress.pop(username, None)
            
            # Provide detailed error message
            repo_count = len(repos) if repos else 0
            return jsonify({
                'error': f'No code files found in {username}\'s repositories.',
                'details': {
                    'repositories_found': repo_count,
                    'repositories_checked': [repo.get('name', 'unknown') for repo in repos[:5]] if repos else [],
                    'possible_reasons': [
                        'Repositories might be empty',
                        'Repositories might only contain non-code files (images, docs, etc.)',
                        'Code files might be in private repositories (requires GitHub token)',
                        'Code files might be in subdirectories deeper than 4 levels',
                        'Repositories might only contain binary files or large files (>50KB)'
                    ]
                },
                'suggestions': [
                    'Ensure repositories contain code files (Python, JavaScript, Java, etc.)',
                    'Check if repositories are public or authenticate with a GitHub token for private repos',
                    'Verify repositories have code files in the root or common directories'
                ]
            }), 404
        
        # Analyze code content for bad patterns
        if code_files:
            code_content_analysis = analyze_code_content(code_files)
            if health_report:
                health_report['bad_patterns'].extend(code_content_analysis['bad_patterns'])
                health_report['bad_score'] += code_content_analysis['bad_score']
                # Recalculate percentages
                total_score = health_report['good_score'] + health_report['bad_score']
                if total_score > 0:
                    health_report['good_percentage'] = round((health_report['good_score'] / total_score) * 100, 1)
                    health_report['bad_percentage'] = round((health_report['bad_score'] / total_score) * 100, 1)
                health_report['health_score'] = round(100 - health_report['bad_percentage'], 1)
        
        # Calculate language percentages
        language_percentages = calculate_language_percentages(code_files) if code_files else {}
        
        # Analyze code (multi-language)
        report = {}
        if code_files:
            print(f"Analyzing {len(code_files)} files across multiple languages...")
            with progress_lock:
                github_progress[username] = {'percent': 60, 'status': f'Analyzing {len(code_files)} files...'}
            
            # Detect if mostly Python or multi-language
            python_files = [f for f in code_files if f.get('language') == 'Python']
            if len(python_files) == len(code_files) and len(code_files) > 0:
                # All Python files - use Python analyzer
                report = analyze_code_files(code_files)
            else:
                # Multi-language - use multi-language analyzer
                report = analyze_all_languages(code_files)
            
            report['files_analyzed'] = len(code_files)
            
            with progress_lock:
                github_progress[username] = {'percent': 75, 'status': 'Code analysis complete. Generating AI suggestions...'}
        
        with progress_lock:
            github_progress[username] = {'percent': 80, 'status': 'Generating AI suggestions...'}
        
        # Generate AI suggestions based on health report
        ai_suggestions = None
        if health_report and ai_engine:
            try:
                suggestions_prompt = f"""Analyze this GitHub profile health report and provide actionable suggestions.

Good Patterns Found: {len(health_report.get('good_patterns', []))}
Bad Patterns Found: {len(health_report.get('bad_patterns', []))}
Health Score: {health_report.get('health_score', 0)}/100
Good Percentage: {health_report.get('good_percentage', 0)}%
Bad Percentage: {health_report.get('bad_percentage', 0)}%

Good Patterns:
{chr(10).join([f"- {p.get('description', '')} ({p.get('category', '')})" for p in health_report.get('good_patterns', [])[:10]])}

Bad Patterns:
{chr(10).join([f"- {p.get('description', '')} ({p.get('category', '')})" for p in health_report.get('bad_patterns', [])[:10]])}

Languages Used: {', '.join([f"{lang} ({pct}%)" for lang, pct in language_percentages.items()])}

Provide:
1. A brief summary of the profile health
2. Top 5 actionable suggestions to improve
3. A roadmap to address bad patterns
4. How to enhance good patterns further

Format as JSON:
{{
  "summary": "brief summary",
  "suggestions": ["suggestion 1", "suggestion 2", ...],
  "roadmap": ["step 1", "step 2", ...],
  "enhancements": ["enhancement 1", "enhancement 2", ...]
}}"""
                
                try:
                    ai_response = ai_engine.client.chat.completions.create(
                        model=ai_engine.model,
                        messages=[{"role": "user", "content": suggestions_prompt}],
                        temperature=0.7,
                        max_tokens=2048
                    )
                except:
                    # Try fallback model
                    ai_response = ai_engine.client.chat.completions.create(
                        model=ai_engine.fallback_model,
                        messages=[{"role": "user", "content": suggestions_prompt}],
                        temperature=0.7,
                        max_tokens=2048
                    )
                
                import json
                import re
                text = ai_response.choices[0].message.content.strip()
                text = re.sub(r'```json\s*', '', text)
                text = re.sub(r'```\s*', '', text)
                ai_suggestions = json.loads(text)
            except Exception as e:
                print(f"Error generating AI suggestions: {e}")
                ai_suggestions = {
                    "summary": f"Profile health: {health_report.get('health_score', 0)}/100",
                    "suggestions": ["Review and fix bad patterns", "Add missing documentation", "Set up CI/CD", "Add security scanning", "Improve code structure"],
                    "roadmap": ["Fix critical issues first", "Add missing files", "Set up automation", "Improve code quality", "Enhance security"],
                    "enhancements": ["Add more documentation", "Set up automated testing", "Improve code structure", "Add code quality tools"]
                }
        
        with progress_lock:
            github_progress[username] = {'percent': 90, 'status': 'Finalizing results...'}
        
        # Combine all data
        report['language_percentages'] = language_percentages
        report['health_report'] = health_report
        report['ai_suggestions'] = ai_suggestions
        
        total_time = time_module.time() - start_time
        
        print(f"Analysis complete in {total_time:.1f}s. Quality score: {report.get('code_quality_score', 'N/A')}")
        
        # Save style profile and health report to database if user is authenticated
        user = get_user_from_request()
        if user:
            save_style_profile(user.id, report)
            # Save health report to user profile
            if health_report:
                user_profile = get_user_profile(user.id)
                if user_profile:
                    user_profile.github_health_report = health_report
                    print(f"GitHub health report saved for user: {user.email}")
            print(f"Style profile saved for user: {user.email}")
        
        # Set progress to 100% before clearing
        with progress_lock:
            github_progress[username] = {'percent': 100, 'status': 'Analysis complete!'}
            # Keep progress for a moment so frontend can see 100%
            import time
            time.sleep(0.5)
            github_progress.pop(username, None)
        
        return jsonify({
            'success': True,
            'report': report,
            'analysis_time': round(total_time, 1),
            'saved_to_profile': user is not None
        }), 200
        
    except requests.exceptions.Timeout:
        print(f"Timeout while fetching GitHub data for {username}")
        with progress_lock:
            github_progress.pop(username, None)
        return jsonify({'error': 'Request timed out. The user may have too many repositories. Try again or contact support.'}), 504
    except requests.exceptions.RequestException as e:
        print(f"GitHub API error: {e}")
        with progress_lock:
            github_progress.pop(username, None)
        return jsonify({'error': f'GitHub API error: {str(e)}'}), 500
    except Exception as e:
        print(f"Error analyzing GitHub: {e}")
        import traceback
        traceback.print_exc()
        with progress_lock:
            github_progress.pop(username, None)
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/api/suggest', methods=['POST'])
def get_suggestion():
    """Get AI suggestion matching user's style (automatically uses stored DNA) - authentication optional"""
    try:
        # Authentication optional - get user if available
        user = get_user_from_request()
        
        data = request.json
        code = data.get('code', '')
        filename = data.get('filename', 'untitled.py')
        
        if not code:
            return jsonify({'error': 'Code required'}), 400
        
        if not ai_engine:
            return jsonify({'error': 'AI engine not initialized. Please check GROQ_API_KEY.'}), 500
        
        # Get style profile from database (automatically use stored DNA)
        style_profile = None
        
        if user:
            stored_profile = get_style_profile(user.id)
            if stored_profile:
                style_profile = stored_profile
                print(f"Using stored style profile (DNA) for user: {user.email}")
            else:
                # Try to get from request body as fallback
                style_profile = data.get('style_profile', {})
                if style_profile:
                    # Save it for future use
                    save_style_profile(user.id, style_profile)
                    print(f"Saved style profile from request for user: {user.email}")
        else:
            # Not authenticated - use provided profile
            style_profile = data.get('style_profile', {})
        
        if not style_profile:
            return jsonify({'error': 'Style profile required. Please upload code first to analyze your style, or log in to use your stored profile.'}), 400
        
        # Get AI suggestion with context (using user's DNA)
        suggestion = ai_engine.suggest_improvement(code, style_profile, filename)
        
        # If teaching moment is missing, generate it
        if suggestion.get('has_suggestion') and not suggestion.get('teaching'):
            try:
                teaching = ai_engine.generate_teaching_moment(code, style_profile, suggestion.get('improved_code'))
                suggestion['teaching'] = teaching
            except Exception as e:
                print(f"Error generating teaching moment: {e}")
                # Continue without teaching moment
        
        return jsonify({
            'success': True,
            'suggestion': suggestion
        }), 200
        
    except Exception as e:
        print(f"Error getting suggestion: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-code', methods=['POST'])
def generate_code():
    """Generate code based on user request matching their style (automatically uses stored DNA) - authentication optional"""
    try:
        # Authentication optional - get user if available
        user = get_user_from_request()
        
        data = request.json
        user_request = data.get('request', '').strip()
        language = data.get('language', 'python')
        template = data.get('template', None)
        tech_stack = data.get('tech_stack', '')
        
        if not user_request:
            return jsonify({'error': 'Request is required'}), 400
        
        if not ai_engine:
            return jsonify({'error': 'AI engine not initialized. Please check GROQ_API_KEY.'}), 500
        
        # Get style profile from database (automatically use stored DNA)
        style_profile = None
        health_report = None
        github_issues = []
        
        if user:
            stored_profile = get_style_profile(user.id)
            if stored_profile:
                style_profile = stored_profile
                print(f"Using stored style profile (DNA) for user: {user.email}")
            
            # Get GitHub health report if available
            try:
                user_profile = get_user_profile(user.id)
                if user_profile and hasattr(user_profile, 'github_health_report') and user_profile.github_health_report:
                    health_report = user_profile.github_health_report
                    # Extract bad patterns/issues to fix
                    bad_patterns = health_report.get('bad_patterns', [])
                    github_issues = [
                        f"{p.get('description', '')} ({p.get('category', 'Unknown')})"
                        for p in bad_patterns[:20]  # Top 20 issues
                    ]
                    print(f"Found {len(github_issues)} GitHub health issues to address")
            except Exception as e:
                print(f"Error fetching GitHub health report: {e}")
            
            if not style_profile:
                # Try to get from request body as fallback
                style_profile = data.get('style_profile', {})
                if style_profile:
                    # Save it for future use
                    save_style_profile(user.id, style_profile)
                    print(f"Saved style profile from request for user: {user.email}")
        else:
            # Not authenticated - use provided profile
            style_profile = data.get('style_profile', {})
            # Try to get health report from request
            if data.get('health_report'):
                health_report = data.get('health_report')
                bad_patterns = health_report.get('bad_patterns', [])
                github_issues = [
                    f"{p.get('description', '')} ({p.get('category', 'Unknown')})"
                    for p in bad_patterns[:20]
                ]
        
        # If no style profile, use a default one for basic code generation
        if not style_profile:
            style_profile = {
                'naming_style': 'snake_case',
                'documentation_percentage': 30,
                'primary_language': language,
                'indentation': 4,
                'line_length': 80,
                'prefer_comprehensions': True,
                'use_type_hints': False
            }
            print("No style profile found, using default style profile")
        
        # Enhance request with GitHub health issues
        enhanced_request = user_request
        if github_issues:
            issues_text = "\n".join([f"- {issue}" for issue in github_issues])
            enhanced_request = f"""{user_request}

IMPORTANT: Address these GitHub health issues in the generated code:
{issues_text}

Generate code that:
1. Fixes all the issues listed above
2. Follows best practices to prevent these issues
3. Includes proper documentation, error handling, and structure
4. Is production-ready and follows industry standards"""
        
        print(f"Generating code for request: {user_request[:50]}...")
        print(f"  Language: {language}, Template: {template}, Tech Stack: {tech_stack}")
        print(f"  Using style profile: {style_profile.get('naming_style', 'default')} naming, {style_profile.get('documentation_percentage', 0)}% docs")
        if github_issues:
            print(f"  Addressing {len(github_issues)} GitHub health issues")
        
        # Get preferred language from style profile or use provided language
        preferred_language = style_profile.get('primary_language') or language
        
        # Generate code using AI (with style matching and health issues)
        try:
            result = ai_engine.generate_code(
                enhanced_request, 
                style_profile, 
                preferred_language,
                template=template,
                tech_stack=tech_stack
            )
        except Exception as ai_error:
            print(f"AI Engine Error: {ai_error}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'AI generation failed: {str(ai_error)}. Please check your API key and try again.'
            }), 500
        
        if not result:
            return jsonify({
                'success': False,
                'error': 'AI engine returned no result. Please try again.'
            }), 500
        
        if not result.get('code') and not result.get('files'):
            error_msg = result.get('explanation', 'Unable to generate code')
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
        
        # Check if multi-file generation
        if result.get('files') and isinstance(result.get('files'), list):
            return jsonify({
                'success': True,
                'files': result.get('files'),
                'explanation': result.get('explanation', 'Multi-file code generated'),
                'confidence': result.get('confidence', 0.0)
            }), 200
        
        # Single file generation
        return jsonify({
            'success': True,
            'code': result.get('code'),
            'explanation': result.get('explanation', 'Code generated'),
            'confidence': result.get('confidence', 0.0)
        }), 200
        
    except Exception as e:
        print(f"Error generating code: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/learn-from-interaction', methods=['POST'])
def learn_from_interaction():
    """Learn from beginner's code interactions - builds profile incrementally - authentication optional"""
    try:
        # Authentication optional - get user if available
        user = get_user_from_request()
        
        # If no user, return success but don't save profile
        if not user:
            return jsonify({
                'success': True,
                'message': 'Feedback received (login to save profile)',
                'saved': False
            }), 200
        
        data = request.json
        user_code = data.get('code', '').strip()
        selected_style = data.get('selected_style', '')  # Which style option they chose
        style_options = data.get('style_options', [])  # The options shown to them
        
        if not user_code:
            return jsonify({'error': 'Code is required'}), 400
        
        # Get or create profile
        current_profile = get_style_profile(user.id)
        if not current_profile:
            # Create a default beginner profile
            current_profile = {
                'naming_style': 'snake_case',
                'naming_confidence': 0.0,
                'documentation_percentage': 0.0,
                'type_hints_percentage': 0.0,
                'error_handling_style': 'basic',
                'code_quality_score': 50,
                'interactions': 0,
                'is_beginner_mode': True
            }
        
        # Update profile based on user's choice
        updated_profile = current_profile.copy()
        updated_profile['interactions'] = updated_profile.get('interactions', 0) + 1
        
        # Analyze the selected style to learn preferences
        if selected_style and style_options:
            selected_code = None
            for option in style_options:
                if option.get('id') == selected_style or option.get('label') == selected_style:
                    selected_code = option.get('code', '')
                    break
            
            if selected_code:
                # Learn from the choice
                # Check for descriptive names
                if len(selected_code.split('def ')[1].split('(')[0].strip()) > 5:
                    # Descriptive function name
                    updated_profile['naming_style'] = 'descriptive_snake_case'
                    updated_profile['naming_confidence'] = min(
                        updated_profile.get('naming_confidence', 0) + 10, 100
                    )
                
                # Check for docstrings
                if '"""' in selected_code or "'''" in selected_code:
                    updated_profile['documentation_percentage'] = min(
                        updated_profile.get('documentation_percentage', 0) + 10, 100
                    )
                
                # Check for type hints
                if ': ' in selected_code and 'def ' in selected_code:
                    updated_profile['type_hints_percentage'] = min(
                        updated_profile.get('type_hints_percentage', 0) + 10, 100
                    )
                
                # Check for error handling
                if 'try:' in selected_code and 'except' in selected_code:
                    updated_profile['error_handling_style'] = 'try_except'
        
        # Calculate confidence based on interactions
        interactions = updated_profile.get('interactions', 0)
        updated_profile['confidence'] = min(interactions / 10.0, 1.0)
        
        # Update quality score based on learning
        if interactions > 0:
            base_score = updated_profile.get('code_quality_score', 50)
            updated_profile['code_quality_score'] = min(base_score + (interactions * 2), 100)
        
        # Save updated profile
        save_style_profile(user.id, updated_profile)
        
        return jsonify({
            'success': True,
            'profile': updated_profile,
            'interactions': interactions,
            'confidence': updated_profile['confidence'],
            'message': f'Learned from your choice! ({interactions} interactions so far)'
        }), 200
        
    except Exception as e:
        print(f"Error learning from interaction: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-beginner-suggestions', methods=['POST'])
def get_beginner_suggestions():
    """Get multiple style suggestions for beginners to choose from"""
    try:
        data = request.json
        user_code = data.get('code', '').strip()
        filename = data.get('filename', 'untitled.py')
        
        if not user_code:
            return jsonify({'error': 'Code is required'}), 400
        
        if not ai_engine:
            return jsonify({'error': 'AI engine not initialized'}), 500
        
        # Get user's current profile (if any) - use stored DNA
        user = get_user_from_request()
        current_profile = None
        if user:
            current_profile = get_style_profile(user.id)
            if current_profile:
                print(f"Using stored style profile (DNA) for beginner suggestions: {user.email}")
        
        # Generate 2-3 style options for the user to choose from
        # If user has stored patterns, incorporate them into suggestions
        # Option A: Concise/Simple (or match their style if they prefer concise)
        # Option B: Descriptive/Well-documented (or match their style if they prefer descriptive)
        # Option C: Professional/Type-hinted (if code is complex enough or they use type hints)
        
        options = []
        
        # Build style context if profile exists
        style_hint = ""
        if current_profile:
            naming = current_profile.get('naming_style', 'snake_case')
            docs = current_profile.get('documentation_percentage', 0)
            type_hints = current_profile.get('type_hints_percentage', 0)
            style_hint = f"\n\nNote: This user typically uses {naming} naming, {docs}% documentation, {type_hints}% type hints. Match their style when possible."
        
        # Option A: Concise (or match their style if they prefer concise)
        concise_prompt = f"""Improve this code to be concise and simple:{style_hint}

{user_code}

Return ONLY the improved code, no explanations."""
        
        try:
            concise_result = ai_engine.client.generate_content(concise_prompt)
            concise_code = concise_result.text.strip()
            # Remove markdown code blocks if present
            if concise_code.startswith('```'):
                concise_code = '\n'.join(concise_code.split('\n')[1:-1])
            
            options.append({
                'id': 'A',
                'label': 'Concise & Simple',
                'code': concise_code,
                'description': 'Short and to the point'
            })
        except:
            pass
        
        # Option B: Descriptive
        descriptive_prompt = f"""Improve this code to be descriptive and well-documented:

{user_code}

Return ONLY the improved code with:
- Descriptive function/variable names
- Docstring explaining what it does
- Clear comments where helpful
No explanations, just code."""
        
        try:
            descriptive_result = ai_engine.client.generate_content(descriptive_prompt)
            descriptive_code = descriptive_result.text.strip()
            if descriptive_code.startswith('```'):
                descriptive_code = '\n'.join(descriptive_code.split('\n')[1:-1])
            
            options.append({
                'id': 'B',
                'label': 'Descriptive & Clear',
                'code': descriptive_code,
                'description': 'Well-documented and easy to understand'
            })
        except:
            pass
        
        # Option C: Professional (if code is complex enough)
        if len(user_code.split('\n')) > 5:
            professional_prompt = f"""Improve this code to be professional and production-ready:

{user_code}

Return ONLY the improved code with:
- Type hints (if Python)
- Error handling
- Docstrings
- Best practices
No explanations, just code."""
            
            try:
                professional_result = ai_engine.client.generate_content(professional_prompt)
                professional_code = professional_result.text.strip()
                if professional_code.startswith('```'):
                    professional_code = '\n'.join(professional_code.split('\n')[1:-1])
                
                options.append({
                    'id': 'C',
                    'label': 'Professional & Complete',
                    'code': professional_code,
                    'description': 'Production-ready with error handling'
                })
            except:
                pass
        
        if not options:
            return jsonify({'error': 'Could not generate suggestions'}), 500
        
        return jsonify({
            'success': True,
            'options': options,
            'message': 'Choose the style that feels right to you!'
        }), 200
        
    except Exception as e:
        print(f"Error getting beginner suggestions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
def handle_feedback():
    """Learn from user's accept/reject feedback"""
    try:
        data = request.json
        user_code = data.get('user_code', '')
        suggestion = data.get('suggestion', '')
        action = data.get('action', '')  # 'accept' or 'reject'
        current_profile = data.get('style_profile', {})
        
        if not action or action not in ['accept', 'reject']:
            return jsonify({'error': 'Action must be "accept" or "reject"'}), 400
        
        # Get user from request (optional)
        user = get_user_from_request()
        
        # If no user, return success but don't save profile
        if not user:
            return jsonify({
                'success': True,
                'message': 'Feedback received (login to save profile)',
                'saved': False
            }), 200
        
        # Get current style profile from database
        if not current_profile:
            current_profile = get_style_profile(user.id)
            if not current_profile:
                # Try to get from request body as fallback
                current_profile = data.get('style_profile', {})
                if not current_profile:
                    return jsonify({'error': 'Style profile required. Please analyze code first.'}), 400
        
        # Analyze the suggestion to extract patterns
        if action == 'accept' and suggestion:
            # User accepted → they like this pattern
            # Note: We'll do simple pattern matching instead of full AST analysis for speed
            
            # Update profile based on accepted suggestion
            updated_profile = current_profile.copy()
            
            # If suggestion has docstring and user code doesn't, increase doc preference
            if '"""' in suggestion or "'''" in suggestion:
                if '"""' not in user_code and "'''" not in user_code:
                    updated_profile['documentation_percentage'] = min(
                        updated_profile.get('documentation_percentage', 0) + 5, 100
                    )
            
            # If suggestion has type hints and user code doesn't, increase type hint preference
            if ': ' in suggestion and 'def ' in suggestion:
                if ': ' not in user_code.split('def ')[1:]:
                    updated_profile['type_hints_percentage'] = min(
                        updated_profile.get('type_hints_percentage', 0) + 3, 100
                    )
            
            # If suggestion has try/except and user code doesn't, update error handling
            if 'try:' in suggestion and 'except' in suggestion:
                if 'try:' not in user_code:
                    updated_profile['error_handling_style'] = 'try_except'
            
            # Recalculate quality score (slight increase for accepting good suggestions)
            updated_profile['code_quality_score'] = min(
                updated_profile.get('code_quality_score', 50) + 1, 100
            )
            
            return jsonify({
                'success': True,
                'updated_profile': updated_profile,
                'message': '✅ Great! I learned from this and updated your profile.'
            }), 200
        
        elif action == 'reject':
            # User rejected → they don't like this pattern
            # We could track this to avoid similar suggestions, but for now just acknowledge
            return jsonify({
                'success': True,
                'updated_profile': current_profile,
                'message': 'Noted! I\'ll avoid similar patterns in the future.'
            }), 200
        
    except Exception as e:
        print(f"Error handling feedback: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/export-github-health-pdf', methods=['POST'])
def export_github_health_pdf():
    """Export GitHub health report as PDF"""
    try:
        from pdf_generator import generate_health_report_pdf
        
        data = request.json
        health_data = data.get('health_data', {})
        
        if not health_data:
            return jsonify({'error': 'Health data required'}), 400
        
        # Generate PDF
        pdf_bytes = generate_health_report_pdf(health_data)
        
        # Return PDF as download
        response = Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=github-health-report-{health_data.get("username", "user")}.pdf'
            }
        )
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-style-guide', methods=['POST'])
def export_style_guide():
    """Export user's style guide as markdown - returns file for download"""
    try:
        from datetime import datetime
        from flask import Response
        
        # Try to get style profile from request body
        profile = request.json.get('style_profile', {}) if request.json else {}
        
        # If not provided, try to get from user's stored profile
        if not profile:
            user = get_user_from_request()
            if user:
                stored_profile = get_style_profile(user.id)
                if stored_profile:
                    profile = stored_profile
        
        # If still no profile, return error
        if not profile:
            return jsonify({'error': 'Style profile required. Please upload code first or provide style_profile in request.'}), 400
        
        # Generate markdown style guide
        guide = f"""# My Coding Style Guide
Generated by CodeMind

## 📊 Overview

This style guide was automatically extracted from your codebase analysis.

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 🏷️ Naming Conventions

- **Style**: {profile.get('naming_style', 'snake_case')}
- **Confidence**: {profile.get('naming_confidence', 0):.0f}%

**Examples:**
- Functions: `{profile.get('naming_style', 'snake_case').replace('_', '_')}`
- Variables: `{profile.get('naming_style', 'snake_case').replace('_', '_')}`

---

## 📝 Documentation

- **Coverage**: {profile.get('documentation_percentage', 0):.0f}% of functions documented
- **Style**: {"Comprehensive docstrings" if profile.get('documentation_percentage', 0) > 50 else "Minimal documentation"}

**Preference:** {"Include docstrings for all functions" if profile.get('documentation_percentage', 0) > 50 else "Document only when necessary"}

---

## 🔤 Type Hints

- **Usage**: {profile.get('type_hints_percentage', 0):.0f}%
- **Preference**: {"Use type hints extensively" if profile.get('type_hints_percentage', 0) > 50 else "Minimal type hint usage"}

---

## ⚠️ Error Handling

- **Preferred Method**: {profile.get('error_handling_style', 'basic')}
- **Pattern**: {"Try/except blocks" if profile.get('error_handling_style', 'basic') == 'try_except' else "Basic error handling"}

---

## ⭐ Code Quality Score

**{profile.get('code_quality_score', 50)}/100**

This score is based on:
- Code consistency
- Best practices adherence
- Documentation quality
- Error handling patterns

---

## 💡 Recommendations

Based on your current style:

1. **Naming**: Continue using {profile.get('naming_style', 'snake_case')} consistently
2. **Documentation**: {"Consider adding more docstrings" if profile.get('documentation_percentage', 0) < 50 else "Great documentation coverage!"}
3. **Type Hints**: {"Consider adding type hints for better code clarity" if profile.get('type_hints_percentage', 0) < 30 else "Good type hint usage"}
4. **Error Handling**: {"Consider using try/except blocks for better error handling" if profile.get('error_handling_style', 'basic') != 'try_except' else "Good error handling patterns"}

---

*This style guide is automatically generated and reflects your current coding patterns. It will evolve as you code!*

"""
        
        # Return file directly for download (avoids blob URL warning on HTTP)
        filename = f"codemind-style-guide-{datetime.now().strftime('%Y%m%d')}.md"
        response = Response(
            guide,
            mimetype='text/markdown',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'text/markdown; charset=utf-8'
            }
        )
        return response
        
    except Exception as e:
        print(f"Error exporting style guide: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok'}), 200


# ==========================================
# FRONTEND ROUTES
# ==========================================

@app.route('/')
def index():
    """Serve index.html"""
    return render_template('index.html')


@app.route('/index.html')
def index_html():
    """Serve index.html (alternative route)"""
    return render_template('index.html')


@app.route('/upload.html')
def upload():
    """Serve upload.html - authentication required (enforced by frontend)"""
    return render_template('upload.html')


@app.route('/editor.html')
def editor():
    """Serve editor.html - authentication required (enforced by frontend)"""
    return render_template('editor.html')


@app.route('/manifest.json')
def manifest():
    """Serve manifest.json"""
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')


@app.route('/icons/<path:filename>')
def icons(filename):
    """Serve icon files"""
    return send_from_directory('static/icons', filename)


@app.route('/favicon.ico')
def favicon():
    """Serve favicon.ico"""
    try:
        return send_from_directory('static/icons', 'icon-192x192.png', mimetype='image/png')
    except:
        # If icon doesn't exist, return 204 No Content to suppress 404
        return '', 204

# GitHub Integration Routes
@app.route('/api/github/connect', methods=['POST'])
def connect_github():
    """Connect GitHub account using OAuth token"""
    try:
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.json
        github_token = data.get('token', '').strip()
        github_username = data.get('username', '').strip()
        
        if not github_token:
            return jsonify({'error': 'GitHub token is required'}), 400
        
        # Verify token by making a test API call
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'CodeMind/1.0'
        }
        
        # Get user info from GitHub
        if not github_username:
            user_response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
            if user_response.status_code == 200:
                github_username = user_response.json().get('login', '')
            else:
                return jsonify({'error': 'Invalid GitHub token'}), 401
        
        # Store GitHub credentials in user profile
        user_profile = get_user_profile(user.id)
        if user_profile:
            user_profile.github_token = github_token
            user_profile.github_username = github_username
            user_profile.github_connected = True
            print(f"GitHub account connected for user: {user.email} (GitHub: {github_username})")
        
        return jsonify({
            'success': True,
            'message': f'GitHub account connected successfully',
            'username': github_username
        }), 200
        
    except Exception as e:
        print(f"Error connecting GitHub: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/github/disconnect', methods=['POST'])
def disconnect_github():
    """Disconnect GitHub account"""
    try:
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        user_profile = get_user_profile(user.id)
        if user_profile:
            user_profile.github_token = None
            user_profile.github_username = None
            user_profile.github_connected = False
        
        return jsonify({'success': True, 'message': 'GitHub account disconnected'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/github/create-repo', methods=['POST'])
def create_github_repo():
    """Create a new GitHub repository"""
    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({'error': 'JSON data required'}), 400
        
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if GitHub is connected
        user_profile = get_user_profile(user.id)
        if not user_profile:
            return jsonify({
                'error': 'User profile not found',
                'requires_connection': True
            }), 400
        
        if not user_profile.github_connected:
            return jsonify({
                'error': 'GitHub account not connected',
                'requires_connection': True
            }), 400
        
        if not user_profile.github_token:
            return jsonify({
                'error': 'GitHub token not found. Please reconnect your GitHub account.',
                'requires_connection': True
            }), 400
        
        data = request.json
        if not data:
            return jsonify({'error': 'Request data required'}), 400
        
        repo_name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        private = data.get('private', False)
        auto_init = data.get('auto_init', True)
        
        if not repo_name:
            return jsonify({'error': 'Repository name is required'}), 400
        
        # Validate repository name (GitHub rules: alphanumeric, hyphens, underscores, dots)
        if not re.match(r'^[a-zA-Z0-9._-]+$', repo_name):
            return jsonify({'error': 'Repository name can only contain alphanumeric characters, hyphens, underscores, and dots'}), 400
        
        github_token = user_profile.github_token
        github_username = user_profile.github_username
        
        # If username is not set, try to get it from GitHub API
        if not github_username:
            try:
                headers_temp = {
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'CodeMind/1.0'
                }
                user_response = requests.get('https://api.github.com/user', headers=headers_temp, timeout=10)
                if user_response.status_code == 200:
                    github_username = user_response.json().get('login', '')
                    if github_username:
                        user_profile.github_username = github_username
                else:
                    return jsonify({
                        'error': 'Failed to verify GitHub token. Please reconnect your GitHub account.',
                        'requires_connection': True
                    }), 400
            except Exception as e:
                print(f"Error fetching GitHub username: {e}")
                return jsonify({
                    'error': 'Failed to verify GitHub account. Please reconnect.',
                    'requires_connection': True
                }), 400
        
        if not github_username:
            return jsonify({
                'error': 'GitHub username not found. Please reconnect your GitHub account.',
                'requires_connection': True
            }), 400
        
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'CodeMind/1.0'
        }
        
        # Create repository
        repo_data = {
            'name': repo_name,
            'description': description,
            'private': private,
            'auto_init': auto_init
        }
        
        try:
            create_response = requests.post(
                'https://api.github.com/user/repos',
                headers=headers,
                json=repo_data,
                timeout=10
            )
        except requests.exceptions.Timeout:
            return jsonify({
                'error': 'Request to GitHub API timed out. Please try again.'
            }), 500
        except requests.exceptions.RequestException as e:
            print(f"GitHub API request error: {e}")
            return jsonify({
                'error': f'Failed to connect to GitHub API: {str(e)}'
            }), 500
        
        if create_response.status_code in [200, 201]:
            try:
                repo_info = create_response.json()
            except ValueError:
                return jsonify({
                    'error': 'Invalid response from GitHub API'
                }), 500
            
            return jsonify({
                'success': True,
                'message': f'Repository "{repo_name}" created successfully',
                'repo_name': repo_name,
                'repo_url': repo_info.get('html_url', f'https://github.com/{github_username}/{repo_name}'),
                'clone_url': repo_info.get('clone_url', ''),
                'ssh_url': repo_info.get('ssh_url', '')
            }), 200
        else:
            try:
                error_data = create_response.json() if create_response.text else {}
            except ValueError:
                error_data = {}
            
            error_message = error_data.get('message', 'Failed to create repository')
            
            # Handle specific GitHub errors
            if 'name already exists' in error_message.lower() or 'already exists' in error_message.lower():
                return jsonify({
                    'error': f'Repository "{repo_name}" already exists. Please choose a different name.'
                }), 400
            elif 'invalid' in error_message.lower():
                return jsonify({
                    'error': f'Invalid repository name: {error_message}'
                }), 400
            elif create_response.status_code == 401:
                return jsonify({
                    'error': 'GitHub token is invalid or expired. Please reconnect your GitHub account.',
                    'requires_connection': True
                }), 401
            elif create_response.status_code == 403:
                return jsonify({
                    'error': 'GitHub API rate limit exceeded or insufficient permissions. Please try again later.'
                }), 403
            
            return jsonify({
                'error': f'Failed to create repository: {error_message}',
                'status_code': create_response.status_code
            }), 500
        
    except Exception as e:
        print(f"Error creating GitHub repository: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'type': type(e).__name__
        }), 500

@app.route('/api/git/status', methods=['POST'])
def git_status():
    """Get Git status for current code"""
    try:
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if GitHub is connected
        user_profile = get_user_profile(user.id)
        if not user_profile or not user_profile.github_connected or not user_profile.github_token:
            return jsonify({
                'error': 'GitHub account not connected',
                'requires_connection': True
            }), 400
        
        data = request.json
        code = data.get('code', '')
        filename = data.get('filename', 'untitled.py')
        
        # For now, return a simple status
        # In a real implementation, you'd check git status
        return jsonify({
            'success': True,
            'status': 'clean',
            'message': 'No changes to commit',
            'files': [filename]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/git/commit', methods=['POST'])
def git_commit():
    """Commit code to GitHub repository"""
    try:
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if GitHub is connected
        user_profile = get_user_profile(user.id)
        if not user_profile or not user_profile.github_connected or not user_profile.github_token:
            return jsonify({
                'error': 'GitHub account not connected',
                'requires_connection': True
            }), 400
        
        data = request.json
        code = data.get('code', '')
        filename = data.get('filename', 'untitled.py')
        message = data.get('message', 'Update code')
        repo_name = data.get('repo', 'codemind-project')
        branch = data.get('branch', 'main')
        
        if not code:
            return jsonify({'error': 'Code is required'}), 400
        
        github_token = user_profile.github_token
        github_username = user_profile.github_username
        
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'CodeMind/1.0'
        }
        
        # Create or update file in repository
        # First, check if repo exists
        repo_url = f'https://api.github.com/repos/{github_username}/{repo_name}'
        repo_response = requests.get(repo_url, headers=headers, timeout=10)
        
        if repo_response.status_code == 404:
            # Create repository
            create_repo_response = requests.post(
                'https://api.github.com/user/repos',
                headers=headers,
                json={
                    'name': repo_name,
                    'private': False,
                    'auto_init': True
                },
                timeout=10
            )
            if create_repo_response.status_code not in [200, 201]:
                return jsonify({'error': 'Failed to create repository'}), 500
        
        # Get current file content (if exists)
        file_url = f'https://api.github.com/repos/{github_username}/{repo_name}/contents/{filename}'
        file_response = requests.get(file_url, headers=headers, timeout=10)
        
        sha = None
        if file_response.status_code == 200:
            sha = file_response.json().get('sha')
        
        # Create or update file
        import base64
        content_encoded = base64.b64encode(code.encode('utf-8')).decode('utf-8')
        
        file_data = {
            'message': message,
            'content': content_encoded,
            'branch': branch
        }
        if sha:
            file_data['sha'] = sha
        
        update_response = requests.put(file_url, headers=headers, json=file_data, timeout=10)
        
        if update_response.status_code in [200, 201]:
            commit_url = update_response.json().get('content', {}).get('html_url', '')
            return jsonify({
                'success': True,
                'message': f'Code committed successfully',
                'commit_url': commit_url,
                'repo_url': f'https://github.com/{github_username}/{repo_name}'
            }), 200
        else:
            return jsonify({
                'error': f'Failed to commit: {update_response.json().get("message", "Unknown error")}'
            }), 500
        
    except Exception as e:
        print(f"Error committing to GitHub: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/git/push', methods=['POST'])
def git_push():
    """Push changes to GitHub (for Git operations, this is handled by commit)"""
    try:
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        user_profile = get_user_profile(user.id)
        if not user_profile or not user_profile.github_connected:
            return jsonify({
                'error': 'GitHub account not connected',
                'requires_connection': True
            }), 400
        
        # Push is automatically handled by commit in GitHub API
        return jsonify({
            'success': True,
            'message': 'Changes pushed successfully (commits are automatically pushed)'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/git/pull', methods=['POST'])
def git_pull():
    """Pull latest changes from GitHub"""
    try:
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        user_profile = get_user_profile(user.id)
        if not user_profile or not user_profile.github_connected or not user_profile.github_token:
            return jsonify({
                'error': 'GitHub account not connected',
                'requires_connection': True
            }), 400
        
        data = request.json
        repo_name = data.get('repo', 'codemind-project')
        filename = data.get('filename', 'untitled.py')
        branch = data.get('branch', 'main')
        
        github_token = user_profile.github_token
        github_username = user_profile.github_username
        
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'CodeMind/1.0'
        }
        
        # Get file content from GitHub
        file_url = f'https://api.github.com/repos/{github_username}/{repo_name}/contents/{filename}?ref={branch}'
        file_response = requests.get(file_url, headers=headers, timeout=10)
        
        if file_response.status_code == 200:
            import base64
            file_data = file_response.json()
            content_encoded = file_data.get('content', '')
            content = base64.b64decode(content_encoded).decode('utf-8')
            
            return jsonify({
                'success': True,
                'code': content,
                'message': f'Pulled latest changes from {branch} branch'
            }), 200
        elif file_response.status_code == 404:
            return jsonify({
                'error': f'File {filename} not found in repository'
            }), 404
        else:
            return jsonify({
                'error': f'Failed to pull: {file_response.json().get("message", "Unknown error")}'
            }), 500
        
    except Exception as e:
        print(f"Error pulling from GitHub: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/login.html')
def login_page():
    """Serve login.html"""
    return render_template('login.html')


@app.route('/dashboard.html')
def dashboard():
    """Serve dashboard.html - requires authentication"""
    return render_template('dashboard.html')


@app.route('/register.html')
def register_page():
    """Serve register.html"""
    return render_template('register.html')


# Serve static files (CSS, JS, images)
@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    # Don't serve API routes as static files
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    
    # Try to serve from static folder
    try:
        return send_from_directory(app.static_folder, path)
    except:
        # If file not found, return 404
        return jsonify({'error': 'File not found', 'path': path}), 404


@app.route('/api/run-code', methods=['POST'])
def run_code():
    """Run code with automatic requirements installation"""
    try:
        # Check authentication
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        session = get_session(token)
        if not session:
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        data = request.json
        files = data.get('files', {})
        main_file = data.get('mainFile', 'main.py')
        current_file = data.get('currentFile', main_file)
        
        if not files or main_file not in files:
            return jsonify({'success': False, 'error': f'Main file "{main_file}" not found in files'}), 400
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='codemind_run_')
        output = []
        error_output = []
        install_output = []
        url = None
        
        try:
            # Write all files to temp directory
            for file_name, file_content in files.items():
                file_path = os.path.join(temp_dir, file_name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)
            
            # Detect language from main file
            main_ext = os.path.splitext(main_file)[1].lower()
            
            # Check for requirements files
            requirements_file = None
            if 'requirements.txt' in files:
                requirements_file = os.path.join(temp_dir, 'requirements.txt')
            elif 'package.json' in files:
                requirements_file = os.path.join(temp_dir, 'package.json')
            
            # Install requirements if exists
            if requirements_file and os.path.exists(requirements_file):
                if main_ext == '.py':
                    # Install Python requirements
                    install_output.append(f"Installing Python requirements from requirements.txt...")
                    try:
                        result = subprocess.run(
                            ['pip', 'install', '-r', requirements_file, '--quiet'],
                            cwd=temp_dir,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        if result.returncode == 0:
                            install_output.append("✓ Requirements installed successfully")
                        else:
                            install_output.append(f"⚠ Warning: {result.stderr}")
                    except subprocess.TimeoutExpired:
                        install_output.append("⚠ Installation timeout (continuing anyway)")
                    except Exception as e:
                        install_output.append(f"⚠ Installation warning: {str(e)}")
                elif main_ext in ['.js', '.ts']:
                    # Install Node.js dependencies
                    install_output.append(f"Installing Node.js dependencies from package.json...")
                    try:
                        result = subprocess.run(
                            ['npm', 'install', '--silent'],
                            cwd=temp_dir,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        if result.returncode == 0:
                            install_output.append("✓ Dependencies installed successfully")
                        else:
                            install_output.append(f"⚠ Warning: {result.stderr}")
                    except subprocess.TimeoutExpired:
                        install_output.append("⚠ Installation timeout (continuing anyway)")
                    except Exception as e:
                        install_output.append(f"⚠ Installation warning: {str(e)}")
            
            # Run the code
            main_path = os.path.join(temp_dir, main_file)
            
            if main_ext == '.py':
                # Run Python code
                result = subprocess.run(
                    ['python', main_path],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                output.append(result.stdout)
                if result.stderr:
                    error_output.append(result.stderr)
            
            elif main_ext in ['.js', '.ts']:
                # Run Node.js code
                result = subprocess.run(
                    ['node', main_path],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                output.append(result.stdout)
                if result.stderr:
                    error_output.append(result.stderr)
            
            # Check if it's a web app (Flask, Express, etc.)
            main_content = files.get(main_file, '')
            if 'app.run' in main_content or 'app.listen' in main_content or 'flask' in main_content.lower() or 'express' in main_content.lower():
                # Extract port from code or use default
                port_match = re.search(r'port[=\s:]+(\d+)', main_content, re.IGNORECASE)
                port = int(port_match.group(1)) if port_match else 5000
                
                # For web apps, we can't actually run them in subprocess easily
                # Instead, return a message that it's a web app
                output.append(f"\n🌐 Web application detected (port {port})")
                output.append(f"Note: Web applications need to be deployed to run. This is a code preview.")
                url = f"http://localhost:{port}"  # Informational only
            
            # Combine output
            full_output = '\n'.join(output) if output else ''
            full_error = '\n'.join(error_output) if error_output else None
            full_install = '\n'.join(install_output) if install_output else None
            
            return jsonify({
                'success': True,
                'output': full_output,
                'error': full_error,
                'installOutput': full_install,
                'url': url,
                'mainFile': main_file
            }), 200
            
        finally:
            # Cleanup temp directory
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Code execution timeout (30 seconds). Your code may be taking too long to run.'
        }), 408
    except Exception as e:
        import traceback
        print(f"Error running code: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Failed to run code: {str(e)}'
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    # For production, disable debug mode
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    # Enable debug mode to auto-reload templates
    app.config['DEBUG'] = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', port=port, debug=True)
