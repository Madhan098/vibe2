# Google OAuth Setup for Production

## Problem
Google OAuth works on localhost but not on live site. This is because Google Cloud Console needs to have your production domain configured.

## Solution

### Step 1: Add Authorized JavaScript Origins

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create one if needed)
3. Navigate to **APIs & Services** > **Credentials**
4. Find your OAuth 2.0 Client ID: `24978387197-r0s4p2l6ee62eigqi1fdddehlp5hnb0b.apps.googleusercontent.com`
5. Click **Edit** (pencil icon)
6. Under **Authorized JavaScript origins**, click **+ ADD URI**
7. Add these URLs:
   - `http://localhost:8000`
   - `http://localhost:5000`
   - `http://127.0.0.1:8000`
   - `http://127.0.0.1:5000`
   - `https://vibe2-1.onrender.com` (your live site)
   - `https://your-custom-domain.com` (if you have one)

### Step 2: Add Authorized Redirect URIs (if using redirect flow)

If you're using redirect-based OAuth (not popup), also add these under **Authorized redirect URIs**:
   - `http://localhost:8000`
   - `http://localhost:5000`
   - `https://vibe2-1.onrender.com`
   - `https://vibe2-1.onrender.com/api/auth/google/callback` (if you have a callback endpoint)

### Step 3: Save Changes

Click **Save** and wait a few minutes for changes to propagate.

### Step 4: Test

1. Clear your browser cache
2. Try Google OAuth on your live site
3. Check browser console for any errors

## Common Issues

### Issue: "redirect_uri_mismatch" error
**Solution:** Make sure your live site URL is added to **Authorized JavaScript origins** in Google Cloud Console.

### Issue: "Access blocked: This app's request is invalid"
**Solution:** 
- Check that your Client ID is correct
- Verify the domain is added to Authorized JavaScript origins
- Make sure you're using HTTPS for production (Google requires HTTPS for production domains)

### Issue: OAuth popup doesn't open
**Solution:**
- Check browser console for errors
- Verify Google Identity Services script is loaded
- Make sure popup blockers are disabled

## Current Configuration

- **Client ID:** `24978387197-r0s4p2l6ee62eigqi1fdddehlp5hnb0b.apps.googleusercontent.com`
- **OAuth Flow:** Popup-based (using Google Identity Services)
- **Redirect URI:** Automatically set to `window.location.origin`

## Testing

After adding your live site URL to Google Cloud Console:

1. Wait 2-5 minutes for changes to propagate
2. Clear browser cache
3. Test on live site: `https://vibe2-1.onrender.com`
4. Check browser console (F12) for any errors

## Need Help?

If issues persist:
1. Check browser console for specific error messages
2. Verify the Client ID matches in Google Cloud Console
3. Ensure your live site is using HTTPS
4. Check that Google Identity Services script is loading correctly

