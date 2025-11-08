# 🔧 Render Environment Variables

Complete list of all environment variables needed for CodeMind deployment on Render.

## 📋 Required Environment Variables

### 1. **GROQ_API_KEY** (Required)
- **Description**: API key for Groq AI service (used for code generation)
- **How to get**: 
  1. Go to https://console.groq.com/
  2. Sign up/Login
  3. Navigate to API Keys section
  4. Create a new API key
- **Format**: `gsk_xxxxxxxxxxxxxxxxxxxx`
- **Example**: `gsk_your_groq_api_key_here`

### 2. **PORT** (Optional - Auto-set by Render)
- **Description**: Port number for the Flask application
- **Default**: `8000`
- **Note**: Render automatically sets this, but you can override if needed
- **Example**: `8000`

### 3. **FLASK_ENV** (Optional)
- **Description**: Flask environment mode
- **Options**: 
  - `development` - For local development (enables debug mode)
  - `production` - For production deployment (recommended for Render)
- **Recommended for Render**: `production`
- **Example**: `production`

## 🔐 Optional Environment Variables

### 4. **GITHUB_TOKEN** (Optional)
- **Description**: GitHub Personal Access Token for enhanced GitHub API access
- **Benefits**: 
  - Higher rate limits (5000 requests/hour vs 60/hour)
  - Access to private repositories
  - Better GitHub integration features
- **How to get**:
  1. Go to https://github.com/settings/tokens
  2. Click "Generate new token" → "Generate new token (classic)"
  3. Select scopes: `repo`, `read:user`, `read:org`
  4. Generate and copy the token
- **Format**: `ghp_xxxxxxxxxxxxxxxxxxxx` or `github_pat_xxxxxxxxxxxxxxxxxxxx`
- **Example**: `ghp_xxxxxxxxxxxxxxxxxxxx`

### 5. **GITHUB_PAT** (Optional - Alternative to GITHUB_TOKEN)
- **Description**: Alternative name for GitHub Personal Access Token
- **Note**: If both `GITHUB_TOKEN` and `GITHUB_PAT` are set, `GITHUB_TOKEN` takes precedence
- **Format**: Same as `GITHUB_TOKEN`

### 6. **FIREBASE_PRIVATE_KEY_ID** (Optional - For Firebase Admin SDK)
- **Description**: Firebase private key ID (if using Firebase Admin SDK)
- **When needed**: Only if you want to use Firebase Admin SDK features
- **Format**: String
- **Example**: `abc123def456...`

### 7. **FIREBASE_PRIVATE_KEY** (Optional - For Firebase Admin SDK)
- **Description**: Firebase private key (if using Firebase Admin SDK)
- **When needed**: Only if you want to use Firebase Admin SDK features
- **Format**: Multi-line string (with `\n` for newlines)
- **Note**: Make sure to escape newlines properly
- **Example**: `-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n`

### 8. **FIREBASE_CLIENT_EMAIL** (Optional - For Firebase Admin SDK)
- **Description**: Firebase client email (if using Firebase Admin SDK)
- **When needed**: Only if you want to use Firebase Admin SDK features
- **Format**: Email address
- **Example**: `firebase-adminsdk-xxxxx@xxxxx.iam.gserviceaccount.com`

### 9. **FIREBASE_CLIENT_ID** (Optional - For Firebase Admin SDK)
- **Description**: Firebase client ID (if using Firebase Admin SDK)
- **When needed**: Only if you want to use Firebase Admin SDK features
- **Format**: String
- **Example**: `123456789012345678901`

### 10. **FIREBASE_CLIENT_X509_CERT_URL** (Optional - For Firebase Admin SDK)
- **Description**: Firebase client X509 certificate URL (if using Firebase Admin SDK)
- **When needed**: Only if you want to use Firebase Admin SDK features
- **Format**: URL
- **Example**: `https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40xxxxx.iam.gserviceaccount.com`

## 🚀 Render Setup Instructions

### Step 1: Add Environment Variables in Render Dashboard

1. Go to your Render service dashboard
2. Navigate to **Environment** tab
3. Click **Add Environment Variable**
4. Add each variable one by one:

#### Minimum Required Setup:
```
GROQ_API_KEY = gsk_your_groq_api_key_here
FLASK_ENV = production
```

#### Recommended Setup (with GitHub integration):
```
GROQ_API_KEY = gsk_your_groq_api_key_here
FLASK_ENV = production
GITHUB_TOKEN = ghp_your_github_token_here
```

### Step 2: Verify Variables

After adding variables:
1. Save the changes
2. Render will automatically redeploy
3. Check the logs to ensure variables are loaded correctly

## 📝 Environment Variables Summary

| Variable | Required | Purpose | Default |
|----------|----------|---------|---------|
| `GROQ_API_KEY` | ✅ Yes | AI code generation | None |
| `PORT` | ❌ No | Server port | `8000` (auto-set by Render) |
| `FLASK_ENV` | ❌ No | Flask environment | `production` (recommended) |
| `GITHUB_TOKEN` | ❌ No | GitHub API access | None |
| `GITHUB_PAT` | ❌ No | Alternative GitHub token | None |
| `FIREBASE_PRIVATE_KEY_ID` | ❌ No | Firebase Admin SDK | None |
| `FIREBASE_PRIVATE_KEY` | ❌ No | Firebase Admin SDK | None |
| `FIREBASE_CLIENT_EMAIL` | ❌ No | Firebase Admin SDK | None |
| `FIREBASE_CLIENT_ID` | ❌ No | Firebase Admin SDK | None |
| `FIREBASE_CLIENT_X509_CERT_URL` | ❌ No | Firebase Admin SDK | None |

## ⚠️ Important Notes

1. **Never commit `.env` file**: The `.env` file is in `.gitignore` and should never be committed to Git
2. **Keep tokens secret**: All API keys and tokens are sensitive - never share them publicly
3. **Rotate keys regularly**: For security, rotate your API keys periodically
4. **Test locally first**: Always test with environment variables locally before deploying to Render

## 🔍 Verification

After deployment, check the Render logs for:
- ✅ `[OK] Groq API key found` - Confirms GROQ_API_KEY is loaded
- ✅ `[OK] GitHub token found` - Confirms GITHUB_TOKEN is loaded (if set)
- ❌ `WARNING: GROQ_API_KEY not found` - Means the key is missing or incorrect

## 📚 Additional Resources

- **Groq API**: https://console.groq.com/
- **GitHub Tokens**: https://github.com/settings/tokens
- **Render Docs**: https://render.com/docs/environment-variables
- **Flask Environment**: https://flask.palletsprojects.com/en/2.3.x/config/

---

**Last Updated**: 2024
**Version**: 1.0

