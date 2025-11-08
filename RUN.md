# How to Run CodeMind Application

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Up API Key

Create a `.env` file in the `backend` directory:

```bash
cd backend
echo GEMINI_API_KEY=your_api_key_here > .env
```

Or manually create `backend/.env`:
```
GEMINI_API_KEY=your_actual_gemini_api_key
```

**Get your FREE API key at:** https://makersuite.google.com/app/apikey

### 3. Run the Application

**The main file to run is: `backend/app.py`**

```bash
cd backend
python app.py
```

Or from the root directory:
```bash
python backend/app.py
```

### 4. Open in Browser

Once the server starts, open your browser and go to:

**http://localhost:8000**

The application will be available at:
- **Frontend:** http://localhost:8000
- **API:** http://localhost:8000/api

## What You'll See

1. **Landing Page** - Beautiful landing page with features
2. **Register/Login** - Create an account or sign in
3. **Dashboard** - View your coding stats
4. **Code Editor** - Main feature with Monaco Editor and AI suggestions

## PWA Features

The app is now a Progressive Web App (PWA):
- ✅ Installable on mobile and desktop
- ✅ Works offline (cached pages)
- ✅ App-like experience
- ✅ Install button will appear automatically

## Troubleshooting

### Port 8000 already in use?
Change the port in `backend/app.py`:
```python
app.run(host='0.0.0.0', port=8001, debug=True)
```

### Missing dependencies?
```bash
cd backend
pip install -r requirements.txt
```

### API Key not working?
Make sure your `.env` file is in the `backend` directory and contains:
```
GEMINI_API_KEY=your_key_here
```

## File Structure

```
vibe2/
├── backend/
│   └── app.py          ← RUN THIS FILE
├── frontend/
│   ├── index.html
│   ├── dashboard.html
│   ├── editor.html
│   └── ...
└── README.md
```

**Main Entry Point:** `backend/app.py`

