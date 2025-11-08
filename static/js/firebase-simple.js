/**
 * Google OAuth Authentication (Direct OAuth, no Firebase)
 */

// Google OAuth Client ID
const GOOGLE_CLIENT_ID = "24978387197-r0s4p2l6ee62eigqi1fdddehlp5hnb0b.apps.googleusercontent.com";

// Wait for Google Identity Services to load
function waitForGoogleIdentity() {
    return new Promise((resolve, reject) => {
        if (typeof google !== 'undefined' && google.accounts) {
            resolve();
        } else {
            let attempts = 0;
            const checkInterval = setInterval(() => {
                attempts++;
                if (typeof google !== 'undefined' && google.accounts) {
                    clearInterval(checkInterval);
                    resolve();
                } else if (attempts > 50) {
                    clearInterval(checkInterval);
                    reject(new Error('Google Identity Services failed to load'));
                }
            }, 100);
        }
    });
}

// Sign in with Google OAuth (Direct OAuth, no Firebase)
async function signInWithGoogle() {
    try {
        await waitForGoogleIdentity();
        
        // Get current origin for redirect URI
        const currentOrigin = window.location.origin;
        console.log('Current origin:', currentOrigin);
        
        // Check if origin is allowed (basic check)
        if (currentOrigin.includes('localhost') || currentOrigin.includes('127.0.0.1')) {
            console.log('Using localhost origin');
        } else {
            console.log('Using production origin:', currentOrigin);
            console.log('Make sure this origin is added to Google Cloud Console > Authorized JavaScript origins');
        }
        
        return new Promise((resolve, reject) => {
            // Use Google OAuth 2.0 Token Client
            const tokenClient = google.accounts.oauth2.initTokenClient({
                client_id: GOOGLE_CLIENT_ID,
                scope: 'email profile',
                callback: async (tokenResponse) => {
                    try {
                        if (tokenResponse.error) {
                            console.error('Google OAuth error:', tokenResponse.error);
                            let errorMessage = tokenResponse.error;
                            
                            // Provide helpful error messages
                            if (tokenResponse.error === 'popup_closed_by_user') {
                                errorMessage = 'Sign-in popup was closed. Please try again.';
                            } else if (tokenResponse.error === 'access_denied') {
                                errorMessage = 'Access denied. Please check that your domain is authorized in Google Cloud Console.';
                            } else if (tokenResponse.error.includes('redirect_uri_mismatch')) {
                                errorMessage = `Redirect URI mismatch. Please add "${currentOrigin}" to Authorized JavaScript origins in Google Cloud Console.`;
                            }
                            
                            reject(new Error(errorMessage));
                            return;
                        }
                        
                        console.log('Google OAuth token received');
                        
                        // Get user info using access token
                        const userInfoResponse = await fetch(`https://www.googleapis.com/oauth2/v2/userinfo?access_token=${tokenResponse.access_token}`);
                        
                        if (!userInfoResponse.ok) {
                            throw new Error('Failed to get user info from Google');
                        }
                        
                        const userInfo = await userInfoResponse.json();
                        
                        // Send to backend
                        const backendResponse = await fetch('/api/auth/google', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ 
                                token: tokenResponse.access_token,
                                userInfo: userInfo
                            })
                        });
                        
                        const data = await backendResponse.json();
                        
                        if (backendResponse.ok && data.success) {
                            localStorage.setItem('token', data.token);
                            localStorage.setItem('user', JSON.stringify(data.user));
                            // Store session expiration (30 days from now)
                            const expirationDate = new Date();
                            expirationDate.setDate(expirationDate.getDate() + 30);
                            localStorage.setItem('token_expires_at', expirationDate.toISOString());
                            resolve({ success: true, user: data.user });
                        } else {
                            reject(new Error(data.error || 'Authentication failed'));
                        }
                    } catch (error) {
                        console.error('Backend auth error:', error);
                        reject(error);
                    }
                }
            });
            
            // Request access token (this will open Google sign-in popup)
            // The redirect URI is automatically set to the current origin
            try {
                tokenClient.requestAccessToken({ prompt: 'consent' });
            } catch (error) {
                console.error('Error requesting access token:', error);
                reject(new Error(`Failed to initiate Google sign-in: ${error.message}. Make sure your domain "${currentOrigin}" is added to Authorized JavaScript origins in Google Cloud Console.`));
            }
        });
    } catch (error) {
        console.error('Google sign-in error:', error);
        const currentOrigin = window.location.origin;
        if (error.message.includes('failed to load') || error.message.includes('Identity Services')) {
            throw new Error(`Google Identity Services failed to load. Please check your internet connection and try again.`);
        }
        throw error;
    }
}

// Sign in with email and password (use existing backend API)
async function signInWithEmail(email, password) {
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            // Store session expiration (30 days from now)
            const expirationDate = new Date();
            expirationDate.setDate(expirationDate.getDate() + 30);
            localStorage.setItem('token_expires_at', expirationDate.toISOString());
            return { success: true, user: data.user };
        } else {
            throw new Error(data.error || 'Authentication failed');
        }
    } catch (error) {
        console.error('Email sign-in error:', error);
        throw error;
    }
}

// Register with email and password (use existing backend API)
async function registerWithEmail(name, email, password) {
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            // Store session expiration (30 days from now)
            const expirationDate = new Date();
            expirationDate.setDate(expirationDate.getDate() + 30);
            localStorage.setItem('token_expires_at', expirationDate.toISOString());
            return { success: true, user: data.user };
        } else {
            throw new Error(data.error || 'Registration failed');
        }
    } catch (error) {
        console.error('Registration error:', error);
        throw error;
    }
}

// Sign out
async function signOutUser() {
    try {
        // Call backend logout
        const token = localStorage.getItem('token');
        if (token) {
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        }
        
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('token_expires_at');
        return { success: true };
    } catch (error) {
        console.error('Sign out error:', error);
        // Still clear local storage
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('token_expires_at');
        return { success: true };
    }
}

// Make functions globally available
window.signInWithGoogle = signInWithGoogle;
window.signInWithEmail = signInWithEmail;
window.registerWithEmail = registerWithEmail;
window.signOutUser = signOutUser;

