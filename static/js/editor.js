/**
 * Editor Page JavaScript
 */

let editor = null;
let suggestionTimeout = null;

// Initialize Monaco Editor
require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' } });

require(['vs/editor/editor.main'], function () {
    editor = monaco.editor.create(document.getElementById('monaco-editor'), {
        value: '# Start typing your Python code here...\n\n',
        language: 'python',
        theme: 'vs-dark',
        automaticLayout: true,
        fontSize: 14,
        minimap: { enabled: false }
    });
    
    // Listen for code changes
    editor.onDidChangeModelContent(() => {
        clearTimeout(suggestionTimeout);
        
        // Wait 2 seconds after user stops typing
        suggestionTimeout = setTimeout(() => {
            getSuggestion();
        }, 2000);
    });
});

// Clear button
const clearBtn = document.getElementById('clear-btn');
if (clearBtn) {
    clearBtn.addEventListener('click', () => {
        if (editor) {
            editor.setValue('# Start typing your Python code here...\n\n');
        }
        hideSuggestion();
    });
}

// Accept/Reject buttons
const acceptBtn = document.getElementById('accept-btn');
const rejectBtn = document.getElementById('reject-btn');

if (acceptBtn) {
    acceptBtn.addEventListener('click', () => {
        const suggestionCode = document.getElementById('suggestion-code').textContent;
        if (editor && suggestionCode) {
            editor.setValue(suggestionCode);
            hideSuggestion();
            updateStatus('Code updated!', 'success');
        }
    });
}

if (rejectBtn) {
    rejectBtn.addEventListener('click', () => {
        hideSuggestion();
        updateStatus('Suggestion rejected', 'info');
    });
}

async function getSuggestion() {
    if (!editor) return;
    
    const code = editor.getValue().trim();
    
    // Skip if code is too short or just placeholder
    if (code.length < 10 || code.includes('Start typing')) {
        return;
    }
    
    const styleProfile = getStyleProfile();
    
    if (!styleProfile) {
        updateStatus('No style profile found. Please upload code first.', 'warning');
        return;
    }
    
    updateStatus('Analyzing...', 'loading');
    showLoadingSuggestion();
    
    try {
        const response = await fetch(`${API_BASE}/api/suggest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                code: code,
                style_profile: styleProfile
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success && data.suggestion) {
            const suggestion = data.suggestion;
            
            if (suggestion.has_suggestion && suggestion.improved_code) {
                displaySuggestion(suggestion);
                updateStatus('Suggestion ready', 'success');
            } else {
                hideSuggestion();
                updateStatus('Code looks good!', 'success');
            }
        } else {
            hideSuggestion();
            updateStatus('Unable to get suggestion', 'error');
        }
    } catch (error) {
        hideSuggestion();
        updateStatus('Network error', 'error');
    }
}

function displaySuggestion(suggestion) {
    const suggestionEl = document.getElementById('suggestion');
    const noSuggestionEl = document.getElementById('no-suggestion');
    const loadingEl = document.getElementById('loading-suggestion');
    
    if (suggestionEl) {
        document.getElementById('suggestion-explanation').textContent = suggestion.explanation || 'Improved version';
        document.getElementById('suggestion-code').textContent = suggestion.improved_code || '';
        suggestionEl.style.display = 'block';
    }
    
    if (noSuggestionEl) noSuggestionEl.style.display = 'none';
    if (loadingEl) loadingEl.style.display = 'none';
}

function hideSuggestion() {
    const suggestionEl = document.getElementById('suggestion');
    const noSuggestionEl = document.getElementById('no-suggestion');
    const loadingEl = document.getElementById('loading-suggestion');
    
    if (suggestionEl) suggestionEl.style.display = 'none';
    if (noSuggestionEl) noSuggestionEl.style.display = 'block';
    if (loadingEl) loadingEl.style.display = 'none';
}

function showLoadingSuggestion() {
    const suggestionEl = document.getElementById('suggestion');
    const noSuggestionEl = document.getElementById('no-suggestion');
    const loadingEl = document.getElementById('loading-suggestion');
    
    if (suggestionEl) suggestionEl.style.display = 'none';
    if (noSuggestionEl) noSuggestionEl.style.display = 'none';
    if (loadingEl) loadingEl.style.display = 'block';
}

function updateStatus(text, type) {
    const statusText = document.getElementById('status-text');
    const statusDot = document.querySelector('.status-dot');
    
    if (statusText) {
        statusText.textContent = text;
    }
    
    if (statusDot) {
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6',
            loading: '#6366f1'
        };
        statusDot.style.background = colors[type] || colors.info;
    }
}
