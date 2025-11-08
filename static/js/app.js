/**
 * CodeMind - Main App JavaScript
 */

// API base URL - automatically detect if running on Render or locally
// Use window.API_BASE to make it globally accessible and avoid redeclaration errors
if (typeof window.API_BASE === 'undefined') {
    window.API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : window.location.origin; // Use same origin when deployed
}
// Use window.API_BASE directly to avoid redeclaration errors
// Other files can access it via window.API_BASE

// Utility functions
function showError(message) {
    const errorEl = document.getElementById('error-message');
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.style.display = 'block';
    }
}

function hideError() {
    const errorEl = document.getElementById('error-message');
    if (errorEl) {
        errorEl.style.display = 'none';
    }
}

function showLoading(text = 'Loading...') {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        const textEl = document.getElementById('loading-text');
        if (textEl) textEl.textContent = text;
        loadingEl.style.display = 'block';
    }
}

function hideLoading() {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
    
    // Also hide enhanced loading overlay
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

// Toast Notification System (Global)
function showToast(message, type = 'info') {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        // Create toast container if it doesn't exist
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️',
        warning: '⚠️'
    };
    
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.animation = 'slideInRight 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

// Save style profile to localStorage (for backward compatibility)
// Also saves to backend if user is authenticated
function saveStyleProfile(profile) {
    // Save to localStorage for immediate use
    localStorage.setItem('codemind_style_profile', JSON.stringify(profile));
    
    // Save to backend if user is authenticated
    const token = localStorage.getItem('token');
    if (token) {
        fetch(`${window.API_BASE}/api/save-style-profile`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ style_profile: profile })
        }).catch(err => console.log('Could not save to backend:', err));
    }
}

// Get style profile - try backend first, then localStorage
async function getStyleProfile() {
    const token = localStorage.getItem('token');
    
    // If authenticated, try to get from backend
    if (token) {
        try {
            const response = await fetch(`${window.API_BASE}/api/get-style-profile`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.style_profile) {
                    // Also save to localStorage for offline use
                    localStorage.setItem('codemind_style_profile', JSON.stringify(data.style_profile));
                    return data.style_profile;
                }
            }
        } catch (error) {
            console.log('Could not fetch from backend, using localStorage:', error);
        }
    }
    
    // Fallback to localStorage
    const profile = localStorage.getItem('codemind_style_profile');
    return profile ? JSON.parse(profile) : null;
}
