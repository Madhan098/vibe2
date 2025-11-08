# 🚀 Quick Start Guide

## Step 1: Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

## Step 2: Configure API Key

Create `.env` file in `backend/` directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000
```

Get your Gemini API key from: https://makersuite.google.com/app/apikey

## Step 3: Run Backend

```bash
cd backend
python app.py
```

Backend will start on: http://localhost:8000

## Step 4: Open Frontend

Option 1: Direct file
- Open `frontend/index.html` in your browser

Option 2: Local server (recommended)
```bash
cd frontend
python -m http.server 3000
```
Then visit: http://localhost:3000

## Step 5: Test It!

1. **Upload Files:**
   - Go to Upload page
   - Click "Choose Files" → Select Python files
   - Click "Upload & Analyze"
   - View your style report

2. **Analyze GitHub:**
   - Enter GitHub username (e.g., "octocat")
   - Click "Analyze GitHub"
   - Wait for analysis
   - View comprehensive report

3. **Get AI Suggestions:**
   - Go to Editor
   - Type some Python code
   - Wait 2 seconds
   - AI will suggest improvements matching your style!

## Troubleshooting

**Backend won't start:**
- Check if port 8000 is available
- Make sure `.env` file exists with GEMINI_API_KEY

**Frontend can't connect:**
- Make sure backend is running on port 8000
- Check browser console for errors
- Update `API_BASE` in `frontend/js/app.js` if needed

**GitHub analysis fails:**
- Make sure repositories are public
- Check if username is correct
- Some repos may not have Python files

## That's it! 🎉

CodeMind is ready to learn your coding style!
