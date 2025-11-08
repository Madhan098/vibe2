# 🔧 Render Deployment Fix

## The Problem
Render was looking for `requirements.txt` in the root directory, but it's in `backend/`.

## The Solution

### Option 1: Set Root Directory (Recommended)

In Render dashboard:
1. Go to your service settings
2. Find **"Root Directory"** field
3. Set it to: `backend`
4. Update **Build Command** to: `pip install -r requirements.txt`
5. Update **Start Command** to: `python app.py`
6. Save and redeploy

### Option 2: Keep Root Directory Empty

If you want to keep root directory empty:
1. **Build Command**: `pip install -r backend/requirements.txt`
2. **Start Command**: `cd backend && python app.py`
3. Make sure these are set correctly

## Updated Render Configuration

### Settings:
- **Root Directory**: `backend` ✅
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`

### Environment Variables:
- `GEMINI_API_KEY` = Your API key
- `FLASK_ENV` = `production`
- `PORT` = `8000` (auto-set by Render)

## Quick Fix Steps

1. **In Render Dashboard:**
   - Go to your service
   - Click "Settings"
   - Set **Root Directory** to: `backend`
   - Update **Build Command**: `pip install -r requirements.txt`
   - Update **Start Command**: `python app.py`
   - Save changes

2. **Redeploy:**
   - Click "Manual Deploy" → "Deploy latest commit"
   - Or push a new commit to trigger auto-deploy

3. **Verify:**
   - Check build logs - should see "Installing dependencies..."
   - Should see "Starting Flask app..."
   - Visit your app URL

## Why This Happened

Render by default looks for `requirements.txt` in the root directory. Since our project structure has it in `backend/`, we need to either:
- Set root directory to `backend` (easier)
- Or specify full path in build command

## After Fix

Your deployment should work! The app will:
- ✅ Install dependencies from `backend/requirements.txt`
- ✅ Start Flask app from `backend/app.py`
- ✅ Serve frontend files from `frontend/` directory
- ✅ Be accessible at your Render URL

---

**The fix is simple: Set Root Directory to `backend` in Render settings!** 🎯

