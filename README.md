# CodeMind - AI That Learns Your Coding Style

An AI coding assistant that analyzes your code patterns and suggests improvements matching YOUR unique style, not generic best practices.

## 🎯 How CodeMind Works

### Core Concept

CodeMind extracts your unique "coding DNA" from your actual code files, then uses that DNA to generate AI suggestions that match YOUR style. Instead of generic improvements, you get suggestions that feel like you wrote them yourself.

---

## 📊 System Architecture

### 1. **Code Analysis Engine** (`code_analyzer.py`)

**What it does:**
- Analyzes Python code files using Python's AST (Abstract Syntax Tree)
- Extracts coding patterns from your actual code
- Identifies your unique style preferences

**How it works:**
1. **Parses Code**: Uses Python's `ast` library to parse code into a tree structure
2. **Extracts Patterns**:
   - **Naming Conventions**: Detects if you use `snake_case`, `camelCase`, or `PascalCase`
   - **Documentation Style**: Calculates what percentage of functions have docstrings
   - **Type Hints Usage**: Measures how often you use type hints
   - **Error Handling**: Identifies if you prefer `try/except` or `if/else` patterns
   - **Code Structure**: Analyzes function lengths, complexity, and organization
3. **Generates Style Profile**: Creates a comprehensive profile with:
   - Dominant naming style with confidence percentage
   - Documentation coverage percentage
   - Type hints usage percentage
   - Error handling style preference
   - Overall code quality score (0-100)

**Example Output:**
```json
{
  "naming_style": "snake_case",
  "naming_confidence": 95.2,
  "documentation_percentage": 67.5,
  "type_hints_percentage": 23.1,
  "error_handling_style": "try_except",
  "code_quality_score": 78
}
```

---

### 2. **GitHub Integration** (`github_integration.py`)

**What it does:**
- Fetches all public repositories for a GitHub username
- Extracts Python files from multiple repositories
- Aggregates code from your entire GitHub profile

**How it works:**
1. **Fetch Repositories**: Uses GitHub API to get all public repos for a username
2. **Extract Files**: For each repository:
   - Gets the repository tree (all files)
   - Filters for Python files (`.py`)
   - Fetches file contents via GitHub API
   - Limits to 30 files per repo (for performance)
3. **Aggregate**: Combines files from all repositories (up to 50 total files)
4. **Return**: Provides all code files for analysis

**Why this matters:**
- Analyzes your coding style across ALL projects
- Gets a comprehensive view of your patterns
- More accurate style detection from multiple codebases

---

### 3. **AI Engine** (`ai_engine.py`)

**What it does:**
- Uses Google Gemini AI to generate code suggestions
- Matches suggestions to YOUR extracted coding style
- Ensures suggestions feel like you wrote them

**How it works:**
1. **Receives Input**:
   - Your code snippet
   - Your extracted style profile (from code analysis)
2. **Builds Context**: Creates a detailed prompt that includes:
   - Your naming convention (e.g., "ALWAYS use snake_case")
   - Your documentation style (e.g., "60% of functions have docstrings")
   - Your type hints usage (e.g., "23% usage - DO NOT add type hints")
   - Your error handling preference (e.g., "prefers try/except")
3. **Generates Suggestion**: Gemini AI analyzes your code and suggests improvements that:
   - Match your naming style exactly
   - Match your documentation style
   - Respect your preferences (e.g., won't add type hints if you don't use them)
   - Feel like YOU wrote the code, just improved
4. **Returns**: JSON with improved code, explanation, and confidence score

**Key Innovation:**
The AI doesn't just suggest "best practices" - it suggests improvements that match YOUR style. If you use `snake_case`, it will NEVER suggest `camelCase`. If you rarely use type hints, it won't force them on you.

---

### 4. **Flask Backend** (`app.py`)

**What it does:**
- Serves the web application
- Handles API requests
- Coordinates all components

**API Endpoints:**

#### `POST /api/analyze-files`
- **Input**: Uploaded Python files
- **Process**: 
  1. Receives files from frontend
  2. Extracts code content
  3. Calls `code_analyzer.py` to analyze patterns
  4. Returns style profile
- **Output**: JSON with your coding style report

#### `POST /api/analyze-github`
- **Input**: GitHub username
- **Process**:
  1. Calls `github_integration.py` to fetch all repos
  2. Extracts Python files from all repositories
  3. Calls `code_analyzer.py` to analyze aggregated code
  4. Returns comprehensive style profile
- **Output**: JSON with style report + number of files/repos analyzed

#### `POST /api/suggest`
- **Input**: Your code + your style profile
- **Process**:
  1. Receives code snippet and style profile
  2. Calls `ai_engine.py` with your code and style
  3. AI generates suggestion matching your style
  4. Returns suggestion
- **Output**: JSON with improved code, explanation, confidence

#### `GET /api/health`
- **Purpose**: Health check for deployment
- **Output**: `{"status": "ok"}`

---

## 🔄 Complete User Flow

### Flow 1: Upload Local Files

1. **User Action**: User clicks "Choose Files" → Selects Python files → Clicks "Upload & Analyze"
2. **Frontend**: Sends files to `/api/analyze-files` via FormData
3. **Backend**: 
   - Receives files
   - Extracts code content
   - Calls `analyze_code_files()` from `code_analyzer.py`
4. **Analysis**:
   - Parses each file with AST
   - Extracts naming patterns, documentation, type hints, error handling
   - Aggregates patterns across all files
   - Calculates style profile
5. **Response**: Returns style profile JSON
6. **Frontend**: 
   - Saves profile to `localStorage`
   - Displays report (naming style, documentation %, etc.)
   - Shows "Go to Editor" button

### Flow 2: Analyze GitHub Username

1. **User Action**: Enters GitHub username → Clicks "Analyze GitHub"
2. **Frontend**: Sends username to `/api/analyze-github`
3. **Backend**: 
   - Calls `fetch_all_user_code_files(username)`
4. **GitHub Integration**:
   - Fetches all public repositories for username
   - For each repo: gets file tree, filters Python files, fetches contents
   - Aggregates up to 50 files from multiple repos
5. **Analysis**: Same as Flow 1 - analyzes all aggregated code
6. **Response**: Returns style profile + stats (files analyzed, repos analyzed)
7. **Frontend**: Same as Flow 1 - saves and displays

### Flow 3: Get AI Suggestions

1. **User Action**: Types code in Monaco editor → Stops typing for 2 seconds
2. **Frontend**: 
   - Gets code from editor
   - Retrieves style profile from `localStorage`
   - Sends to `/api/suggest`
3. **Backend**: 
   - Receives code + style profile
   - Calls `ai_engine.suggest_improvement(code, style_profile)`
4. **AI Processing**:
   - Builds prompt with your style DNA
   - Sends to Gemini AI with instructions to match your style
   - AI generates suggestion matching your patterns
5. **Response**: Returns suggestion JSON
6. **Frontend**: 
   - Displays suggestion in right panel
   - Shows "Accept" and "Reject" buttons
7. **User Action**: 
   - **Accept**: Replaces code in editor with suggestion
   - **Reject**: Keeps original code

---

## 🧬 Style DNA Extraction Process

### Step-by-Step:

1. **File Collection**: Gather Python files (from upload or GitHub)
2. **AST Parsing**: Parse each file into Abstract Syntax Tree
3. **Pattern Detection**:
   - **Function Names**: Extract all function names → Analyze naming style
   - **Variable Names**: Extract variable names → Confirm naming style
   - **Docstrings**: Check each function for docstrings → Calculate percentage
   - **Type Hints**: Check function signatures for type hints → Calculate percentage
   - **Error Handling**: Count `try/except` vs `if/else` patterns
   - **Code Structure**: Measure function lengths, complexity
4. **Aggregation**: Combine patterns from all files
5. **Confidence Calculation**: 
   - Naming confidence = percentage of names matching dominant style
   - Documentation coverage = functions with docstrings / total functions
   - Type hints usage = functions with type hints / total functions
6. **Quality Score**: Calculate overall code quality (0-100) based on:
   - Documentation coverage
   - Type hints usage
   - Error handling presence
   - Code structure quality
7. **Profile Generation**: Create final style profile JSON

---

## 🤖 AI Suggestion Generation

### How AI Matches Your Style:

1. **Style Context Building**:
   ```
   USER'S CODING STYLE:
   - Naming: snake_case (95% confidence)
   - Documentation: 67% of functions have docstrings
   - Type Hints: 23% usage
   - Error Handling: try_except style
   - Code Quality: 78/100
   ```

2. **AI Instructions**:
   - "ALWAYS use snake_case for ALL function/variable names"
   - "Match their documentation style (67% usage)"
   - "DO NOT add type hints (they only use 23%)"
   - "Use try_except for error handling"
   - "Code should feel like THEY wrote it"

3. **Suggestion Generation**:
   - AI analyzes your code
   - Suggests improvements that match your style
   - Provides explanation of why it's better
   - Returns confidence score

4. **Result**: Code that looks like YOU wrote it, just improved!

---

## 📁 Project Structure

```
vibe2/
├── app.py                    # Flask server (main entry point)
├── code_analyzer.py          # AST-based code pattern extraction
├── github_integration.py     # GitHub API integration
├── ai_engine.py             # Gemini AI integration
├── requirements.txt          # Python dependencies
├── Procfile                 # Process file for Render
├── render.yaml              # Render deployment config
├── .env                     # Environment variables (GEMINI_API_KEY)
├── templates/               # HTML templates (Flask standard)
│   ├── index.html          # Landing page
│   ├── upload.html         # File upload & GitHub analysis
│   └── editor.html         # Code editor with AI suggestions
└── static/                 # Static files (Flask standard)
    ├── css/
    │   └── style.css          # Main stylesheet
    └── js/
        ├── app.js          # Main app logic
        ├── upload.js       # Upload page functionality
        └── editor.js        # Editor with Monaco integration
```

---

## 🚀 Quick Start

### Local Development

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key**:
   Create `.env` file:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   PORT=8000
   FLASK_ENV=development
   ```

3. **Run Application**:
   ```bash
   python app.py
   ```

4. **Access**:
   - Homepage: http://localhost:8000
   - Upload: http://localhost:8000/upload
   - Editor: http://localhost:8000/editor

### Deploy to Render

1. **Push to GitHub** (already done)
2. **Connect to Render**:
   - Go to render.com
   - New Web Service
   - Connect repository
   - **Settings**:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `python app.py`
   - **Environment Variables**:
     - `GEMINI_API_KEY` = your API key
     - `FLASK_ENV` = `production`
3. **Deploy**: Click "Create Web Service"

---

## 🔑 Key Features

### 1. **Style DNA Extraction**
- Analyzes your actual code files
- Extracts unique patterns (naming, docs, type hints, etc.)
- Creates comprehensive style profile
- Works with local files or GitHub repositories

### 2. **AI-Powered Suggestions**
- Uses Google Gemini AI
- Matches YOUR coding style exactly
- Respects your preferences (won't force patterns you don't use)
- Provides explanations and confidence scores

### 3. **Real-Time Analysis**
- Upload files → Get instant style report
- Enter GitHub username → Analyze all repos
- Type code → Get suggestions in 2 seconds

### 4. **Persistent Learning**
- Style profile saved in browser `localStorage`
- Used for all future suggestions
- No need to re-analyze every time

---

## 🛠️ Technology Stack

- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Backend**: Python Flask
- **Code Analysis**: Python AST library
- **AI**: Google Gemini API (gemini-1.5-flash)
- **Editor**: Monaco Editor (VS Code in browser)
- **GitHub**: GitHub REST API
- **Deployment**: Render.com

---

## 📝 API Documentation

### `POST /api/analyze-files`
Analyze uploaded Python files.

**Request**: `multipart/form-data` with `files[]`

**Response**:
```json
{
  "success": true,
  "report": {
    "naming_style": "snake_case",
    "naming_confidence": 95.2,
    "documentation_percentage": 67.5,
    "type_hints_percentage": 23.1,
    "error_handling_style": "try_except",
    "code_quality_score": 78
  }
}
```

### `POST /api/analyze-github`
Analyze all repositories for a GitHub username.

**Request**:
```json
{
  "username": "octocat"
}
```

**Response**:
```json
{
  "success": true,
  "report": { /* same as analyze-files */ },
  "files_analyzed": 45,
  "repos_analyzed": 12
}
```

### `POST /api/suggest`
Get AI suggestion matching user's style.

**Request**:
```json
{
  "code": "def get_user_data():\n    return data",
  "style_profile": {
    "naming_style": "snake_case",
    "documentation_percentage": 67.5,
    "type_hints_percentage": 23.1,
    "error_handling_style": "try_except"
  }
}
```

**Response**:
```json
{
  "success": true,
  "suggestion": {
    "has_suggestion": true,
    "improved_code": "def get_user_data():\n    \"\"\"Get user data.\"\"\"\n    try:\n        return data\n    except Exception as e:\n        return None",
    "explanation": "Added docstring and error handling matching your style",
    "confidence": 0.85
  }
}
```

---

## 🎯 How It's Different

### Traditional AI Assistants:
- Suggest generic "best practices"
- Force patterns you don't use
- Don't learn your style
- One-size-fits-all suggestions

### CodeMind:
- ✅ Learns YOUR unique coding style
- ✅ Matches YOUR naming conventions
- ✅ Respects YOUR preferences
- ✅ Suggests code that looks like YOU wrote it
- ✅ Adapts to your patterns, not generic templates

---

## 📄 License

MIT

---

**Made with ❤️ for developers who want AI that learns**
