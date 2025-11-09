/**
 * Editor Page JavaScript
 */

// API_BASE should be defined in app.js (loaded before this file)
// If not, define it here
if (typeof window.API_BASE === 'undefined') {
    window.API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000'
        : window.location.origin;
}

// Ensure utility functions are available
if (typeof getStyleProfile === 'undefined') {
    async function getStyleProfile() {
        // Try to use global async version if available
        if (typeof window.getStyleProfile === 'function') {
            return await window.getStyleProfile();
        }
        // Fallback to localStorage
        const profile = localStorage.getItem('codemind_style_profile');
        return profile ? JSON.parse(profile) : null;
    }
    window.getStyleProfile = getStyleProfile;
}

// Ensure getCurrentUser is available
if (typeof getCurrentUser === 'undefined') {
    async function getCurrentUser() {
        // Try to use global version if available
        if (typeof window.getCurrentUser === 'function') {
            return await window.getCurrentUser();
        }
        // Fallback to API call
        try {
            const response = await fetch(`${window.API_BASE}/api/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            const data = await response.json();
            return { success: true, ...data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    window.getCurrentUser = getCurrentUser;
}

if (typeof saveStyleProfile === 'undefined') {
    function saveStyleProfile(profile) {
        localStorage.setItem('codemind_style_profile', JSON.stringify(profile));
    }
}

let editor = null;
let suggestionTimeout = null;
let originalCodeBeforeSuggestion = ''; // Store original code for feedback
let beginnerMode = false; // Beginner mode flag
let currentStyleOptions = []; // Store current style options for beginner mode

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
    
    // Initialize file system with current editor content
    if (editor) {
        const initialCode = editor.getValue();
        if (initialCode && initialCode.trim() !== '# Start typing your Python code here...\n\n') {
            window.fileSystem['main.py'] = initialCode;
            window.currentFile = 'main.py';
        } else {
            // Initialize empty main.py
            window.fileSystem['main.py'] = '';
            window.currentFile = 'main.py';
        }
    }
    
    // Initialize sidebar after editor is ready
    initializeSidebar();
    
    // Listen for code changes
    editor.onDidChangeModelContent(() => {
        clearTimeout(suggestionTimeout);
        
        // Wait 2 seconds after user stops typing
        suggestionTimeout = setTimeout(() => {
            getSuggestion();
        }, 2000);
    });
    
    // Selection context menu - show when text is selected
    let selectionTimeout = null;
    editor.onDidChangeCursorSelection(() => {
        const selection = editor.getSelection();
        
        // Clear any pending hide timeout
        if (selectionTimeout) {
            clearTimeout(selectionTimeout);
            selectionTimeout = null;
        }
        
        if (selection && !selection.isEmpty()) {
            // Small delay to allow selection to complete
            setTimeout(() => {
                const currentSelection = editor.getSelection();
                if (currentSelection && !currentSelection.isEmpty()) {
                    showSelectionContextMenu(currentSelection);
                }
            }, 150);
        } else {
            // Delay hiding to allow clicking on menu
            selectionTimeout = setTimeout(() => {
                hideSelectionContextMenu();
            }, 200);
        }
    });
    
    // Prevent default browser context menu on editor
    editor.onContextMenu((e) => {
        e.preventDefault();
        e.stopPropagation();
    });
    
    // Hide menu when clicking outside (but not on the menu itself)
    document.addEventListener('mousedown', (e) => {
        if (selectionContextMenu && !selectionContextMenu.contains(e.target)) {
            // Check if clicking on editor
            const editorContainer = document.getElementById('monaco-editor');
            if (editorContainer && !editorContainer.contains(e.target)) {
                // Only hide if selection is cleared
                const selection = editor.getSelection();
                if (!selection || selection.isEmpty()) {
                    hideSelectionContextMenu();
                }
            }
        }
    });
    
    // Keep menu visible while text is selected
    editor.onDidChangeModelContent(() => {
        const selection = editor.getSelection();
        if (selection && !selection.isEmpty() && selectionContextMenu) {
            // Update menu position if selection changes
            const selectedText = editor.getModel().getValueInRange(selection);
            if (selectedText && selectedText.trim().length > 0) {
                // Menu is still valid, keep it visible
                return;
            }
        }
    });
    
    // Language selector
    const languageSelector = document.getElementById('language-selector');
    if (languageSelector) {
        languageSelector.addEventListener('change', (e) => {
            const selectedLanguage = e.target.value;
            if (editor) {
                monaco.editor.setModelLanguage(editor.getModel(), selectedLanguage);
                updateStatus(`Language changed to ${selectedLanguage}`, 'success');
            }
        });
    }
    
    // Initialize VS Code menu functionality
    initializeVSCodeMenu();
    
    // Beginner mode toggle
    const beginnerModeToggle = document.getElementById('beginner-mode-toggle');
    if (beginnerModeToggle) {
        beginnerModeToggle.addEventListener('change', (e) => {
            beginnerMode = e.target.checked;
            const beginnerHint = document.getElementById('beginner-hint');
            if (beginnerHint) {
                beginnerHint.style.display = beginnerMode ? 'block' : 'none';
            }
            updateStatus(beginnerMode ? 'Beginner mode enabled' : 'Beginner mode disabled', 'info');
        });
    }
});

// Clear button
const clearBtn = document.getElementById('clear-btn');
if (clearBtn) {
    clearBtn.addEventListener('click', () => {
        if (editor) {
            const languageSelector = document.getElementById('language-selector');
            const lang = languageSelector ? languageSelector.value : 'python';
            const defaultCode = {
                'python': '# Start typing your Python code here...\n\n',
                'javascript': '// Start typing your JavaScript code here...\n\n',
                'typescript': '// Start typing your TypeScript code here...\n\n',
                'java': '// Start typing your Java code here...\n\n',
                'html': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Document</title>\n</head>\n<body>\n    \n</body>\n</html>',
                'css': '/* Start typing your CSS here... */\n',
                'json': '{\n    \n}',
                'markdown': '# Start typing your Markdown here...\n\n'
            };
            editor.setValue(defaultCode[lang] || defaultCode['python']);
        }
        hideSuggestion();
    });
}

// Template buttons
let selectedTemplate = null;
// Custom Stack Button Toggle
const customStackBtn = document.getElementById('custom-stack-btn');
const techStackInputContainer = document.getElementById('tech-stack-input-container');
if (customStackBtn && techStackInputContainer) {
    customStackBtn.addEventListener('click', () => {
        const isVisible = techStackInputContainer.style.display !== 'none';
        techStackInputContainer.style.display = isVisible ? 'none' : 'block';
        customStackBtn.textContent = isVisible ? '🔧 Custom Stack' : '✕ Close';
    });
}

// Template buttons removed - no longer needed

// Accept/Reject buttons
const acceptBtn = document.getElementById('accept-suggestion-btn') || document.getElementById('accept-btn');
const rejectBtn = document.getElementById('reject-suggestion-btn') || document.getElementById('reject-btn');
const closeSuggestionBtn = document.getElementById('close-suggestion-btn');
const explainMoreBtn = document.getElementById('explain-more-btn');

if (acceptBtn) {
    acceptBtn.addEventListener('click', async () => {
        // Get improved code from comparison view
        const improvedCodeEl = document.getElementById('improved-code');
        const suggestionCode = improvedCodeEl ? improvedCodeEl.textContent : 
                              (document.getElementById('suggestion-code') ? document.getElementById('suggestion-code').textContent : '');
        const originalCode = originalCodeBeforeSuggestion || (editor ? editor.getValue() : '');
        
        if (editor && suggestionCode) {
            editor.setValue(suggestionCode);
            hideSuggestion();
            updateStatus('Code updated!', 'success');
            
            // Show toast notification
            if (typeof showToast === 'function') {
                showToast('Suggestion applied to your code', 'success');
            }
            
            // Send feedback to backend to learn from acceptance
            const styleProfile = getStyleProfile();
            if (styleProfile) {
                try {
                    const response = await fetch(`${window.API_BASE}/api/feedback`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            user_code: originalCode,
                            suggestion: suggestionCode,
                            action: 'accept',
                            style_profile: styleProfile
                        })
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        if (result.success && result.updated_profile) {
                            // Update stored profile
                            saveStyleProfile(result.updated_profile);
                            // Show success message
                            setTimeout(() => {
                                updateStatus(result.message || '✅ Profile updated!', 'success');
                            }, 1000);
                        }
                    }
                } catch (error) {
                    console.error('Error sending feedback:', error);
                    // Don't show error to user - feedback is optional
                }
            }
        }
    });
}

// Close suggestion button
if (closeSuggestionBtn) {
    closeSuggestionBtn.addEventListener('click', () => {
        hideSuggestion();
    });
}

// Explain more button
if (explainMoreBtn) {
    explainMoreBtn.addEventListener('click', () => {
        const styleExplanation = document.getElementById('style-explanation');
        if (styleExplanation) {
            // Could expand explanation or show more details
            if (typeof showToast === 'function') {
                showToast('Detailed explanation shown in the panel below', 'info');
            }
        }
    });
}

if (rejectBtn) {
    rejectBtn.addEventListener('click', async () => {
        const originalCode = originalCodeBeforeSuggestion || (editor ? editor.getValue() : '');
        const improvedCodeEl = document.getElementById('improved-code');
        const suggestionCode = improvedCodeEl ? improvedCodeEl.textContent : 
                              (document.getElementById('suggestion-code') ? document.getElementById('suggestion-code').textContent : '');
        
        hideSuggestion();
        updateStatus('Suggestion rejected', 'info');
        
        // Show toast notification
        if (typeof showToast === 'function') {
            showToast('Suggestion rejected', 'info');
        }
        
        // Send feedback to backend
        const styleProfile = getStyleProfile();
        if (styleProfile && suggestionCode) {
            try {
                const response = await fetch(`${window.API_BASE}/api/feedback`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_code: originalCode,
                        suggestion: suggestionCode,
                        action: 'reject',
                        style_profile: styleProfile
                    })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    if (result.message) {
                        setTimeout(() => {
                            updateStatus(result.message, 'info');
                        }, 500);
                    }
                }
            } catch (error) {
                console.error('Error sending feedback:', error);
                // Don't show error - feedback is optional
            }
        }
    });
}

async function getSuggestion() {
    if (!editor) return;
    
    const code = editor.getValue().trim();
    
    // Skip if code is too short or just placeholder
    if (code.length < 10 || code.includes('Start typing')) {
        return;
    }
    
    // Store original code for feedback
    originalCodeBeforeSuggestion = code;
    
    // Check if beginner mode is enabled
    if (beginnerMode) {
        // In beginner mode, show multiple style options
        await getBeginnerSuggestions(code);
        return;
    }
    
    // Regular mode: check for style profile
    const styleProfile = await getStyleProfile();
    
    if (!styleProfile) {
        // No profile - suggest beginner mode
        updateStatus('No style profile found. Enable Beginner Mode to learn as you code!', 'warning');
        return;
    }
    
    updateStatus('Analyzing...', 'loading');
    showLoadingSuggestion();
    
    // Get filename from editor (if available) or use default
    const filename = 'code.py'; // Could be enhanced to track filename
    
    try {
        const response = await fetch(`${window.API_BASE}/api/suggest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                code: code,
            filename: filename,
            // Style profile will be loaded automatically from backend if authenticated
            // Only send if not authenticated (fallback)
                style_profile: styleProfile
            })
        });
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Non-JSON response:', text.substring(0, 200));
            hideSuggestion();
            updateStatus('Server error. Please try again.', 'error');
            return;
        }
        
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
            updateStatus(data.error || 'Unable to get suggestion', 'error');
        }
    } catch (error) {
        console.error('Error getting suggestion:', error);
        hideSuggestion();
        updateStatus('Network error: ' + error.message, 'error');
    }
}

function displaySuggestion(suggestion) {
    const suggestionPanel = document.getElementById('suggestion-panel');
    const noSuggestionEl = document.getElementById('no-suggestion');
    const loadingEl = document.getElementById('loading-suggestion');
    
    if (suggestionPanel) {
        // Get original code
        const originalCode = originalCodeBeforeSuggestion || (editor ? editor.getValue() : '');
        const improvedCode = suggestion.improved_code || '';
        
        // Display side-by-side comparison
        const originalCodeEl = document.getElementById('original-code');
        const improvedCodeEl = document.getElementById('improved-code');
        
        if (originalCodeEl) {
            originalCodeEl.textContent = originalCode;
        }
        if (improvedCodeEl) {
            improvedCodeEl.textContent = improvedCode;
        }
        
        // Update confidence badge
        const confidenceEl = document.getElementById('confidence-value');
        if (confidenceEl) {
            const confidence = suggestion.confidence || suggestion.style_match || 85;
            confidenceEl.textContent = `${Math.round(confidence)}%`;
        }
        
        // Populate changes list
        const changesList = document.getElementById('changes-list');
        if (changesList) {
            changesList.innerHTML = '';
            
            // Extract changes from explanation or generate them
            const changes = extractChanges(originalCode, improvedCode, suggestion.explanation);
            changes.forEach(change => {
                const li = document.createElement('li');
                li.textContent = change;
                changesList.appendChild(li);
            });
        }
        
        // Display style explanation
        const styleExplanation = document.getElementById('style-explanation');
        if (styleExplanation) {
            let explanation = suggestion.explanation || suggestion.teaching?.why || 'This improvement matches your coding style.';
            
            // Add style match details if available
            if (suggestion.style_match) {
                explanation += ` The AI matched your style with ${Math.round(suggestion.style_match)}% confidence.`;
            }
            
            if (suggestion.teaching) {
                explanation += ` ${suggestion.teaching.what || ''}`;
            }
            
            styleExplanation.textContent = explanation;
        }
        
        // Show suggestion panel
        suggestionPanel.style.display = 'block';
        
        // Scroll to suggestion
        suggestionPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    if (noSuggestionEl) noSuggestionEl.style.display = 'none';
    if (loadingEl) loadingEl.style.display = 'none';
}

function extractChanges(original, improved, explanation) {
    const changes = [];
    
    // Try to extract from explanation
    if (explanation) {
        // Look for bullet points or numbered lists
        const lines = explanation.split('\n');
        lines.forEach(line => {
            const trimmed = line.trim();
            if (trimmed.match(/^[-•*]\s+/) || trimmed.match(/^\d+\.\s+/)) {
                changes.push(trimmed.replace(/^[-•*\d.]+\s+/, ''));
            }
        });
    }
    
    // If no changes found, generate generic ones
    if (changes.length === 0) {
        if (original.length !== improved.length) {
            changes.push('Code structure improved');
        }
        if (improved.includes('def ') && !original.includes('def ')) {
            changes.push('Function definition added');
        }
        if (improved.includes('"""') || improved.includes("'''")) {
            changes.push('Documentation added');
        }
        if (improved.includes('type:') || improved.includes('->')) {
            changes.push('Type hints added');
        }
        changes.push('Style matched to your coding patterns');
    }
    
    return changes.slice(0, 5); // Limit to 5 changes
}

function hideSuggestion() {
    const suggestionPanel = document.getElementById('suggestion-panel');
    const suggestionEl = document.getElementById('suggestion'); // Old element (for backward compatibility)
    const noSuggestionEl = document.getElementById('no-suggestion');
    const loadingEl = document.getElementById('loading-suggestion');
    
    if (suggestionPanel) suggestionPanel.style.display = 'none';
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

// Code Generation from User Input
const generateCodeBtn = document.getElementById('generate-code-btn');
const codeRequestInput = document.getElementById('code-request-input');
const generatedCodeSection = document.getElementById('generated-code');
const insertCodeBtn = document.getElementById('insert-code-btn');
const copyCodeBtn = document.getElementById('copy-code-btn');
const closeGeneratedBtn = document.getElementById('close-generated-btn');

if (generateCodeBtn) {
    generateCodeBtn.addEventListener('click', async () => {
        await generateCodeFromRequest();
    });
}

if (codeRequestInput) {
    codeRequestInput.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
            await generateCodeFromRequest();
        }
    });
}

if (insertCodeBtn) {
    insertCodeBtn.addEventListener('click', () => {
        const code = document.getElementById('generated-code-content').textContent;
        if (editor && code) {
            const currentCode = editor.getValue();
            const newCode = currentCode.trim() ? `${currentCode}\n\n${code}` : code;
            editor.setValue(newCode);
            hideGeneratedCode();
            updateStatus('Code inserted!', 'success');
        }
    });
}

if (copyCodeBtn) {
    copyCodeBtn.addEventListener('click', () => {
        const code = document.getElementById('generated-code-content').textContent;
        if (code) {
            navigator.clipboard.writeText(code).then(() => {
                updateStatus('Code copied!', 'success');
                setTimeout(() => updateStatus('Ready', 'info'), 2000);
            });
        }
    });
}

if (closeGeneratedBtn) {
    closeGeneratedBtn.addEventListener('click', () => {
        hideGeneratedCode();
    });
}

async function generateCodeFromRequest() {
    const request = codeRequestInput.value.trim();
    const techStackInput = document.getElementById('tech-stack-input');
    const techStack = techStackInput ? techStackInput.value.trim() : '';
    const languageSelector = document.getElementById('language-selector');
    const selectedLanguage = languageSelector ? languageSelector.value : 'python';
    
    // Helper function to get language selector (reuse the one declared above)
    const getLangSelector = () => languageSelector || document.getElementById('language-selector');
    
    if (!request && !selectedTemplate) {
        updateStatus('Please enter a request or select a template', 'warning');
        return;
    }
    
    // Get style profile if available, otherwise use default
    let styleProfile;
    let healthReport = null;
    try {
        styleProfile = await getStyleProfile();
        
        // Try to get GitHub health report from user profile
        try {
            if (typeof getCurrentUser === 'function') {
                const userData = await getCurrentUser();
                if (userData && userData.success && userData.user_profile && userData.user_profile.github_health_report) {
                    healthReport = userData.user_profile.github_health_report;
                    console.log('Found GitHub health report with', healthReport.bad_patterns?.length || 0, 'issues');
                }
            }
        } catch (e) {
            console.log('No GitHub health report available:', e);
        }
    } catch (error) {
        console.log('Error getting style profile:', error);
        styleProfile = null;
    }
    
    // Use default if no profile found
    if (!styleProfile) {
        styleProfile = {
            naming_style: 'snake_case',
            naming_confidence: 80,
            documentation_percentage: 50,
            type_hints_percentage: 30,
            code_quality_score: 70
        };
    }
    
    // Build the full request - focus on fixing errors found by AI recommender
    let fullRequest = request;
    
    // Get current code to check for errors
    const currentCode = editor ? editor.getValue() : '';
    
    // If there's existing code, focus on fixing errors
    if (currentCode && currentCode.trim() && currentCode !== '# Start typing your Python code here...\n\n') {
        fullRequest = `Fix errors and improve this code based on AI recommendations: ${request}`;
    }
    
    if (techStack) {
        fullRequest += ` using ${techStack}`;
    }
    
    // Add style profile context to request
    if (styleProfile) {
        fullRequest += `. Match my coding style: ${styleProfile.naming_style || 'snake_case'} naming, ${styleProfile.documentation_percentage || 0}% documentation, ${styleProfile.type_hints_percentage || 0}% type hints.`;
    }
    
    updateStatus('Generating code...', 'loading');
    showLoadingSuggestion('Generating code matching your style...');
    hideGeneratedCode();
    
    try {
        const response = await fetch(`${window.API_BASE}/api/generate-code`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                request: fullRequest,
                style_profile: styleProfile,
                language: selectedLanguage,
                template: selectedTemplate,
                tech_stack: techStack,
                health_report: healthReport  // Include health report if available
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            hideLoadingSuggestion();
            
            // Store generated code for accept/reject
            window.generatedCodeData = data;
            
            // Check if it's multi-file generation
            if (data.files && Array.isArray(data.files) && data.files.length > 0) {
                // Show accept/reject dialog for multi-file generation
                showAcceptRejectDialog(data.files, data.explanation || 'Code generated', true);
            } else if (data.code) {
                // Single file - show accept/reject dialog
                showAcceptRejectDialog([{ code: data.code, filename: 'generated.py' }], data.explanation || 'Code generated', false);
            } else {
                hideLoadingSuggestion();
                updateStatus('No code generated', 'error');
                return;
            }
            
            codeRequestInput.value = ''; // Clear input
            if (techStackInput) techStackInput.value = ''; // Clear tech stack
            // Clear template selection (template buttons removed, so no need to clear)
            selectedTemplate = null;
        } else {
            hideLoadingSuggestion();
            const errorMsg = data.error || 'Unable to generate code';
            updateStatus(errorMsg, 'error');
            if (typeof showToast === 'function') {
                showToast(errorMsg, 'error');
            }
        }
    } catch (error) {
        hideLoadingSuggestion();
        const errorMsg = 'Network error: ' + (error.message || 'Failed to connect to server');
        updateStatus(errorMsg, 'error');
        console.error('Code generation error:', error);
        if (typeof showToast === 'function') {
            showToast(errorMsg, 'error');
        }
    }
}

function displayGeneratedCode(code, explanation) {
    const generatedEl = document.getElementById('generated-code');
    const noSuggestionEl = document.getElementById('no-suggestion');
    const suggestionEl = document.getElementById('suggestion');
    const loadingEl = document.getElementById('loading-suggestion');
    const singleFileDisplay = document.getElementById('single-file-display');
    const multiFileDisplay = document.getElementById('multi-file-display');
    
    if (generatedEl) {
        // Show single file display, hide multi-file
        if (singleFileDisplay) singleFileDisplay.style.display = 'block';
        if (multiFileDisplay) multiFileDisplay.style.display = 'none';
        
        document.getElementById('generated-code-content').textContent = code;
        document.getElementById('generated-explanation').textContent = explanation;
        generatedEl.style.display = 'block';
    }
    
    if (noSuggestionEl) noSuggestionEl.style.display = 'none';
    if (suggestionEl) suggestionEl.style.display = 'none';
    if (loadingEl) loadingEl.style.display = 'none';
}

function displayMultiFileCode(files, explanation) {
    const generatedEl = document.getElementById('generated-code');
    const noSuggestionEl = document.getElementById('no-suggestion');
    const suggestionEl = document.getElementById('suggestion');
    const loadingEl = document.getElementById('loading-suggestion');
    const singleFileDisplay = document.getElementById('single-file-display');
    const multiFileDisplay = document.getElementById('multi-file-display');
    const multiFileList = document.getElementById('multi-file-list');
    
    if (generatedEl && multiFileList) {
        // Show multi-file display, hide single file
        if (singleFileDisplay) singleFileDisplay.style.display = 'none';
        if (multiFileDisplay) multiFileDisplay.style.display = 'block';
        
        document.getElementById('generated-explanation').textContent = explanation;
        
        // Clear previous files
        multiFileList.innerHTML = '';
        
        // Display each file with accept/reject buttons
        files.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'multi-file-item';
            fileItem.dataset.index = index;
            
            const filename = file.filename || file.name || `file${index + 1}.${getFileExtension(file.code || file.content)}`;
            const code = file.code || file.content || '';
            
            fileItem.innerHTML = `
                <div class="multi-file-item-header">
                    <span class="filename">📄 ${filename}</span>
                    <div class="multi-file-item-actions">
                        <button class="btn btn-success btn-small accept-file-btn" data-index="${index}" style="background: #10b981; color: white; padding: 6px 12px; font-size: 0.85rem;">✅ Accept</button>
                        <button class="btn btn-danger btn-small reject-file-btn" data-index="${index}" style="background: #ef4444; color: white; padding: 6px 12px; font-size: 0.85rem;">❌ Reject</button>
                    </div>
                </div>
                <div class="multi-file-item-code">
                    <pre><code>${escapeHtml(code)}</code></pre>
                </div>
            `;
            
            multiFileList.appendChild(fileItem);
        });
        
        // Add event listeners for accept/reject buttons
        document.querySelectorAll('.accept-file-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const index = parseInt(btn.dataset.index);
                acceptFile(files[index], index);
            });
        });
        
        document.querySelectorAll('.reject-file-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const index = parseInt(btn.dataset.index);
                rejectFile(index);
            });
        });
        
        // Accept All button
        const acceptAllBtn = document.getElementById('accept-all-btn');
        if (acceptAllBtn) {
            acceptAllBtn.onclick = () => {
                files.forEach((file, index) => {
                    acceptFile(file, index, true);
                });
                hideGeneratedCode();
                updateStatus('All files accepted and applied!', 'success');
            };
        }
        
        // Reject All button
        const rejectAllBtn = document.getElementById('reject-all-btn');
        if (rejectAllBtn) {
            rejectAllBtn.onclick = () => {
                hideGeneratedCode();
                updateStatus('All files rejected', 'info');
            };
        }
        
        generatedEl.style.display = 'block';
    }
    
    if (noSuggestionEl) noSuggestionEl.style.display = 'none';
    if (suggestionEl) suggestionEl.style.display = 'none';
    if (loadingEl) loadingEl.style.display = 'none';
}

function acceptFile(file, index, isAcceptAll = false) {
    if (!editor) return;
    
    const filename = file.filename || file.name || `file${index + 1}.${getFileExtension(file.code || file.content)}`;
    const code = file.code || file.content || '';
    
    // Get current editor content
    const currentCode = editor.getValue();
    
    // Create file header comment
    const fileHeader = `# File: ${filename}\n# Generated by CodeMind\n\n`;
    
    // Append to editor
    const newCode = currentCode.trim() 
        ? `${currentCode}\n\n${'='.repeat(60)}\n${fileHeader}${code}`
        : `${fileHeader}${code}`;
    
    editor.setValue(newCode);
    
    // Update language if needed
    const languageSelector = document.getElementById('language-selector');
    if (languageSelector) {
        const detectedLang = detectLanguageFromCode(code);
        if (detectedLang && languageSelector.value !== detectedLang) {
            languageSelector.value = detectedLang;
            monaco.editor.setModelLanguage(editor.getModel(), detectedLang);
        }
    }
    
    // Remove the file from display if not accepting all
    if (!isAcceptAll) {
        const fileItem = document.querySelector(`.multi-file-item[data-index="${index}"]`);
        if (fileItem) {
            fileItem.style.opacity = '0.5';
            fileItem.querySelector('.accept-file-btn').disabled = true;
            fileItem.querySelector('.reject-file-btn').disabled = true;
        }
    }
    
    if (!isAcceptAll) {
        updateStatus(`File "${filename}" accepted and applied!`, 'success');
    }
}

function rejectFile(index) {
    const fileItem = document.querySelector(`.multi-file-item[data-index="${index}"]`);
    if (fileItem) {
        fileItem.style.opacity = '0.3';
        fileItem.querySelector('.accept-file-btn').disabled = true;
        fileItem.querySelector('.reject-file-btn').disabled = true;
        updateStatus('File rejected', 'info');
    }
}

// Selection context menu functions
let selectionContextMenu = null;
let currentSelection = null;

function showSelectionContextMenu(selection) {
    // Get selected text
    const selectedText = editor.getModel().getValueInRange(selection);
    if (!selectedText || selectedText.trim().length === 0) {
        return;
    }
    
    // Store current selection
    currentSelection = selection;
    
    // Remove existing menu if it exists
    if (selectionContextMenu) {
        selectionContextMenu.remove();
    }
    
    // Create context menu
    selectionContextMenu = document.createElement('div');
    selectionContextMenu.className = 'selection-context-menu';
    selectionContextMenu.style.zIndex = '10000'; // Ensure it's on top
    selectionContextMenu.innerHTML = `
        <div class="context-menu-item" id="edit-with-ai">
            <span class="menu-icon">✨</span>
            <span>Edit with AI</span>
        </div>
        <div class="context-menu-item" id="change-language">
            <span class="menu-icon">🔄</span>
            <span>Change Programming Language</span>
            <span class="menu-arrow">▶</span>
        </div>
        <div class="language-submenu" id="language-submenu" style="display: none;">
            <div class="submenu-item" data-lang="python">Python</div>
            <div class="submenu-item" data-lang="java">Java</div>
            <div class="submenu-item" data-lang="c">C</div>
            <div class="submenu-item" data-lang="cpp">C++</div>
            <div class="submenu-item" data-lang="javascript">JavaScript</div>
            <div class="submenu-item" data-lang="typescript">TypeScript</div>
            <div class="submenu-item" data-lang="go">Go</div>
            <div class="submenu-item" data-lang="rust">Rust</div>
            <div class="submenu-item" data-lang="php">PHP</div>
            <div class="submenu-item" data-lang="ruby">Ruby</div>
        </div>
    `;
    
    document.body.appendChild(selectionContextMenu);
    
    // Position menu near selection - better positioning
    try {
        const position = editor.getScrolledVisiblePosition(selection.getStartPosition());
        const editorContainer = document.getElementById('monaco-editor');
        const rect = editorContainer.getBoundingClientRect();
        
        // Calculate position relative to viewport
        const menuTop = rect.top + (position.top || 0) - 10; // Position above selection
        const menuLeft = rect.left + (position.left || 0);
        
        // Ensure menu stays within viewport
        const menuRect = selectionContextMenu.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        let finalTop = menuTop;
        let finalLeft = menuLeft;
        
        // Adjust if menu would go off screen
        if (finalLeft + menuRect.width > viewportWidth) {
            finalLeft = viewportWidth - menuRect.width - 10;
        }
        if (finalTop + menuRect.height > viewportHeight) {
            finalTop = rect.top + (position.top || 0) - menuRect.height - 10; // Position above
        }
        if (finalTop < 0) {
            finalTop = rect.top + (position.top || 0) + 20; // Position below if no room above
        }
        if (finalLeft < 0) {
            finalLeft = 10;
        }
        
        selectionContextMenu.style.top = `${finalTop}px`;
        selectionContextMenu.style.left = `${finalLeft}px`;
        selectionContextMenu.style.position = 'fixed'; // Use fixed positioning
    } catch (error) {
        console.error('Error positioning menu:', error);
        // Fallback positioning
        selectionContextMenu.style.top = '50%';
        selectionContextMenu.style.left = '50%';
        selectionContextMenu.style.transform = 'translate(-50%, -50%)';
        selectionContextMenu.style.position = 'fixed';
    }
    
    // Prevent clicks on menu from hiding it
    selectionContextMenu.addEventListener('mousedown', (e) => {
        e.stopPropagation();
    });
    
    selectionContextMenu.addEventListener('click', (e) => {
        e.stopPropagation();
    });
    
    // Event listeners
    const editWithAI = selectionContextMenu.querySelector('#edit-with-ai');
    const changeLanguage = selectionContextMenu.querySelector('#change-language');
    const languageSubmenu = selectionContextMenu.querySelector('#language-submenu');
    const submenuItems = selectionContextMenu.querySelectorAll('.submenu-item');
    
    editWithAI.addEventListener('click', (e) => {
        e.stopPropagation();
        e.preventDefault();
        editSelectedCodeWithAI(selection, selectedText);
        hideSelectionContextMenu();
    });
    
    changeLanguage.addEventListener('click', (e) => {
        e.stopPropagation();
        e.preventDefault();
        const isVisible = languageSubmenu.style.display !== 'none';
        languageSubmenu.style.display = isVisible ? 'none' : 'block';
    });
    
    submenuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            const targetLang = item.dataset.lang;
            convertSelectedCodeToLanguage(selection, selectedText, targetLang);
            hideSelectionContextMenu();
        });
    });
}

function hideSelectionContextMenu() {
    if (selectionContextMenu) {
        selectionContextMenu.remove();
        selectionContextMenu = null;
    }
    currentSelection = null;
}

async function editSelectedCodeWithAI(selection, selectedText) {
    if (!editor || !selectedText) return;
    
    updateStatus('Editing code with AI...', 'loading');
    
    try {
        const styleProfile = await getStyleProfile() || {};
        
        const response = await fetch(`${window.API_BASE}/api/generate-code`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                request: `Improve and optimize this code:\n\n${selectedText}`,
                style_profile: styleProfile,
                language: editor.getModel().getLanguageId()
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success && data.code) {
            // Replace selected text with improved code
            editor.executeEdits('edit-with-ai', [{
                range: selection,
                text: data.code
            }]);
            updateStatus('Code improved with AI!', 'success');
        } else {
            updateStatus(data.error || 'Unable to edit code', 'error');
        }
    } catch (error) {
        updateStatus('Error editing code', 'error');
        console.error('Error editing code:', error);
    }
}

async function convertSelectedCodeToLanguage(selection, selectedText, targetLanguage) {
    if (!editor || !selectedText) return;
    
    const sourceLanguage = editor.getModel().getLanguageId();
    
    if (sourceLanguage === targetLanguage) {
        updateStatus('Code is already in the selected language', 'info');
        return;
    }
    
    updateStatus(`Converting code to ${targetLanguage}...`, 'loading');
    
    try {
        const styleProfile = await getStyleProfile() || {};
        
        const languageNames = {
            'python': 'Python',
            'java': 'Java',
            'c': 'C',
            'cpp': 'C++',
            'javascript': 'JavaScript',
            'typescript': 'TypeScript',
            'go': 'Go',
            'rust': 'Rust',
            'php': 'PHP',
            'ruby': 'Ruby'
        };
        
        const response = await fetch(`${window.API_BASE}/api/generate-code`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                request: `Convert this ${languageNames[sourceLanguage] || sourceLanguage} code to ${languageNames[targetLanguage] || targetLanguage}. Maintain the same functionality and logic:\n\n${selectedText}`,
                style_profile: styleProfile,
                language: targetLanguage
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success && data.code) {
            // Replace selected text with converted code
            editor.executeEdits('convert-language', [{
                range: selection,
                text: data.code
            }]);
            
            // Update editor language if converting entire file
            const fullCode = editor.getValue();
            if (fullCode === selectedText || fullCode.trim() === selectedText.trim()) {
                monaco.editor.setModelLanguage(editor.getModel(), targetLanguage);
                const languageSelector = document.getElementById('language-selector');
                if (languageSelector) {
                    languageSelector.value = targetLanguage;
                }
            }
            
            updateStatus(`Code converted to ${languageNames[targetLanguage] || targetLanguage}!`, 'success');
        } else {
            updateStatus(data.error || 'Unable to convert code', 'error');
        }
    } catch (error) {
        updateStatus('Error converting code', 'error');
        console.error('Error converting code:', error);
    }
}

function getFileExtension(code) {
    // Try to detect extension from code content
    if (code.includes('def ') || code.includes('import ') || code.includes('from ')) return 'py';
    if (code.includes('function ') || code.includes('const ') || code.includes('let ')) return 'js';
    if (code.includes('interface ') || code.includes('type ')) return 'ts';
    if (code.includes('public class ') || code.includes('import java.')) return 'java';
    if (code.includes('<!DOCTYPE') || code.includes('<html')) return 'html';
    if (code.includes('{') && code.includes('}') && code.includes(':')) return 'css';
    return 'txt';
}

function detectLanguageFromCode(code) {
    if (code.includes('def ') || code.includes('import ') || code.includes('from ')) return 'python';
    if (code.includes('function ') || code.includes('const ') || code.includes('let ')) return 'javascript';
    if (code.includes('interface ') || code.includes('type ')) return 'typescript';
    if (code.includes('public class ') || code.includes('import java.')) return 'java';
    if (code.includes('<!DOCTYPE') || code.includes('<html')) return 'html';
    if (code.includes('{') && code.includes('}') && code.includes(':')) return 'css';
    return 'python';
}

// VS Code Menu Functionality
function initializeVSCodeMenu() {
    // Wait for editor to be initialized
    if (!editor) {
        // Retry after a short delay if editor is not ready
        setTimeout(() => {
            if (editor) {
                initializeVSCodeMenu();
            }
        }, 100);
        return;
    }
    
    let currentFontSize = 14;
    let isMinimapEnabled = false;
    let isWordWrapEnabled = false;
    let isTerminalVisible = false;
    
    // File Menu
    document.getElementById('new-file')?.addEventListener('click', () => {
        if (editor) {
            editor.setValue('');
            updateStatus('New file created', 'success');
        }
    });
    
    document.getElementById('open-file')?.addEventListener('click', () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.py,.js,.ts,.java,.html,.css,.json,.md,.txt';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    editor.setValue(event.target.result);
                    const lang = detectLanguageFromCode(event.target.result);
                    monaco.editor.setModelLanguage(editor.getModel(), lang);
                    const langSelector = document.getElementById('language-selector');
                    if (langSelector) langSelector.value = lang;
                    updateStatus(`File opened: ${file.name}`, 'success');
                };
                reader.readAsText(file);
            }
        };
        input.click();
    });
    
    document.getElementById('save-file')?.addEventListener('click', () => {
        const code = editor.getValue();
        const blob = new Blob([code], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `code.${editor.getModel().getLanguageId() || 'txt'}`;
        a.click();
        URL.revokeObjectURL(url);
        updateStatus('File saved', 'success');
    });
    
    document.getElementById('save-as-file')?.addEventListener('click', () => {
        const code = editor.getValue();
        const lang = editor.getModel().getLanguageId() || 'txt';
        const filename = prompt('Enter filename:', `code.${lang}`);
        if (filename) {
            const blob = new Blob([code], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
            updateStatus(`File saved as: ${filename}`, 'success');
        }
    });
    
    document.getElementById('download-file')?.addEventListener('click', () => {
        const code = editor.getValue();
        const blob = new Blob([code], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `code.${editor.getModel().getLanguageId() || 'txt'}`;
        a.click();
        URL.revokeObjectURL(url);
        updateStatus('File downloaded', 'success');
    });
    
    // Edit Menu
    document.getElementById('undo-action')?.addEventListener('click', () => {
        editor.trigger('editor', 'undo');
        updateStatus('Undo', 'info');
    });
    
    document.getElementById('redo-action')?.addEventListener('click', () => {
        editor.trigger('editor', 'redo');
        updateStatus('Redo', 'info');
    });
    
    document.getElementById('cut-action')?.addEventListener('click', () => {
        editor.trigger('editor', 'editor.action.clipboardCutAction');
        updateStatus('Cut', 'info');
    });
    
    document.getElementById('copy-action')?.addEventListener('click', () => {
        editor.trigger('editor', 'editor.action.clipboardCopyAction');
        updateStatus('Copied', 'success');
    });
    
    document.getElementById('paste-action')?.addEventListener('click', () => {
        editor.trigger('editor', 'editor.action.clipboardPasteAction');
        updateStatus('Pasted', 'success');
    });
    
    document.getElementById('find-action')?.addEventListener('click', () => {
        editor.trigger('editor', 'actions.find');
        updateStatus('Find', 'info');
    });
    
    document.getElementById('replace-action')?.addEventListener('click', () => {
        editor.trigger('editor', 'editor.action.startFindReplaceAction');
        updateStatus('Replace', 'info');
    });
    
    document.getElementById('find-all-action')?.addEventListener('click', () => {
        editor.trigger('editor', 'editor.action.changeAll');
        updateStatus('Find All', 'info');
    });
    
    // View Menu
    document.getElementById('zoom-in')?.addEventListener('click', () => {
        currentFontSize += 2;
        editor.updateOptions({ fontSize: currentFontSize });
        updateStatus(`Zoom: ${currentFontSize}px`, 'info');
    });
    
    document.getElementById('zoom-out')?.addEventListener('click', () => {
        currentFontSize = Math.max(8, currentFontSize - 2);
        editor.updateOptions({ fontSize: currentFontSize });
        updateStatus(`Zoom: ${currentFontSize}px`, 'info');
    });
    
    document.getElementById('reset-zoom')?.addEventListener('click', () => {
        currentFontSize = 14;
        editor.updateOptions({ fontSize: currentFontSize });
        updateStatus('Zoom reset', 'success');
    });
    
    document.getElementById('toggle-theme')?.addEventListener('click', () => {
        const currentTheme = editor._themeService.getColorTheme().themeName;
        const newTheme = currentTheme === 'vs-dark' ? 'vs' : 'vs-dark';
        monaco.editor.setTheme(newTheme);
        updateStatus(`Theme: ${newTheme}`, 'success');
    });
    
    document.getElementById('toggle-minimap')?.addEventListener('click', () => {
        isMinimapEnabled = !isMinimapEnabled;
        editor.updateOptions({ minimap: { enabled: isMinimapEnabled } });
        updateStatus(`Minimap: ${isMinimapEnabled ? 'enabled' : 'disabled'}`, 'success');
    });
    
    document.getElementById('toggle-word-wrap')?.addEventListener('click', () => {
        isWordWrapEnabled = !isWordWrapEnabled;
        editor.updateOptions({ wordWrap: isWordWrapEnabled ? 'on' : 'off' });
        updateStatus(`Word wrap: ${isWordWrapEnabled ? 'on' : 'off'}`, 'success');
    });
    
    // Run Menu - Execute code with auto-install requirements
    document.getElementById('run-code')?.addEventListener('click', async () => {
        await runCode();
    });
    
    // Save current file when editor content changes
    if (editor) {
        editor.onDidChangeModelContent(() => {
            if (window.currentFile) {
                window.fileSystem[window.currentFile] = editor.getValue();
            }
        });
    }
    
    document.getElementById('debug-code')?.addEventListener('click', () => {
        updateStatus('Debug mode (simulated)', 'info');
        // Debug functionality can be enhanced later
    });
    
    document.getElementById('format-code')?.addEventListener('click', () => {
        editor.trigger('editor', 'editor.action.formatDocument');
        updateStatus('Document formatted', 'success');
    });
    
    // Terminal Menu
    document.getElementById('new-terminal')?.addEventListener('click', () => {
        const terminalPanel = document.getElementById('terminal-panel');
        const terminalContent = document.getElementById('terminal-content');
        if (terminalPanel && terminalContent) {
            terminalPanel.style.display = 'flex';
            isTerminalVisible = true;
            terminalContent.textContent = '$ New terminal opened\n';
            updateStatus('Terminal opened', 'success');
        }
    });
    
    document.getElementById('toggle-terminal')?.addEventListener('click', () => {
        const terminalPanel = document.getElementById('terminal-panel');
        if (terminalPanel) {
            isTerminalVisible = !isTerminalVisible;
            terminalPanel.style.display = isTerminalVisible ? 'flex' : 'none';
            updateStatus(`Terminal: ${isTerminalVisible ? 'shown' : 'hidden'}`, 'success');
        }
    });
    
    document.getElementById('close-terminal-btn')?.addEventListener('click', () => {
        const terminalPanel = document.getElementById('terminal-panel');
        if (terminalPanel) {
            terminalPanel.style.display = 'none';
            isTerminalVisible = false;
            updateStatus('Terminal closed', 'info');
        }
    });
    
    // Settings Button
    document.getElementById('settings-btn')?.addEventListener('click', () => {
        updateStatus('Settings (coming soon)', 'info');
        // Settings modal can be added later
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            if (e.key === 's') {
                e.preventDefault();
                document.getElementById('save-file')?.click();
            } else if (e.key === 'o') {
                e.preventDefault();
                document.getElementById('open-file')?.click();
            } else if (e.key === 'n') {
                e.preventDefault();
                document.getElementById('new-file')?.click();
            } else if (e.key === 'f') {
                e.preventDefault();
                document.getElementById('find-action')?.click();
            } else if (e.key === 'h') {
                e.preventDefault();
                document.getElementById('replace-action')?.click();
            } else if (e.key === '=' || e.key === '+') {
                e.preventDefault();
                document.getElementById('zoom-in')?.click();
            } else if (e.key === '-') {
                e.preventDefault();
                document.getElementById('zoom-out')?.click();
            }
        }
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function hideGeneratedCode() {
    const generatedEl = document.getElementById('generated-code');
    if (generatedEl) {
        generatedEl.style.display = 'none';
    }
}

function showLoadingSuggestion(text = 'Analyzing your code...') {
    const loadingText = document.getElementById('loading-text');
    if (loadingText) {
        loadingText.textContent = text;
    }
    
    const suggestionEl = document.getElementById('suggestion');
    const noSuggestionEl = document.getElementById('no-suggestion');
    const generatedEl = document.getElementById('generated-code');
    const loadingEl = document.getElementById('loading-suggestion');
    
    if (suggestionEl) suggestionEl.style.display = 'none';
    if (noSuggestionEl) noSuggestionEl.style.display = 'none';
    if (generatedEl) generatedEl.style.display = 'none';
    if (loadingEl) loadingEl.style.display = 'block';
}

function hideLoadingSuggestion() {
    const loadingEl = document.getElementById('loading-suggestion');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
}

// Beginner mode: Get multiple style suggestions
async function getBeginnerSuggestions(code) {
    if (!code || code.length < 10) {
        return;
    }
    
    updateStatus('Generating style options...', 'loading');
    showLoadingSuggestion();
    
    try {
        const response = await fetch(`${window.API_BASE}/api/get-beginner-suggestions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                code: code,
                filename: 'code.py'
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success && data.options) {
            displayBeginnerOptions(data.options, code);
            updateStatus('Choose your preferred style!', 'success');
        } else {
            hideLoadingSuggestion();
            updateStatus(data.error || 'Could not generate suggestions', 'error');
        }
    } catch (error) {
        hideLoadingSuggestion();
        updateStatus('Network error', 'error');
    }
}

// Display beginner mode style options
function displayBeginnerOptions(options, originalCode) {
    const beginnerOptionsEl = document.getElementById('beginner-options');
    const styleOptionsList = document.getElementById('style-options-list');
    const noSuggestionEl = document.getElementById('no-suggestion');
    const suggestionEl = document.getElementById('suggestion');
    const loadingEl = document.getElementById('loading-suggestion');
    
    if (!beginnerOptionsEl || !styleOptionsList) return;
    
    // Hide other elements
    if (noSuggestionEl) noSuggestionEl.style.display = 'none';
    if (suggestionEl) suggestionEl.style.display = 'none';
    if (loadingEl) loadingEl.style.display = 'none';
    
    // Store options for later use
    currentStyleOptions = options;
    
    // Clear previous options
    styleOptionsList.innerHTML = '';
    
    // Display each option
    options.forEach((option, index) => {
        const optionCard = document.createElement('div');
        optionCard.className = 'style-option-card';
        optionCard.style.cssText = `
            background: var(--bg-light);
            border: 2px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.2s;
        `;
        
        optionCard.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h5 style="margin: 0; color: var(--text-primary); font-size: 1rem;">${option.label}</h5>
                <span style="font-size: 0.85rem; color: var(--text-secondary);">${option.description}</span>
            </div>
            <pre style="background: #0a0e17; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 0.85rem; margin: 0;"><code>${escapeHtml(option.code)}</code></pre>
        `;
        
        optionCard.addEventListener('click', () => {
            selectStyleOption(option, originalCode);
        });
        
        optionCard.addEventListener('mouseenter', () => {
            optionCard.style.borderColor = 'var(--primary-color)';
            optionCard.style.transform = 'translateY(-2px)';
        });
        
        optionCard.addEventListener('mouseleave', () => {
            optionCard.style.borderColor = 'var(--border-color)';
            optionCard.style.transform = 'translateY(0)';
        });
        
        styleOptionsList.appendChild(optionCard);
    });
    
    // Show beginner options
    beginnerOptionsEl.style.display = 'block';
    
    // Skip button
    const skipBtn = document.getElementById('skip-style-btn');
    if (skipBtn) {
        skipBtn.onclick = () => {
            beginnerOptionsEl.style.display = 'none';
            if (noSuggestionEl) noSuggestionEl.style.display = 'block';
        };
    }
}

// Handle style option selection in beginner mode
async function selectStyleOption(option, originalCode) {
    if (!editor) return;
    
    // Apply the selected code to editor
    editor.setValue(option.code);
    
    // Hide beginner options
    const beginnerOptionsEl = document.getElementById('beginner-options');
    if (beginnerOptionsEl) {
        beginnerOptionsEl.style.display = 'none';
    }
    
    // Learn from this interaction
    try {
        const token = localStorage.getItem('token');
        if (token) {
            const response = await fetch(`${window.API_BASE}/api/learn-from-interaction`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    code: originalCode,
                    selected_style: option.id,
                    style_options: currentStyleOptions
                })
            });
            
            const data = await response.json();
            if (data.success) {
                updateStatus(`Learned from your choice! (${data.interactions} interactions)`, 'success');
                // Update local profile if available
                if (data.profile) {
                    saveStyleProfile(data.profile);
                }
            }
        } else {
            updateStatus('Style applied! Sign in to save your preferences.', 'info');
        }
    } catch (error) {
        console.error('Error learning from interaction:', error);
        updateStatus('Style applied!', 'success');
    }
}

// File System Storage (in-memory)
window.fileSystem = window.fileSystem || {};
window.currentFile = window.currentFile || null;

// VS Code Sidebar Functionality
function initializeSidebar() {
    // Toggle Sidebar
    const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
    const sidebar = document.getElementById('vscode-sidebar');
    if (toggleSidebarBtn && sidebar) {
        toggleSidebarBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            toggleSidebarBtn.textContent = sidebar.classList.contains('collapsed') ? '▶' : '◀';
        });
    }
    
    // New Folder
    const newFolderBtn = document.getElementById('new-folder-btn');
    if (newFolderBtn) {
        newFolderBtn.addEventListener('click', () => {
            const folderName = prompt('Enter folder name:');
            if (folderName) {
                addFolderToTree(folderName);
                if (typeof showToast === 'function') {
                    showToast(`Folder "${folderName}" created`, 'success');
                }
            }
        });
    }
    
    // New File (Sidebar)
    const newFileSidebarBtn = document.getElementById('new-file-sidebar-btn');
    if (newFileSidebarBtn) {
        newFileSidebarBtn.addEventListener('click', () => {
            const fileName = prompt('Enter file name (e.g., app.py):');
            if (fileName) {
                addFileToTree(fileName);
                if (editor) {
                    editor.setValue('');
                    const lang = getLanguageFromFileName(fileName);
                    monaco.editor.setModelLanguage(editor.getModel(), lang);
                    const langSelector = document.getElementById('language-selector');
                    if (langSelector) langSelector.value = lang;
                }
                if (typeof showToast === 'function') {
                    showToast(`File "${fileName}" created`, 'success');
                }
            }
        });
    }
    
    // Check GitHub connection status
    checkGitHubConnection();
    
    // Connect GitHub Button
    document.getElementById('connect-github-btn')?.addEventListener('click', () => {
        showGitHubConnectionModal();
    });
    
    // Close GitHub Modal
    document.getElementById('close-github-modal-btn')?.addEventListener('click', () => {
        hideGitHubConnectionModal();
    });
    
    // Connect GitHub Submit
    document.getElementById('connect-github-submit-btn')?.addEventListener('click', async () => {
        await connectGitHub();
    });
    
    // Disconnect GitHub
    document.getElementById('git-disconnect-btn')?.addEventListener('click', async () => {
        await disconnectGitHub();
    });
    
    // Create Repository Button
    document.getElementById('create-repo-btn')?.addEventListener('click', () => {
        showCreateRepoModal();
    });
    
    // Close Create Repo Modal
    document.getElementById('close-create-repo-modal-btn')?.addEventListener('click', () => {
        hideCreateRepoModal();
    });
    
    document.getElementById('close-create-repo-modal-btn-2')?.addEventListener('click', () => {
        hideCreateRepoModal();
    });
    
    // Create Repository Submit
    document.getElementById('create-repo-submit-btn')?.addEventListener('click', async () => {
        await createGitHubRepo();
    });
    
    // Git Actions
    document.getElementById('git-status-btn')?.addEventListener('click', async () => {
        await gitStatus();
    });
    
    document.getElementById('git-commit-btn')?.addEventListener('click', async () => {
        await gitCommit();
    });
    
    document.getElementById('git-push-btn')?.addEventListener('click', async () => {
        await gitPush();
    });
    
    document.getElementById('git-pull-btn')?.addEventListener('click', async () => {
        await gitPull();
    });
    
    // Run Actions (Sidebar)
    document.getElementById('run-code-sidebar-btn')?.addEventListener('click', () => {
        document.getElementById('run-code')?.click();
    });
    
    document.getElementById('debug-code-sidebar-btn')?.addEventListener('click', () => {
        document.getElementById('debug-code')?.click();
    });
    
    document.getElementById('format-code-sidebar-btn')?.addEventListener('click', () => {
        document.getElementById('format-code')?.click();
    });
    
    // File Tree Click - Open file in editor
    function setupFileTreeClick() {
        const fileTreeItems = document.querySelectorAll('.file-tree-item');
        fileTreeItems.forEach(item => {
            item.addEventListener('click', () => {
                fileTreeItems.forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                const fileName = item.dataset.file;
                if (fileName) {
                    openFileInEditor(fileName);
                }
            });
        });
    }
    
    // Setup initial file tree items
    setupFileTreeClick();
    
    // Re-setup when new files are added
    const originalAddFileToTree = addFileToTree;
    addFileToTree = function(fileName) {
        originalAddFileToTree(fileName);
        setupFileTreeClick();
    };
}

// Open file in editor
function openFileInEditor(fileName) {
    if (!editor) return;
    
    // Save current file if exists
    if (window.currentFile && window.fileSystem[window.currentFile]) {
        window.fileSystem[window.currentFile] = editor.getValue();
    }
    
    // Load file content
    let fileContent = '';
    if (window.fileSystem[fileName]) {
        // File exists in memory, load it
        fileContent = window.fileSystem[fileName];
    } else {
        // New file or file not in memory, check if it's in editor
        if (window.currentFile === fileName) {
            fileContent = editor.getValue();
        } else {
            // New file, initialize empty
            fileContent = '';
        }
        window.fileSystem[fileName] = fileContent;
    }
    
    // Set file content in editor
    editor.setValue(fileContent);
    
    // Set language based on file extension
    const lang = getLanguageFromFileName(fileName);
    monaco.editor.setModelLanguage(editor.getModel(), lang);
    
    // Update language selector
    const langSelector = document.getElementById('language-selector');
    if (langSelector) {
        langSelector.value = lang;
    }
    
    // Update current file
    window.currentFile = fileName;
    
    // Show toast
    if (typeof showToast === 'function') {
        showToast(`Opened: ${fileName}`, 'info');
    }
    
    // Update status
    updateStatus(`File: ${fileName}`, 'info');
}

// Save current file
function saveCurrentFile() {
    if (!editor || !window.currentFile) return;
    
    const content = editor.getValue();
    window.fileSystem[window.currentFile] = content;
    
    if (typeof showToast === 'function') {
        showToast(`Saved: ${window.currentFile}`, 'success');
    }
}

// Get main file from file system
function getMainFile() {
    const mainFiles = ['main.py', 'app.py', 'index.js', 'server.js', 'app.js', 'main.js', 'index.py', 'run.py'];
    
    // Check for main files in file system
    for (const mainFile of mainFiles) {
        if (window.fileSystem[mainFile]) {
            return mainFile;
        }
    }
    
    // If no main file found, use current file or first file
    if (window.currentFile) {
        return window.currentFile;
    }
    
    const files = Object.keys(window.fileSystem);
    if (files.length > 0) {
        return files[0];
    }
    
    return null;
}

function addFolderToTree(folderName) {
    const fileTree = document.getElementById('file-tree');
    if (fileTree) {
        const folderItem = document.createElement('div');
        folderItem.className = 'file-tree-item';
        folderItem.innerHTML = `
            <span class="file-icon">📁</span>
            <span class="file-name">${folderName}</span>
        `;
        fileTree.appendChild(folderItem);
    }
}

function addFileToTree(fileName) {
    const fileTree = document.getElementById('file-tree');
    if (fileTree) {
        // Check if file already exists
        const existingItem = fileTree.querySelector(`[data-file="${fileName}"]`);
        if (existingItem) {
            // File exists, just open it
            existingItem.click();
            return;
        }
        
        const fileItem = document.createElement('div');
        fileItem.className = 'file-tree-item';
        fileItem.dataset.file = fileName;
        const icon = getFileIcon(fileName);
        fileItem.innerHTML = `
            <span class="file-icon">${icon}</span>
            <span class="file-name">${fileName}</span>
        `;
        fileTree.appendChild(fileItem);
        
        // Initialize file in file system if not exists
        if (!window.fileSystem[fileName]) {
            window.fileSystem[fileName] = '';
        }
        
        // Add click handler to open file
        fileItem.addEventListener('click', () => {
            document.querySelectorAll('.file-tree-item').forEach(i => i.classList.remove('active'));
            fileItem.classList.add('active');
            openFileInEditor(fileName);
        });
    }
}

function getFileIcon(fileName) {
    const ext = fileName.split('.').pop().toLowerCase();
    const icons = {
        'py': '🐍', 'js': '📜', 'ts': '📘', 'java': '☕', 'html': '🌐',
        'css': '🎨', 'json': '📋', 'md': '📝', 'txt': '📄', 'jsx': '⚛️',
        'tsx': '⚛️', 'vue': '💚', 'go': '🐹', 'rs': '🦀', 'php': '🐘'
    };
    return icons[ext] || '📄';
}

function getLanguageFromFileName(fileName) {
    const ext = fileName.split('.').pop().toLowerCase();
    const langMap = {
        'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'java': 'java',
        'html': 'html', 'css': 'css', 'json': 'json', 'md': 'markdown',
        'cpp': 'cpp', 'c': 'c', 'go': 'go', 'rs': 'rust', 'rb': 'ruby',
        'php': 'php', 'swift': 'swift', 'kt': 'kotlin', 'scala': 'scala'
    };
    return langMap[ext] || 'python';
}

// Run Code Function
async function runCode() {
    if (!editor) {
        if (typeof showToast === 'function') {
            showToast('Editor not initialized', 'error');
        }
        return;
    }
    
    // Save current file
    saveCurrentFile();
    
    // Get main file or current file
    const mainFile = getMainFile();
    if (!mainFile) {
        if (typeof showToast === 'function') {
            showToast('No file to run. Please create or open a file.', 'warning');
        }
        updateStatus('No file to run', 'warning');
        return;
    }
    
    // Get all files in file system
    const files = {};
    Object.keys(window.fileSystem).forEach(fileName => {
        files[fileName] = window.fileSystem[fileName];
    });
    
    // Show terminal
    const terminalPanel = document.getElementById('terminal-panel');
    const terminalContent = document.getElementById('terminal-content');
    if (terminalPanel && terminalContent) {
        terminalPanel.style.display = 'flex';
        isTerminalVisible = true;
        terminalContent.innerHTML = `<div style="color: var(--text-secondary);">$ Running code...</div>`;
        // Scroll terminal to bottom
        terminalContent.scrollTop = terminalContent.scrollHeight;
    }
    
    updateStatus('Running code...', 'loading');
    
    try {
        // Call backend to run code
        const token = localStorage.getItem('token');
        const response = await fetch('/api/run-code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                files: files,
                mainFile: mainFile,
                currentFile: window.currentFile
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Display output in terminal
            let outputHtml = `<div style="color: var(--success); margin-bottom: 10px;">$ Code execution completed successfully!</div>\n`;
            
            if (data.installOutput) {
                outputHtml += `<div style="color: var(--info); margin-bottom: 10px; white-space: pre-wrap; font-family: monospace; background: var(--bg-secondary); padding: 10px; border-radius: 8px;">${escapeHtml(data.installOutput)}</div>\n`;
            }
            
            if (data.output) {
                outputHtml += `<div style="color: var(--text-primary); white-space: pre-wrap; font-family: monospace; background: var(--bg-card); padding: 10px; border-radius: 8px; margin-bottom: 10px;">${escapeHtml(data.output)}</div>\n`;
            }
            
            if (data.error) {
                outputHtml += `<div style="color: var(--error); white-space: pre-wrap; font-family: monospace; background: var(--error-bg); padding: 10px; border-radius: 8px; margin-bottom: 10px;">Error: ${escapeHtml(data.error)}</div>\n`;
            }
            
            if (data.url) {
                outputHtml += `<div style="margin-top: 15px; padding: 15px; background: var(--bg-card); border-radius: 12px; border: 2px solid var(--accent-primary);">`;
                outputHtml += `<div style="color: var(--text-primary); margin-bottom: 10px; font-weight: 600; font-size: 1.1rem;">🌐 Application Running:</div>`;
                outputHtml += `<a href="${data.url}" target="_blank" style="color: var(--accent-primary); text-decoration: underline; font-size: 1.2rem; font-weight: 700; word-break: break-all;">${data.url}</a>`;
                outputHtml += `<div style="color: var(--text-secondary); margin-top: 8px; font-size: 0.9rem;">Click to open in new tab</div>`;
                outputHtml += `</div>\n`;
            }
            
            if (terminalContent) {
                terminalContent.innerHTML = outputHtml;
                // Scroll terminal to bottom to show latest output
                terminalContent.scrollTop = terminalContent.scrollHeight;
            }
            
            // Ensure terminal is visible
            if (terminalPanel) {
                terminalPanel.style.display = 'flex';
                isTerminalVisible = true;
            }
            
            updateStatus('Code executed successfully', 'success');
            if (typeof showToast === 'function') {
                showToast('Code executed successfully!', 'success');
            }
        } else {
            // Error running code
            let errorHtml = `<div style="color: var(--error); margin-bottom: 10px;">$ Error running code</div>\n`;
            if (data.error) {
                errorHtml += `<div style="color: var(--error); white-space: pre-wrap; font-family: monospace; background: var(--error-bg); padding: 10px; border-radius: 8px;">${escapeHtml(data.error)}</div>\n`;
            }
            
            if (terminalContent) {
                terminalContent.innerHTML = errorHtml;
                // Scroll terminal to bottom to show error
                terminalContent.scrollTop = terminalContent.scrollHeight;
            }
            
            // Ensure terminal is visible
            if (terminalPanel) {
                terminalPanel.style.display = 'flex';
                isTerminalVisible = true;
            }
            
            updateStatus('Code execution failed', 'error');
            if (typeof showToast === 'function') {
                showToast(data.error || 'Code execution failed', 'error');
            }
        }
    } catch (error) {
        console.error('Error running code:', error);
        if (terminalContent) {
            terminalContent.innerHTML = `<div style="color: var(--error);">$ Error: ${escapeHtml(error.message)}</div>\n`;
        }
        updateStatus('Code execution failed', 'error');
        if (typeof showToast === 'function') {
            showToast('Failed to run code: ' + error.message, 'error');
        }
    }
}

// Escape HTML for terminal output
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Accept/Reject Dialog Functions
function showAcceptRejectDialog(files, explanation, isMultiFile) {
    const dialog = document.getElementById('accept-reject-dialog');
    const dialogExplanation = document.getElementById('dialog-explanation');
    const dialogFilesList = document.getElementById('dialog-files-list');
    
    if (!dialog) return;
    
    // Hide other panels
    hideGeneratedCode();
    hideSuggestion();
    document.getElementById('no-suggestion')?.style.setProperty('display', 'none');
    document.getElementById('loading-suggestion')?.style.setProperty('display', 'none');
    
    // Set explanation
    if (dialogExplanation) {
        dialogExplanation.textContent = explanation || 
            (isMultiFile ? `Generated ${files.length} files to address all issues. Review and accept to apply.` : 
             'Code generated. Review and accept to apply.');
    }
    
    // Display files
    if (dialogFilesList) {
        dialogFilesList.innerHTML = '';
        files.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'dialog-file-item';
            const fileName = file.filename || file.name || `file_${index + 1}.py`;
            const fileCode = file.code || file.content || '';
            const fileSize = fileCode.length;
            const icon = getFileIcon(fileName);
            
            fileItem.innerHTML = `
                <span class="file-icon">${icon}</span>
                <div class="file-info">
                    <div class="file-name">${fileName}</div>
                    <div class="file-size">${(fileSize / 1024).toFixed(2)} KB</div>
                </div>
            `;
            dialogFilesList.appendChild(fileItem);
        });
    }
    
    // Show dialog
    dialog.style.display = 'block';
    
    // Scroll to dialog
    dialog.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideAcceptRejectDialog() {
    const dialog = document.getElementById('accept-reject-dialog');
    if (dialog) {
        dialog.style.display = 'none';
    }
}

// Accept All Code
function acceptAllCode() {
    const data = window.generatedCodeData;
    if (!data) return;
    
    hideAcceptRejectDialog();
    
    if (data.files && Array.isArray(data.files) && data.files.length > 0) {
        // Multi-file: Insert first file into editor, add others to file tree
        const firstFile = data.files[0];
        const code = firstFile.code || firstFile.content || '';
        const filename = firstFile.filename || firstFile.name || 'generated.py';
        
        if (editor && code) {
            const langSelector = document.getElementById('language-selector');
            const currentLang = langSelector ? langSelector.value : 'python';
            const fileLang = detectLanguageFromCode(code) || getLanguageFromFileName(filename) || currentLang;
            
            // Insert first file into editor
            editor.setValue(code);
            monaco.editor.setModelLanguage(editor.getModel(), fileLang);
            
            if (langSelector) {
                langSelector.value = fileLang;
            }
            
            // Add other files to file tree
            for (let i = 1; i < data.files.length; i++) {
                const file = data.files[i];
                const fileName = file.filename || file.name || `file_${i + 1}.py`;
                addFileToTree(fileName);
            }
            
            updateStatus(`✅ Accepted! ${data.files.length} files applied. First file in editor.`, 'success');
            if (typeof showToast === 'function') {
                showToast(`✅ Accepted! ${data.files.length} files applied.`, 'success');
            }
        }
    } else if (data.code) {
        // Single file
        if (editor) {
            const code = data.code;
            const langSelector = document.getElementById('language-selector');
            const currentLang = langSelector ? langSelector.value : 'python';
            const detectedLang = detectLanguageFromCode(code) || currentLang;
            
            editor.setValue(code);
            monaco.editor.setModelLanguage(editor.getModel(), detectedLang);
            
            if (langSelector) {
                langSelector.value = detectedLang;
            }
            
            updateStatus('✅ Accepted! Code applied to editor.', 'success');
            if (typeof showToast === 'function') {
                showToast('✅ Accepted! Code applied to editor.', 'success');
            }
        }
    }
    
    // Clear generated data
    window.generatedCodeData = null;
}

// Reject All Code
function rejectAllCode() {
    hideAcceptRejectDialog();
    window.generatedCodeData = null;
    updateStatus('❌ Rejected. Code not applied.', 'info');
    if (typeof showToast === 'function') {
        showToast('❌ Rejected. Code not applied.', 'info');
    }
}

// Set up accept/reject button listeners (run immediately, DOM might already be loaded)
(function() {
    function setupAcceptRejectButtons() {
        const acceptBtn = document.getElementById('accept-all-code-btn');
        const rejectBtn = document.getElementById('reject-all-code-btn');
        
        if (acceptBtn && !acceptBtn.dataset.listenerAdded) {
            acceptBtn.addEventListener('click', acceptAllCode);
            acceptBtn.dataset.listenerAdded = 'true';
        }
        
        if (rejectBtn && !rejectBtn.dataset.listenerAdded) {
            rejectBtn.addEventListener('click', rejectAllCode);
            rejectBtn.dataset.listenerAdded = 'true';
        }
    }
    
    // Try immediately
    setupAcceptRejectButtons();
    
    // Also try on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupAcceptRejectButtons);
    } else {
        // DOM already loaded
        setTimeout(setupAcceptRejectButtons, 100);
    }
})();

// GitHub Connection Functions
async function checkGitHubConnection() {
    try {
        const userData = await getCurrentUser();
        if (userData && userData.success && userData.user_profile && userData.user_profile.github_connected) {
            showGitHubConnected();
        } else {
            showGitHubNotConnected();
        }
    } catch (e) {
        console.log('Error checking GitHub connection:', e);
        showGitHubNotConnected();
    }
}

function showGitHubConnected() {
    const connectedDiv = document.getElementById('github-connected');
    const notConnectedDiv = document.getElementById('github-not-connected');
    const statusIndicator = document.getElementById('github-connection-status');
    
    if (connectedDiv) connectedDiv.style.display = 'block';
    if (notConnectedDiv) notConnectedDiv.style.display = 'none';
    if (statusIndicator) {
        statusIndicator.style.display = 'inline';
        statusIndicator.textContent = '🔗';
        statusIndicator.title = 'GitHub Connected';
    }
}

function showGitHubNotConnected() {
    const connectedDiv = document.getElementById('github-connected');
    const notConnectedDiv = document.getElementById('github-not-connected');
    const statusIndicator = document.getElementById('github-connection-status');
    
    if (connectedDiv) connectedDiv.style.display = 'none';
    if (notConnectedDiv) notConnectedDiv.style.display = 'block';
    if (statusIndicator) statusIndicator.style.display = 'none';
}

function showGitHubConnectionModal() {
    const modal = document.getElementById('github-connection-modal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function hideGitHubConnectionModal() {
    const modal = document.getElementById('github-connection-modal');
    if (modal) {
        modal.style.display = 'none';
        // Clear inputs
        document.getElementById('github-token-input').value = '';
        document.getElementById('github-username-input').value = '';
    }
}

async function connectGitHub() {
    const tokenInput = document.getElementById('github-token-input');
    const usernameInput = document.getElementById('github-username-input');
    const submitBtn = document.getElementById('connect-github-submit-btn');
    
    const token = tokenInput?.value.trim();
    const username = usernameInput?.value.trim();
    
    if (!token) {
        if (typeof showToast === 'function') {
            showToast('Please enter a GitHub token', 'error');
        }
        return;
    }
    
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Connecting...';
    }
    
    try {
        const response = await fetch(`${window.API_BASE}/api/github/connect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({
                token: token,
                username: username
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            hideGitHubConnectionModal();
            showGitHubConnected();
            if (typeof showToast === 'function') {
                showToast(`✅ GitHub connected: ${data.username}`, 'success');
            }
        } else {
            if (typeof showToast === 'function') {
                showToast(data.error || 'Failed to connect GitHub', 'error');
            }
        }
    } catch (error) {
        if (typeof showToast === 'function') {
            showToast('Error connecting GitHub: ' + error.message, 'error');
        }
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = '🔗 Connect GitHub';
        }
    }
}

async function disconnectGitHub() {
    if (!confirm('Are you sure you want to disconnect your GitHub account?')) {
        return;
    }
    
    try {
        const response = await fetch(`${window.API_BASE}/api/github/disconnect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showGitHubNotConnected();
            if (typeof showToast === 'function') {
                showToast('GitHub account disconnected', 'info');
            }
        } else {
            if (typeof showToast === 'function') {
                showToast(data.error || 'Failed to disconnect', 'error');
            }
        }
    } catch (error) {
        if (typeof showToast === 'function') {
            showToast('Error disconnecting GitHub: ' + error.message, 'error');
        }
    }
}

// Create Repository Modal Functions
function showCreateRepoModal() {
    const modal = document.getElementById('create-repo-modal');
    if (modal) {
        modal.style.display = 'flex';
        // Clear form
        const nameInput = document.getElementById('repo-name-input');
        const descInput = document.getElementById('repo-description-input');
        const privateInput = document.getElementById('repo-private-input');
        const initReadmeInput = document.getElementById('repo-init-readme');
        
        if (nameInput) nameInput.value = '';
        if (descInput) descInput.value = '';
        if (privateInput) privateInput.checked = false;
        if (initReadmeInput) initReadmeInput.checked = true;
        
        // Focus on name input
        if (nameInput) nameInput.focus();
    }
}

function hideCreateRepoModal() {
    const modal = document.getElementById('create-repo-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Create GitHub Repository
async function createGitHubRepo() {
    const nameInput = document.getElementById('repo-name-input');
    const descriptionInput = document.getElementById('repo-description-input');
    const privateInput = document.getElementById('repo-private-input');
    const initReadmeInput = document.getElementById('repo-init-readme');
    const submitBtn = document.getElementById('create-repo-submit-btn');
    
    const repoName = nameInput?.value.trim();
    const description = descriptionInput?.value.trim();
    const isPrivate = privateInput?.checked;
    const autoInit = initReadmeInput?.checked;
    
    if (!repoName) {
        if (typeof showToast === 'function') {
            showToast('Please enter a repository name', 'error');
        }
        if (nameInput) nameInput.focus();
        return;
    }
    
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';
    }
    
    updateStatus('Creating repository...', 'loading');
    
    try {
        const response = await fetch(`${window.API_BASE}/api/github/create-repo`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({
                name: repoName,
                description: description,
                private: isPrivate,
                auto_init: autoInit
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            hideCreateRepoModal();
            updateStatus('✅ Repository created successfully!', 'success');
            if (typeof showToast === 'function') {
                showToast(`✅ Repository "${repoName}" created! View: ${data.repo_url}`, 'success');
            }
            
            // Optionally open the repository URL
            if (data.repo_url && confirm(`Repository created successfully!\n\nWould you like to open it in a new tab?`)) {
                window.open(data.repo_url, '_blank');
            }
        } else if (data.requires_connection) {
            hideCreateRepoModal();
            showGitHubConnectionModal();
            if (typeof showToast === 'function') {
                showToast('Please connect GitHub account first', 'warning');
            }
        } else {
            updateStatus('Failed to create repository', 'error');
            if (typeof showToast === 'function') {
                showToast(data.error || 'Failed to create repository', 'error');
            }
        }
    } catch (error) {
        updateStatus('Error creating repository', 'error');
        if (typeof showToast === 'function') {
            showToast('Error creating repository: ' + error.message, 'error');
        }
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = '➕ Create Repository';
        }
    }
}

async function gitStatus() {
    if (!editor) {
        if (typeof showToast === 'function') {
            showToast('No code in editor', 'warning');
        }
        return;
    }
    
    const code = editor.getValue();
    const filename = getCurrentFileName() || 'untitled.py';
    
    try {
        const response = await fetch(`${window.API_BASE}/api/git/status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({
                code: code,
                filename: filename
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            if (typeof showToast === 'function') {
                showToast(`Git Status: ${data.message}`, 'info');
            }
        } else if (data.requires_connection) {
            showGitHubConnectionModal();
            if (typeof showToast === 'function') {
                showToast('Please connect GitHub account first', 'warning');
            }
        } else {
            if (typeof showToast === 'function') {
                showToast(data.error || 'Failed to get status', 'error');
            }
        }
    } catch (error) {
        if (typeof showToast === 'function') {
            showToast('Error getting Git status: ' + error.message, 'error');
        }
    }
}

async function gitCommit() {
    if (!editor) {
        if (typeof showToast === 'function') {
            showToast('No code in editor', 'warning');
        }
        return;
    }
    
    const code = editor.getValue();
    const filename = getCurrentFileName() || 'untitled.py';
    
    // Prompt for commit message
    const message = prompt('Enter commit message:', 'Update code');
    if (!message) {
        return;
    }
    
    // Prompt for repository name
    const repoName = prompt('Repository name (leave empty for "codemind-project"):', 'codemind-project') || 'codemind-project';
    
    updateStatus('Committing to GitHub...', 'loading');
    
    try {
        const response = await fetch(`${window.API_BASE}/api/git/commit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({
                code: code,
                filename: filename,
                message: message,
                repo: repoName,
                branch: 'main'
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            updateStatus('✅ Committed successfully!', 'success');
            if (typeof showToast === 'function') {
                showToast(`✅ Committed to GitHub! View: ${data.repo_url}`, 'success');
            }
        } else if (data.requires_connection) {
            showGitHubConnectionModal();
            if (typeof showToast === 'function') {
                showToast('Please connect GitHub account first', 'warning');
            }
        } else {
            updateStatus('Failed to commit', 'error');
            if (typeof showToast === 'function') {
                showToast(data.error || 'Failed to commit', 'error');
            }
        }
    } catch (error) {
        updateStatus('Error committing', 'error');
        if (typeof showToast === 'function') {
            showToast('Error committing: ' + error.message, 'error');
        }
    }
}

async function gitPush() {
    try {
        const response = await fetch(`${window.API_BASE}/api/git/push`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            if (typeof showToast === 'function') {
                showToast(data.message || 'Pushed successfully', 'success');
            }
        } else if (data.requires_connection) {
            showGitHubConnectionModal();
            if (typeof showToast === 'function') {
                showToast('Please connect GitHub account first', 'warning');
            }
        } else {
            if (typeof showToast === 'function') {
                showToast(data.error || 'Failed to push', 'error');
            }
        }
    } catch (error) {
        if (typeof showToast === 'function') {
            showToast('Error pushing: ' + error.message, 'error');
        }
    }
}

async function gitPull() {
    if (!editor) {
        if (typeof showToast === 'function') {
            showToast('No editor available', 'warning');
        }
        return;
    }
    
    const filename = getCurrentFileName() || 'untitled.py';
    const repoName = prompt('Repository name (leave empty for "codemind-project"):', 'codemind-project') || 'codemind-project';
    
    updateStatus('Pulling from GitHub...', 'loading');
    
    try {
        const response = await fetch(`${window.API_BASE}/api/git/pull`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({
                filename: filename,
                repo: repoName,
                branch: 'main'
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Update editor with pulled code
            editor.setValue(data.code);
            updateStatus('✅ Pulled successfully!', 'success');
            if (typeof showToast === 'function') {
                showToast(data.message || 'Pulled from GitHub', 'success');
            }
        } else if (data.requires_connection) {
            showGitHubConnectionModal();
            if (typeof showToast === 'function') {
                showToast('Please connect GitHub account first', 'warning');
            }
        } else {
            updateStatus('Failed to pull', 'error');
            if (typeof showToast === 'function') {
                showToast(data.error || 'Failed to pull', 'error');
            }
        }
    } catch (error) {
        updateStatus('Error pulling', 'error');
        if (typeof showToast === 'function') {
            showToast('Error pulling: ' + error.message, 'error');
        }
    }
}

function getCurrentFileName() {
    // Try to get filename from active file tree item
    const activeFile = document.querySelector('.file-tree-item.active');
    if (activeFile) {
        return activeFile.dataset.file || 'untitled.py';
    }
    return 'untitled.py';
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('github-connection-modal');
    if (modal && e.target === modal) {
        hideGitHubConnectionModal();
    }
});
