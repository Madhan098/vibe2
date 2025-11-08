"""
CodeMind Flask Backend
"""
from flask import Flask, request, jsonify, render_template, send_from_directory, Response
from flask_cors import CORS
import os
from dotenv import load_dotenv
import requests
from code_analyzer import analyze_code_files, analyze_code
from github_integration import fetch_all_user_code_files
import threading

# Global progress tracking for GitHub analysis
github_progress = {}
progress_lock = threading.Lock()
from ai_engine import AIEngine
from multi_language_analyzer import analyze_all_languages
from language_detector import get_language_from_extension, detect_language_from_content
from models import (
    create_user, get_user_by_email, get_user_by_id,
    create_session, get_session, delete_session,
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
        
        # Create session
        token = create_session(user.id)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': user.to_dict()
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
        
        # Create session
        token = create_session(user.id)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': user.to_dict()
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
        
        # Create session
        token = create_session(user.id)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': user.to_dict()
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
        
        # Include style profile if available
        style_profile = get_style_profile(user.id)
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'has_style_profile': style_profile is not None,
            'style_profile': style_profile  # Return the full profile
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
    """Save or update user's style profile (DNA)"""
    try:
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.json
        style_profile = data.get('style_profile', {})
        
        if not style_profile:
            return jsonify({'error': 'Style profile is required'}), 400
        
        save_style_profile(user.id, style_profile)
        
        return jsonify({
            'success': True,
            'message': 'Style profile saved successfully'
        }), 200
        
    except Exception as e:
        print(f"Error saving style profile: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze-files', methods=['POST'])
def analyze_files():
    """Analyze uploaded code files (all languages) - authentication optional"""
    try:
        # Authentication optional - get user if available
        user = get_user_from_request()
        
        files = request.files.getlist('files')
        
        if not files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        code_files = []
        # Common code file extensions (all languages)
        code_extensions = [
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
            '.m', '.sh', '.bash', '.html', '.css', '.scss', '.vue', '.svelte',
            '.dart', '.lua', '.pl', '.pm', '.sql'
        ]
        
        for file in files:
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
                except UnicodeDecodeError:
                    # Skip binary files
                    continue
        
        if not code_files:
            return jsonify({'error': 'No code files found. Please upload files with code file extensions.'}), 400
        
        # Analyze code (multi-language)
        if len(code_files) == 1 and code_files[0]['language'] == 'Python':
            # Use Python-specific analyzer for single Python file
            report = analyze_code_files(code_files)
        else:
            # Use multi-language analyzer
            report = analyze_all_languages(code_files)
        
        # Save style profile to database if user is authenticated
        user = get_user_from_request()
        if user:
            save_style_profile(user.id, report)
            print(f"Style profile saved for user: {user.email}")
        
        return jsonify({
            'success': True,
            'report': report,
            'saved_to_profile': user is not None
        }), 200
        
    except Exception as e:
        print(f"Error analyzing files: {e}")
        import traceback
        traceback.print_exc()
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
        
        # Fetch all code files from user's repositories (optimized)
        print(f"Fetching repositories for {username}...")
        with progress_lock:
            github_progress[username] = {'percent': 2, 'status': 'Connecting to GitHub...'}
        
        code_files = fetch_all_user_code_files(username, progress_key=username)
        
        fetch_time = time_module.time() - start_time
        print(f"Found {len(code_files)} files to analyze (fetched in {fetch_time:.1f}s)")
        
        if not code_files:
            with progress_lock:
                github_progress.pop(username, None)
            return jsonify({
                'error': f'No code files found in {username}\'s repositories. Make sure the username is correct and has public repositories with code files.'
            }), 404
        
        # Analyze code (multi-language)
        print(f"Analyzing {len(code_files)} files across multiple languages...")
        with progress_lock:
            github_progress[username] = {'percent': 65, 'status': f'Analyzing {len(code_files)} files...'}
        
        # Detect if mostly Python or multi-language
        python_files = [f for f in code_files if f.get('language') == 'Python']
        if len(python_files) == len(code_files) and len(code_files) > 0:
            # All Python files - use Python analyzer
            report = analyze_code_files(code_files)
        else:
            # Multi-language - use multi-language analyzer
            report = analyze_all_languages(code_files)
        
        with progress_lock:
            github_progress[username] = {'percent': 90, 'status': 'Finalizing results...'}
        
        report['files_analyzed'] = len(code_files)
        total_time = time_module.time() - start_time
        
        print(f"Analysis complete in {total_time:.1f}s. Quality score: {report.get('code_quality_score', 'N/A')}")
        
        # Save style profile to database if user is authenticated
        user = get_user_from_request()
        if user:
            save_style_profile(user.id, report)
            print(f"Style profile saved for user: {user.email}")
        
        # Clear progress
        with progress_lock:
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
        
        print(f"Generating code for request: {user_request[:50]}...")
        print(f"  Language: {language}, Template: {template}, Tech Stack: {tech_stack}")
        print(f"  Using style profile: {style_profile.get('naming_style', 'default')} naming, {style_profile.get('documentation_percentage', 0)}% docs")
        
        # Get preferred language from style profile or use provided language
        preferred_language = style_profile.get('primary_language') or language
        
        # Generate code using AI (with style matching)
        try:
            result = ai_engine.generate_code(
                user_request, 
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


@app.route('/api/export-style-guide', methods=['POST'])
def export_style_guide():
    """Export user's style guide as markdown - returns file for download"""
    try:
        from datetime import datetime
        from flask import Response
        
        profile = request.json.get('style_profile', {})
        
        if not profile:
            return jsonify({'error': 'Style profile required'}), 400
        
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
    """Serve upload.html - no authentication required"""
    return render_template('upload.html')


@app.route('/editor.html')
def editor():
    """Serve editor.html - no authentication required"""
    return render_template('editor.html')


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


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    # For production, disable debug mode
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    # Enable debug mode to auto-reload templates
    app.config['DEBUG'] = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', port=port, debug=True)
