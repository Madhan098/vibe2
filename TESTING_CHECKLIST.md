# ✅ CodeMind Testing Checklist

## 🎯 Core Functionalities

### 1. **File Upload & Analysis**
- [ ] Upload local Python files
- [ ] See analysis report with:
  - Naming style
  - Documentation percentage
  - Type hints usage
  - Error handling style
  - Code quality score
- [ ] Style profile saved to localStorage

### 2. **GitHub Analysis**
- [ ] Enter GitHub username
- [ ] Analyze repositories
- [ ] See aggregated style report
- [ ] Works with multiple repositories

### 3. **Code Editor**
- [ ] Monaco editor loads correctly
- [ ] Type code in editor
- [ ] Auto-suggestions appear after 2 seconds
- [ ] Suggestions match user's style
- [ ] Context detection works (shows detected context)
- [ ] Teaching moments appear with suggestions

### 4. **AI Code Generation**
- [ ] Enter request in input field
- [ ] Click "Generate" or press Enter
- [ ] Code generated matching user's style
- [ ] Can insert code into editor
- [ ] Can copy code to clipboard

### 5. **Feedback Learning**
- [ ] Accept suggestion → Profile updates
- [ ] Reject suggestion → Feedback recorded
- [ ] Profile changes persist in localStorage

### 6. **Export Style Guide**
- [ ] Click "Export Style Guide" button
- [ ] Markdown file downloads
- [ ] File contains all style information

## 🔧 Technical Checks

### Backend
- [ ] Flask server starts without errors
- [ ] All API endpoints respond correctly:
  - `/api/analyze-files` (POST)
  - `/api/analyze-github` (POST)
  - `/api/suggest` (POST)
  - `/api/generate-code` (POST)
  - `/api/feedback` (POST)
  - `/api/export-style-guide` (POST)
  - `/api/auth/register` (POST)
  - `/api/auth/login` (POST)
  - `/api/auth/me` (GET)
- [ ] Error handling works (invalid requests return proper errors)
- [ ] CORS configured correctly

### Frontend
- [ ] All pages load correctly:
  - `/` (index.html)
  - `/upload.html`
  - `/editor.html`
  - `/login.html`
  - `/register.html`
- [ ] JavaScript functions work:
  - `getStyleProfile()`
  - `saveStyleProfile()`
  - `showError()`
  - `showSuccess()`
- [ ] API calls use correct base URL
- [ ] Error messages display properly
- [ ] Loading states work

### AI Features
- [ ] Gemini API key configured
- [ ] AI suggestions generate correctly
- [ ] Context detection works
- [ ] Teaching moments generate
- [ ] Code generation works

## 🐛 Common Issues to Check

1. **API Key Missing**
   - Check `.env` file exists
   - Verify `GEMINI_API_KEY` is set
   - Server should warn if missing

2. **CORS Errors**
   - Check browser console
   - Verify Flask-CORS is configured

3. **localStorage Issues**
   - Check browser allows localStorage
   - Verify profile saves/loads correctly

4. **Monaco Editor**
   - Check CDN loads correctly
   - Verify editor initializes

5. **GitHub API**
   - Check rate limits
   - Verify username exists
   - Check repositories are public

## 🚀 Quick Test Flow

1. **Start Server**: `python app.py`
2. **Open Browser**: `http://localhost:8000`
3. **Upload Files**: Go to upload page, select Python files
4. **Check Report**: Verify style analysis appears
5. **Go to Editor**: Type some code
6. **Check Suggestions**: Wait for AI suggestion
7. **Accept Suggestion**: Verify profile updates
8. **Generate Code**: Enter request, generate code
9. **Export Guide**: Download style guide

## ✅ All Systems Ready!

If all checks pass, your CodeMind is ready for the hackathon! 🎉

