# 🔧 Fix Render Deployment - Gunicorn Error

## The Problem
Render is trying to use `gunicorn` but it's not installed. This happens when Render auto-detects instead of using your Procfile.

## ✅ Solution

### Option 1: Update Render Settings (Recommended)

1. **Go to Render Dashboard**
2. **Click on your service** (codemind-backend)
3. **Go to "Settings"**
4. **Find "Start Command"**
5. **Change it to**: `python app.py`
6. **Save changes**
7. **Click "Manual Deploy" → "Deploy latest commit"**

### Option 2: Delete and Recreate Service

If settings are stuck:

1. **Delete the current service** in Render
2. **Create new Web Service**
3. **Connect same repository**: `Madhan098/vibe2`
4. **Configure**:
   - **Name**: `codemind-backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py` ⚠️ **Set this explicitly**
   - **Root Directory**: Leave empty
5. **Environment Variables**:
   - `GEMINI_API_KEY` = your API key
   - `FLASK_ENV` = `production`
6. **Create Service**

## ✅ Why This Works

- **Procfile exists**: `web: python app.py`
- **No gunicorn needed**: Flask's built-in server works fine
- **Simple and clean**: Just Python, no extra dependencies

## 📝 Important Notes

- **Don't use gunicorn**: Not needed for this app
- **Use `python app.py`**: This is the correct start command
- **Procfile is correct**: Make sure Render uses it

## 🎯 After Fix

Your deployment should work! The app will:
- ✅ Install dependencies
- ✅ Start Flask server
- ✅ Serve on port 8000
- ✅ Be accessible at your Render URL

---

**The fix is simple: Set Start Command to `python app.py` in Render settings!**

