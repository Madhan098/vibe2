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
    function getStyleProfile() {
        const profile = localStorage.getItem('codemind_style_profile');
        return profile ? JSON.parse(profile) : null;
    }
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
    
    // Listen for code changes
    editor.onDidChangeModelContent(() => {
        clearTimeout(suggestionTimeout);
        
        // Wait 2 seconds after user stops typing
        suggestionTimeout = setTimeout(() => {
            getSuggestion();
        }, 2000);
    });
    
    // Selection context menu - show when text is selected
    editor.onDidChangeCursorSelection(() => {
        const selection = editor.getSelection();
        if (selection && !selection.isEmpty()) {
            // Small delay to allow selection to complete
            setTimeout(() => {
                if (editor.getSelection() && !editor.getSelection().isEmpty()) {
                    showSelectionContextMenu(editor.getSelection());
                }
            }, 100);
        } else {
            hideSelectionContextMenu();
        }
    });
    
    // Hide menu when clicking outside
    document.addEventListener('click', (e) => {
        if (selectionContextMenu && !selectionContextMenu.contains(e.target)) {
            hideSelectionContextMenu();
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
const templateButtons = document.querySelectorAll('.template-btn');
templateButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all buttons
        templateButtons.forEach(b => b.classList.remove('active'));
        // Add active class to clicked button
        btn.classList.add('active');
        selectedTemplate = btn.dataset.template;
        
        // Update input placeholder based on template
        const codeRequestInput = document.getElementById('code-request-input');
        const templates = {
            'web-app': 'Create a modern web application with...',
            'flask-app': 'Create a Flask web application with...',
            'static-site': 'Create a static website with...',
            'rest-api': 'Create a REST API with endpoints for...',
            'cli-tool': 'Create a command-line tool that...',
            'data-analysis': 'Create a data analysis script that...'
        };
        if (codeRequestInput && templates[selectedTemplate]) {
            codeRequestInput.placeholder = templates[selectedTemplate];
        }
    });
});

// Accept/Reject buttons
const acceptBtn = document.getElementById('accept-btn');
const rejectBtn = document.getElementById('reject-btn');

if (acceptBtn) {
    acceptBtn.addEventListener('click', async () => {
        const suggestionCode = document.getElementById('suggestion-code').textContent;
        const originalCode = originalCodeBeforeSuggestion || (editor ? editor.getValue() : '');
        
        if (editor && suggestionCode) {
            editor.setValue(suggestionCode);
            hideSuggestion();
            updateStatus('Code updated!', 'success');
            
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

if (rejectBtn) {
    rejectBtn.addEventListener('click', async () => {
        const originalCode = originalCodeBeforeSuggestion || (editor ? editor.getValue() : '');
        const suggestionCode = document.getElementById('suggestion-code').textContent;
        
        hideSuggestion();
        updateStatus('Suggestion rejected', 'info');
        
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
    const suggestionEl = document.getElementById('suggestion');
    const noSuggestionEl = document.getElementById('no-suggestion');
    const loadingEl = document.getElementById('loading-suggestion');
    
    if (suggestionEl) {
        // Clear any previous teaching moments
        const existingTeaching = suggestionEl.querySelector('.teaching-moment');
        if (existingTeaching) {
            existingTeaching.remove();
        }
        
        // Clear any previous context indicators
        const existingContext = suggestionEl.querySelector('.context-indicator');
        if (existingContext) {
            existingContext.remove();
        }
        
        document.getElementById('suggestion-explanation').textContent = suggestion.explanation || 'Improved version';
        document.getElementById('suggestion-code').textContent = suggestion.improved_code || '';
        
        const explanationEl = document.getElementById('suggestion-explanation');
        
        // Show context if available
        if (suggestion.context) {
            const contextHTML = `<div class="context-indicator" style="margin-bottom: 8px; font-size: 0.85rem; color: var(--text-secondary);">🎯 Context: <strong>${suggestion.context}</strong></div>`;
            if (explanationEl) {
                explanationEl.insertAdjacentHTML('beforebegin', contextHTML);
            }
        }
        
        // Display teaching moment if available
        if (suggestion.teaching) {
            const teachingHTML = `
                <div class="teaching-moment" style="margin-top: 12px; padding: 12px; background: var(--bg-color); border-radius: 6px; border-left: 3px solid var(--primary-color);">
                    <h5 style="margin-bottom: 8px; color: var(--primary-color);">📚 Why This Is Better:</h5>
                    <p style="margin-bottom: 8px; font-size: 0.9rem;">${suggestion.teaching.why || suggestion.teaching.what || ''}</p>
                    <details style="margin-top: 8px;">
                        <summary style="cursor: pointer; color: var(--text-secondary); font-size: 0.85rem;">Learn More</summary>
                        <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border-color);">
                            <p style="font-size: 0.85rem; margin-bottom: 4px;"><strong>When to use:</strong> ${suggestion.teaching.when_to_use || 'In similar situations'}</p>
                            <p style="font-size: 0.85rem;"><strong>Tips:</strong> ${suggestion.teaching.tips || 'Keep practicing!'}</p>
                        </div>
                    </details>
                </div>
            `;
            
            // Insert teaching moment after explanation
            if (explanationEl) {
                explanationEl.insertAdjacentHTML('afterend', teachingHTML);
            }
        }
        
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
    
    if (!request && !selectedTemplate) {
        updateStatus('Please enter a request or select a template', 'warning');
        return;
    }
    
    const styleProfile = getStyleProfile();
    
    if (!styleProfile) {
        updateStatus('No style profile found. Please upload code first.', 'warning');
        return;
    }
    
    // Build the full request
    let fullRequest = request;
    if (selectedTemplate) {
        const templateRequests = {
            'web-app': 'Create a complete modern web application',
            'flask-app': 'Create a complete Flask web application',
            'static-site': 'Create a complete static website',
            'rest-api': 'Create a complete REST API',
            'cli-tool': 'Create a complete command-line tool',
            'data-analysis': 'Create a complete data analysis script'
        };
        fullRequest = `${templateRequests[selectedTemplate]}${request ? ': ' + request : ''}`;
    }
    
    if (techStack) {
        fullRequest += ` using ${techStack}`;
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
                tech_stack: techStack
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Check if it's multi-file generation
            if (data.files && Array.isArray(data.files) && data.files.length > 1) {
                // For multi-file, insert the first file into editor and show others in panel
                if (data.files.length > 0 && editor) {
                    const firstFile = data.files[0];
                    const code = firstFile.code || firstFile.content || '';
                    const filename = firstFile.filename || firstFile.name || 'generated';
                    
                    // Detect language from filename or use selected language
                    const languageSelector = document.getElementById('language-selector');
                    const currentLang = languageSelector ? languageSelector.value : 'python';
                    const fileLang = detectLanguageFromCode(code) || currentLang || 'python';
                    
                    // Insert code directly into editor
                    editor.setValue(code);
                    monaco.editor.setModelLanguage(editor.getModel(), fileLang);
                    
                    // Update language selector to match
                    const languageSelector = document.getElementById('language-selector');
                    if (languageSelector) {
                        languageSelector.value = fileLang;
                    }
                    
                    updateStatus(`Code generated! ${data.files.length} files total. First file inserted into editor.`, 'success');
                }
                // Show remaining files in the panel
                displayMultiFileCode(data.files, data.explanation || 'Code generated');
            } else if (data.code) {
                // Single file - insert directly into editor
                if (editor) {
                    const code = data.code;
                    const languageSelector = document.getElementById('language-selector');
                    const currentLang = languageSelector ? languageSelector.value : 'python';
                    const detectedLang = detectLanguageFromCode(code) || currentLang || 'python';
                    
                    // Insert code directly into editor
                    editor.setValue(code);
                    monaco.editor.setModelLanguage(editor.getModel(), detectedLang);
                    
                    // Update language selector to match
                    const languageSelector = document.getElementById('language-selector');
                    if (languageSelector) {
                        languageSelector.value = detectedLang;
                    }
                    
                    updateStatus(`Code generated and inserted into editor! ${data.explanation || ''}`, 'success');
                } else {
                    // Fallback to old display method if editor not available
                    displayGeneratedCode(data.code, data.explanation || 'Code generated');
                    updateStatus('Code generated!', 'success');
                }
            } else {
                hideLoadingSuggestion();
                updateStatus('No code generated', 'error');
                return;
            }
            codeRequestInput.value = ''; // Clear input
            if (techStackInput) techStackInput.value = ''; // Clear tech stack
            // Clear template selection
            templateButtons.forEach(b => b.classList.remove('active'));
            selectedTemplate = null;
        } else {
            hideLoadingSuggestion();
            updateStatus(data.error || 'Unable to generate code', 'error');
        }
    } catch (error) {
        hideLoadingSuggestion();
        updateStatus('Network error', 'error');
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
    // Remove existing menu
    if (selectionContextMenu) {
        selectionContextMenu.remove();
    }
    
    // Get selected text
    const selectedText = editor.getModel().getValueInRange(selection);
    if (!selectedText || selectedText.trim().length === 0) {
        return;
    }
    
    // Create context menu
    selectionContextMenu = document.createElement('div');
    selectionContextMenu.className = 'selection-context-menu';
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
    
    // Position menu near selection
    const position = editor.getScrolledVisiblePosition(selection.getStartPosition());
    const coords = editor.getScrolledVisiblePosition(selection.getEndPosition());
    const editorContainer = document.getElementById('monaco-editor');
    const rect = editorContainer.getBoundingClientRect();
    
    selectionContextMenu.style.top = `${rect.top + (coords.top || 0) + 20}px`;
    selectionContextMenu.style.left = `${rect.left + (coords.left || 0)}px`;
    
    // Event listeners
    const editWithAI = selectionContextMenu.querySelector('#edit-with-ai');
    const changeLanguage = selectionContextMenu.querySelector('#change-language');
    const languageSubmenu = selectionContextMenu.querySelector('#language-submenu');
    const submenuItems = selectionContextMenu.querySelectorAll('.submenu-item');
    
    editWithAI.addEventListener('click', () => {
        editSelectedCodeWithAI(selection, selectedText);
        hideSelectionContextMenu();
    });
    
    changeLanguage.addEventListener('click', (e) => {
        e.stopPropagation();
        const isVisible = languageSubmenu.style.display !== 'none';
        languageSubmenu.style.display = isVisible ? 'none' : 'block';
    });
    
    submenuItems.forEach(item => {
        item.addEventListener('click', () => {
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
    if (!editor) return;
    
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
    
    // Run Menu
    document.getElementById('run-code')?.addEventListener('click', () => {
        const code = editor.getValue();
        if (!code.trim()) {
            updateStatus('No code to run', 'warning');
            return;
        }
        updateStatus('Running code...', 'loading');
        // Terminal simulation
        const terminalPanel = document.getElementById('terminal-panel');
        const terminalContent = document.getElementById('terminal-content');
        if (terminalPanel && terminalContent) {
            terminalPanel.style.display = 'flex';
            isTerminalVisible = true;
            terminalContent.textContent = `$ Running code...\n${code}\n$ Code execution completed.\n`;
            updateStatus('Code executed (simulated)', 'success');
        }
    });
    
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
