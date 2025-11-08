# 🚀 Render Deployment Setup

## Quick Deploy Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Create Render Service

1. Go to [render.com](https://render.com)
2. Sign up/Login with GitHub
3. Click **"New +"** → **"Web Service"**
4. Connect repository: `Madhan098/vibe2`

### 3. Configure Service

**Basic Settings:**
- **Name**: `codemind` (or your preferred name)
- **Region**: Choose closest to you
- **Branch**: `main`
- **Root Directory**: `backend` ⚠️ **IMPORTANT: Set this to `backend`**
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`

**Environment Variables:**
Click **"Add Environment Variable"**:

1. **GEMINI_API_KEY**
   - Value: Your Gemini API key
   - Get from: https://makersuite.google.com/app/apikey

2. **PORT**
   - Value: `8000`
   - Render sets this automatically, but good to have

3. **FLASK_ENV**
   - Value: `production`

### 4. Deploy

Click **"Create Web Service"** and wait for deployment (2-5 minutes).

### 5. Your App is Live!

Your app will be available at:
```
https://your-app-name.onrender.com
```

## Project Structure for Render

```
vibe2/
├── backend/
│   ├── app.py              # Flask app (serves frontend + API)
│   ├── code_analyzer.py
│   ├── github_integration.py
│   ├── ai_engine.py
│   └── requirements.txt
├── frontend/             # Served as static files
│   ├── index.html
│   ├── upload.html
│   ├── editor.html
│   ├── css/
│   └── js/
├── Procfile              # Process file
├── render.yaml           # Render config (optional)
└── .gitignore
```

## Key Features

✅ **Single Service**: Backend serves both API and frontend  
✅ **Auto URL Detection**: Frontend automatically uses correct API URL  
✅ **CORS Configured**: Works with any origin  
✅ **Production Ready**: Debug mode disabled in production  

## Testing

After deployment, test:

1. **Health Check**: `https://your-app.onrender.com/api/health`
2. **Homepage**: `https://your-app.onrender.com/`
3. **Upload Page**: `https://your-app.onrender.com/upload.html`
4. **Editor**: `https://your-app.onrender.com/editor.html`

## Troubleshooting

### Build Fails
- Check `backend/requirements.txt` exists
- Verify Python version compatibility
- Check build logs in Render dashboard

### App Crashes
- Check logs in Render dashboard
- Verify `GEMINI_API_KEY` is set correctly
- Ensure port is configured

### Frontend Not Loading
- Check that `frontend/` folder exists
- Verify static folder path in `app.py`
- Check browser console for errors

### API Not Working
- Verify CORS is configured
- Check API endpoints in browser network tab
- Ensure environment variables are set

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Your Google Gemini API key |
| `PORT` | No | Port (auto-set by Render) |
| `FLASK_ENV` | No | `production` or `development` |

## Cost

- **Free Tier**: 750 hours/month (spins down after 15 min inactivity)
- **Hobby Plan**: $7/month (always on)
- **Professional**: $25/month (better performance)

## Next Steps

1. ✅ Deploy to Render
2. ✅ Test all features
3. ✅ Share your app URL
4. ✅ Monitor usage in Render dashboard

---

**Your app is ready for production!** 🎉

