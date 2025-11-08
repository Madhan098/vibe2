/**
 * Authentication Helper Functions
 */

/**
 * Show error message
 */
function showError(message) {
    const errorEl = document.getElementById('error-message');
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.style.display = 'block';
    }
}

/**
 * Hide error message
 */
function hideError() {
    const errorEl = document.getElementById('error-message');
    if (errorEl) {
        errorEl.style.display = 'none';
    }
}

/**
 * Show success message
 */
function showSuccess(message) {
    const successEl = document.getElementById('success-message');
    if (successEl) {
        successEl.textContent = message;
        successEl.style.display = 'block';
    }
}

/**
 * Hide success message
 */
function hideSuccess() {
    const successEl = document.getElementById('success-message');
    if (successEl) {
        successEl.style.display = 'none';
    }
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!localStorage.getItem('token');
}

/**
 * Redirect to login if not authenticated
 */
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

/**
 * Check if user is already logged in and redirect to dashboard
 */
async function checkAutoLogin() {
    const token = localStorage.getItem('token');
    if (!token) {
        return false;
    }
    
    try {
        const userData = await getCurrentUser();
        if (userData.success && userData.user) {
            // User is logged in, redirect to dashboard
            return true;
        } else {
            // Token is invalid, clear it
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            return false;
        }
    } catch (error) {
        // Token is invalid, clear it
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        return false;
    }
}

/**
 * Auto-redirect if already logged in
 */
async function autoRedirectIfLoggedIn() {
    const isLoggedIn = await checkAutoLogin();
    if (isLoggedIn) {
        window.location.href = 'dashboard.html';
    }
}

