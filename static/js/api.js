/**
 * API Client for CodeMind
 */

const API_BASE_URL = window.location.origin;

/**
 * Make API request
 */
async function apiRequest(endpoint, options = {}) {
    // Check if token is expired
    const token = localStorage.getItem('token');
    const expiresAt = localStorage.getItem('token_expires_at');
    
    if (token && expiresAt) {
        const expirationDate = new Date(expiresAt);
        const now = new Date();
        if (now > expirationDate) {
            // Token expired, clear it
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            localStorage.removeItem('token_expires_at');
        }
    }
    
    const currentToken = localStorage.getItem('token');
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (currentToken) {
        defaultOptions.headers['Authorization'] = `Bearer ${currentToken}`;
    }
    
    const config = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
            // If not JSON, read as text to see what we got
            const text = await response.text();
            console.error('Non-JSON response:', text.substring(0, 200));
            throw new Error('Server returned non-JSON response. Check if endpoint exists.');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Authentication API
 */
async function register(name, email, password) {
    try {
        const data = await apiRequest('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify({ name, email, password })
        });
        
        if (data.token) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            // Store session expiration (30 days from now)
            const expirationDate = new Date();
            expirationDate.setDate(expirationDate.getDate() + 30);
            localStorage.setItem('token_expires_at', expirationDate.toISOString());
        }
        
        return { success: true, ...data };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

async function login(email, password) {
    try {
        const data = await apiRequest('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        
        if (data.token) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            // Store session expiration (30 days from now)
            const expirationDate = new Date();
            expirationDate.setDate(expirationDate.getDate() + 30);
            localStorage.setItem('token_expires_at', expirationDate.toISOString());
        }
        
        return { success: true, ...data };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

async function logout() {
    try {
        await apiRequest('/api/auth/logout', {
            method: 'POST'
        });
        
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('token_expires_at');
        
        return { success: true };
    } catch (error) {
        // Clear local storage even if request fails
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('token_expires_at');
        return { success: true };
    }
}

async function getCurrentUser() {
    try {
        const data = await apiRequest('/api/auth/me');
        return { success: true, ...data };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Code Analysis API
 */
async function analyzeCode(code) {
    try {
        const data = await apiRequest('/api/analyze/code', {
            method: 'POST',
            body: JSON.stringify({ code })
        });
        return { success: true, ...data };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * AI Suggestion API
 */
async function getAISuggestion(code, fileName = 'untitled.py') {
    try {
        const data = await apiRequest('/api/ai/suggest', {
            method: 'POST',
            body: JSON.stringify({ code, file_name: fileName })
        });
        return { success: true, ...data };
    } catch (error) {
        return { success: false, error: error.message, has_suggestion: false };
    }
}

async function submitFeedback(userCode, suggestion, action) {
    try {
        const data = await apiRequest('/api/ai/feedback', {
            method: 'POST',
            body: JSON.stringify({ 
                user_code: userCode, 
                suggestion: suggestion, 
                action: action 
            })
        });
        return { success: true, ...data };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

async function detectErrors(code) {
    try {
        const data = await apiRequest('/api/ai/detect-errors', {
            method: 'POST',
            body: JSON.stringify({ code })
        });
        return { success: true, ...data };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Profile API
 */
async function getProfile() {
    try {
        const data = await apiRequest('/api/profile');
        return { success: true, ...data };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Style DNA API
 */
async function getDNAProfile() {
    try {
        const data = await apiRequest('/api/dna/profile');
        return { success: true, ...data };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

async function uploadCodeFiles(files) {
    try {
        const token = localStorage.getItem('token');
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        
        const response = await fetch(`${API_BASE_URL}/api/upload/code`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        const data = await response.json();
        return { success: response.ok, ...data };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

async function analyzeGitHubRepo(repoUrl) {
    try {
        const data = await apiRequest('/api/analyze-github', {
            method: 'POST',
            body: JSON.stringify({ repo_url: repoUrl })
        });
        return { success: true, ...data };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

async function analyzeGitHubUsername(username) {
    try {
        const data = await apiRequest('/api/analyze-github', {
            method: 'POST',
            body: JSON.stringify({ username: username })
        });
        return { success: true, ...data };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

async function trackEvolution(qualityScore) {
    try {
        const data = await apiRequest('/api/evolution/track', {
            method: 'POST',
            body: JSON.stringify({ quality_score: qualityScore })
        });
        return { success: true, ...data };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

