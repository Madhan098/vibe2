# CodeMind - AI That Learns Your Coding Style

An AI coding assistant that analyzes your code patterns and suggests improvements matching YOUR unique style.

## 🚀 Quick Start

### Local Development

1. **Backend Setup:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure API Key:**
   Create `backend/.env`:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   PORT=8000
   FLASK_ENV=development
   ```

3. **Run Backend:**
   ```bash
   cd backend
   python app.py
   ```
   Backend runs on: http://localhost:8000

4. **Open Frontend:**
   - Open `frontend/index.html` in browser
   - Or use: `python -m http.server 3000` in frontend directory

### Deploy to Render

See [DEPLOY.md](./DEPLOY.md) for detailed deployment instructions.

**Quick Deploy:**
1. Push code to GitHub
2. Connect repository to Render
3. Set environment variables
4. Deploy!

## 📁 Project Structure

```
vibe2/
├── backend/
│   ├── app.py              # Flask server
│   ├── code_analyzer.py    # AST pattern detection
│   ├── github_integration.py # GitHub API
│   ├── ai_engine.py        # Gemini AI integration
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Landing page
│   ├── upload.html         # File upload page
│   ├── editor.html         # Code editor
│   ├── css/
│   │   └── style.css       # Styles
│   └── js/
│       ├── app.js          # Main app logic
│       ├── upload.js       # Upload functionality
│       └── editor.js       # Editor functionality
├── render.yaml             # Render configuration
├── Procfile                # Process file for Render
└── README.md
```

## ✨ Features

- 📊 **Style Analysis** - Analyzes naming conventions, documentation, type hints, and error handling
- 🤖 **AI Suggestions** - Get code improvements that match YOUR style, not generic templates
- 🔗 **GitHub Integration** - Analyze all your repositories to extract comprehensive patterns
- 💻 **Live Editor** - Monaco editor with real-time AI suggestions

## 🔧 API Endpoints

- `POST /api/analyze-files` - Analyze uploaded Python files
- `POST /api/analyze-github` - Analyze GitHub repositories
- `POST /api/suggest` - Get AI suggestion matching user's style
- `GET /api/health` - Health check

## 🛠️ Tech Stack

- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Backend**: Python Flask
- **AI**: Google Gemini API (gemini-1.5-flash)
- **Code Analysis**: Python AST library
- **Editor**: Monaco Editor
- **Hosting**: Render.com

## 📝 Usage

### 1. Upload Local Files
- Go to Upload page
- Click "Choose Files" → Select Python files
- Click "Upload & Analyze"
- View your style report

### 2. Analyze GitHub
- Enter GitHub username
- Click "Analyze GitHub"
- View comprehensive style report

### 3. Get AI Suggestions
- Go to Editor
- Start typing code
- AI analyzes after 2 seconds of inactivity
- Accept or reject suggestions

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Your Google Gemini API key |
| `PORT` | No | Port number (default: 8000) |
| `FLASK_ENV` | No | `development` or `production` |

## 📄 License

MIT

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

**Made with ❤️ for developers who want AI that learns**
