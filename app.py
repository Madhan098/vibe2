"""
CodeMind Flask Backend
"""
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
from code_analyzer import analyze_code_files
from github_integration import fetch_all_user_code_files
from ai_engine import AIEngine

load_dotenv()

# Initialize Flask app with templates and static folders
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static',
            static_url_path='')

# CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize AI engine
ai_engine = AIEngine(api_key=os.getenv('GEMINI_API_KEY'))


# ==========================================
# API ROUTES
# ==========================================

@app.route('/api/analyze-files', methods=['POST'])
def analyze_files():
    """Analyze uploaded Python files"""
    try:
        files = request.files.getlist('files')
        
        if not files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        code_files = []
        for file in files:
            if file.filename.endswith('.py'):
                content = file.read().decode('utf-8')
                code_files.append({
                    'filename': file.filename,
                    'content': content
                })
        
        if not code_files:
            return jsonify({'error': 'No Python files found'}), 400
        
        # Analyze code
        report = analyze_code_files(code_files)
        
        return jsonify({
            'success': True,
            'report': report
        }), 200
        
    except Exception as e:
        print(f"Error analyzing files: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze-github', methods=['POST'])
def analyze_github():
    """Analyze GitHub repositories"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'error': 'GitHub username required'}), 400
        
        # Fetch all code files from user's repositories
        code_files = fetch_all_user_code_files(username)
        
        if not code_files:
            return jsonify({'error': f'No Python files found in {username}\'s repositories'}), 404
        
        # Analyze code
        report = analyze_code_files(code_files)
        report['files_analyzed'] = len(code_files)
        
        return jsonify({
            'success': True,
            'report': report
        }), 200
        
    except Exception as e:
        print(f"Error analyzing GitHub: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/suggest', methods=['POST'])
def get_suggestion():
    """Get AI suggestion matching user's style"""
    try:
        data = request.json
        code = data.get('code', '')
        style_profile = data.get('style_profile', {})
        
        if not code:
            return jsonify({'error': 'Code required'}), 400
        
        # Get AI suggestion
        suggestion = ai_engine.suggest_improvement(code, style_profile)
        
        return jsonify({
            'success': True,
            'suggestion': suggestion
        }), 200
        
    except Exception as e:
        print(f"Error getting suggestion: {e}")
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


@app.route('/upload.html')
def upload():
    """Serve upload.html"""
    return render_template('upload.html')


@app.route('/editor.html')
def editor():
    """Serve editor.html"""
    return render_template('editor.html')


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
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
