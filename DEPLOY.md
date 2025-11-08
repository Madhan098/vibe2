# 🚀 Deploy CodeMind to Render

## Step 1: Prepare Your Repository

1. Make sure all files are committed and pushed to GitHub:
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

## Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account
3. Connect your GitHub repository

## Step 3: Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your repository: `Madhan098/vibe2`
3. Configure the service:

### Basic Settings:
- **Name**: `codemind-backend` (or any name you prefer)
- **Region**: Choose closest to you
- **Branch**: `main`
- **Root Directory**: Leave empty (or set to `backend` if you prefer)
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `cd backend && python app.py`

### Environment Variables:
Click **"Add Environment Variable"** and add:

- **Key**: `GEMINI_API_KEY`
- **Value**: Your Gemini API key (get from https://makersuite.google.com/app/apikey)

- **Key**: `PORT`
- **Value**: `8000`

- **Key**: `FLASK_ENV`
- **Value**: `production`

### Advanced Settings (Optional):
- **Auto-Deploy**: `Yes` (deploys on every push)
- **Health Check Path**: `/api/health`

## Step 4: Deploy

1. Click **"Create Web Service"**
2. Render will:
   - Clone your repository
   - Install dependencies
   - Start your Flask app
3. Wait for deployment (usually 2-5 minutes)

## Step 5: Get Your URL

Once deployed, Render will give you a URL like:
```
https://codemind-backend.onrender.com
```

## Step 6: Update Frontend (Optional)

If you want to use the deployed backend:

1. Update `frontend/js/app.js`:
   ```javascript
   const API_BASE = 'https://your-app-name.onrender.com';
   ```

2. Or use the automatic detection (already configured):
   - Works locally: `http://localhost:8000`
   - Works on Render: Uses same origin

## Step 7: Test

1. Visit your Render URL
2. Test the API: `https://your-app.onrender.com/api/health`
3. Should return: `{"status":"ok"}`

## Troubleshooting

### Build Fails:
- Check that `backend/requirements.txt` exists
- Verify Python version (3.11.0)
- Check build logs in Render dashboard

### App Crashes:
- Check logs in Render dashboard
- Verify `GEMINI_API_KEY` is set
- Check that port is set to `8000`

### CORS Errors:
- Already configured with `flask-cors`
- If issues persist, check `CORS(app)` in `app.py`

### Static Files Not Loading:
- Frontend files are served from `frontend/` directory
- Check that files exist in the repository

## Alternative: Deploy Frontend Separately

You can also deploy the frontend separately:

1. **Option 1**: Use Render Static Site
   - Upload `frontend/` folder
   - Update `API_BASE` to your backend URL

2. **Option 2**: Use Netlify/Vercel
   - Connect GitHub repo
   - Set build directory to `frontend`
   - Update `API_BASE` in `app.js`

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Your Google Gemini API key |
| `PORT` | No | Port number (default: 8000) |
| `FLASK_ENV` | No | Set to `production` for production |

## Cost

- **Free Tier**: 750 hours/month
- **Hobby Plan**: $7/month (always on)
- **Professional**: $25/month (better performance)

## Support

If you encounter issues:
1. Check Render logs
2. Verify environment variables
3. Test API endpoints manually
4. Check GitHub repository is up to date

---

**Your app will be live at**: `https://your-app-name.onrender.com` 🎉

