/**
 * CodeMind - Main App JavaScript
 */

// API base URL - automatically detect if running on Render or locally
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : window.location.origin; // Use same origin when deployed

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
}

// Save style profile to localStorage
function saveStyleProfile(profile) {
    localStorage.setItem('codemind_style_profile', JSON.stringify(profile));
}

// Get style profile from localStorage
function getStyleProfile() {
    const profile = localStorage.getItem('codemind_style_profile');
    return profile ? JSON.parse(profile) : null;
}
