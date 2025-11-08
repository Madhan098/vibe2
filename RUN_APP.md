# 🚀 How to Run the Application

## Quick Start

### 1. Make sure you're in the project root:
```bash
cd C:\Users\jmadh\OneDrive\Desktop\vibe2
```

### 2. Verify files exist:
```bash
# Check if app.py exists
dir app.py

# Check if templates and static folders exist
dir templates
dir static
```

### 3. Install dependencies (if not already):
```bash
pip install -r requirements.txt
```

### 4. Run the app:
```bash
python app.py
```

## Expected Output

You should see:
```
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8000
 * Running on http://10.20.23.230:8000
Press CTRL+C to quit
```

## Access the App

Open your browser and visit:
- **Homepage**: http://localhost:8000
- **Upload Page**: http://localhost:8000/upload
- **Editor**: http://localhost:8000/editor
- **API Health**: http://localhost:8000/api/health

## Troubleshooting

### Error: "No such file or directory"
**Solution:**
1. Make sure you're in the project root directory
2. Check that `app.py` exists: `dir app.py`
3. Check that `templates/` and `static/` folders exist

### Error: "Module not found"
**Solution:**
```bash
pip install -r requirements.txt
```

### Error: "GEMINI_API_KEY not found"
**Solution:**
1. Create `.env` file in the root directory
2. Add: `GEMINI_API_KEY=your_api_key_here`
3. Add: `PORT=8000`
4. Add: `FLASK_ENV=development`

## Project Structure

```
vibe2/
├── app.py              # Main Flask app
├── code_analyzer.py    # Code analysis
├── github_integration.py
├── ai_engine.py
├── requirements.txt
├── .env               # Your API keys (create this)
├── templates/         # HTML files
└── static/           # CSS, JS, images
```

## That's it!

Your app should be running on **http://localhost:8000** 🎉

