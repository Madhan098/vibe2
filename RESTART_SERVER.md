# 🔄 How to Restart the Server

## Why Restart?

The server needs to be restarted to load the new API keys from the `.env` file.

## Steps to Restart:

### 1. Stop the Current Server

**In the terminal where the server is running:**
- Press `Ctrl + C` to stop the server
- Wait for it to fully stop

### 2. Start the Server Again

```bash
cd backend
python app.py
```

Or from the root directory:
```bash
python backend/app.py
```

### 3. Clear Browser Cache (Optional)

If you still see old content:

**Chrome/Edge:**
- Press `Ctrl + Shift + Delete`
- Select "Cached images and files"
- Click "Clear data"

**Or use Hard Refresh:**
- Press `Ctrl + F5` (Windows)
- Or `Ctrl + Shift + R`

### 4. Open the Application

Go to: **http://localhost:8000**

## Quick Restart Command

If you're in the backend directory:
```bash
# Stop: Ctrl+C
# Then run:
python app.py
```

## Verify API Keys Are Loaded

When the server starts, you should see:
```
============================================================
🚀 CodeMind Backend Starting...
============================================================
📍 Server: http://localhost:8000
🌐 Frontend: http://localhost:8000
📡 API Base: http://localhost:8000/api
============================================================
```

If you see an error about `GEMINI_API_KEY`, the .env file might not be loading correctly.

## Troubleshooting

### Server won't stop?
- Close the terminal window
- Or use Task Manager to kill Python processes

### Still seeing old content?
1. Hard refresh browser: `Ctrl + F5`
2. Clear browser cache
3. Try incognito/private mode
4. Check if you're on the right URL: `http://localhost:8000`

### API keys not working?
1. Verify `.env` file exists in `backend/` directory
2. Check file contents: `cat backend/.env` (Linux/Mac) or `type backend\.env` (Windows)
3. Make sure there are no extra spaces in the .env file
4. Restart the server after any .env changes

