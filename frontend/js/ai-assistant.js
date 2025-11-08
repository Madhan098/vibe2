/**
 * AI Assistant Panel Functionality
 */

/**
 * Display AI suggestion in assistant panel
 */
function displaySuggestion(suggestionData) {
    const assistantContent = document.getElementById('assistant-content');
    const assistantPanel = document.getElementById('assistant-panel');
    
    if (!assistantContent || !assistantPanel) {
        console.error('Assistant panel elements not found');
        return;
    }
    
    // Show assistant panel
    assistantPanel.style.display = 'flex';
    
    if (!suggestionData.has_suggestion) {
        assistantContent.innerHTML = `
            <div class="suggestion-card">
                <div class="suggestion-header">
                    <span class="suggestion-title">No Suggestions</span>
                </div>
                <p style="color: var(--text-secondary);">
                    Your code looks good! No improvements needed at this time.
                </p>
            </div>
        `;
        return;
    }
    
    const { improved_code, explanation, confidence, teaching_tip, teaching_moment } = suggestionData;
    
    let html = `
        <div class="suggestion-card">
            <div class="suggestion-header">
                <span class="suggestion-title">AI Suggestion</span>
                <span class="confidence-badge">${Math.round(confidence * 100)}% confident</span>
            </div>
            
            ${explanation ? `
                <div class="explanation">
                    <strong>Why this is better:</strong>
                    <p>${explanation}</p>
                </div>
            ` : ''}
            
            ${improved_code ? `
                <div class="improved-code">${escapeHtml(improved_code)}</div>
            ` : ''}
            
            <div class="suggestion-actions">
                <button class="btn btn-primary" onclick="acceptSuggestion('${escapeHtml(improved_code || '')}')">
                    ✅ Accept
                </button>
                <button class="btn btn-secondary" onclick="rejectSuggestion()">
                    ❌ Reject
                </button>
                <button class="btn btn-secondary" onclick="askMoreInfo()">
                    💡 More Info
                </button>
            </div>
        </div>
    `;
    
    if (teaching_tip) {
        html += `
            <div class="teaching-tip">
                <h4>💡 Learning Tip</h4>
                <p>${teaching_tip}</p>
            </div>
        `;
    }
    
    if (teaching_moment) {
        html += `
            <div class="teaching-tip">
                <h4>👨‍🏫 Teaching Moment: ${teaching_moment.topic}</h4>
                <p><strong>Difficulty:</strong> ${teaching_moment.difficulty}</p>
                <p>${teaching_moment.why}</p>
            </div>
        `;
    }
    
    assistantContent.innerHTML = html;
}

/**
 * Display code analysis results
 */
function displayAnalysis(analysisData) {
    const assistantContent = document.getElementById('assistant-content');
    const assistantPanel = document.getElementById('assistant-panel');
    
    if (!assistantContent || !assistantPanel) {
        return;
    }
    
    assistantPanel.style.display = 'flex';
    
    const { patterns, quality_score, dominant_naming } = analysisData;
    
    let html = `
        <div class="suggestion-card">
            <div class="suggestion-header">
                <span class="suggestion-title">Code Analysis</span>
                <span class="confidence-badge">Score: ${quality_score}/100</span>
            </div>
            
            <div style="margin-top: 16px;">
                <p><strong>Naming Style:</strong> ${dominant_naming}</p>
                <p><strong>Functions:</strong> ${patterns.function_count}</p>
                <p><strong>Has Docstrings:</strong> ${patterns.has_docstrings ? '✅' : '❌'}</p>
                <p><strong>Has Type Hints:</strong> ${patterns.has_type_hints ? '✅' : '❌'}</p>
                <p><strong>Error Handling:</strong> ${patterns.error_handling}</p>
            </div>
            
            ${patterns.issues && patterns.issues.length > 0 ? `
                <div style="margin-top: 16px;">
                    <strong>Issues Found:</strong>
                    <ul style="margin-top: 8px; margin-left: 20px;">
                        ${patterns.issues.map(issue => `<li style="color: var(--text-secondary);">${issue}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
    
    assistantContent.innerHTML = html;
}

/**
 * Display errors
 */
function displayErrors(errorData) {
    const assistantContent = document.getElementById('assistant-content');
    const assistantPanel = document.getElementById('assistant-panel');
    
    if (!assistantContent || !assistantPanel) {
        return;
    }
    
    assistantPanel.style.display = 'flex';
    
    if (!errorData.has_errors || !errorData.errors || errorData.errors.length === 0) {
        assistantContent.innerHTML = `
            <div class="suggestion-card">
                <p style="color: var(--success-color);">✅ No errors detected!</p>
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="error-display">
            <h4>⚠️ Errors Found</h4>
            ${errorData.errors.map(error => `
                <div class="error-item">
                    <strong>${error.severity.toUpperCase()}:</strong> ${error.message}
                    ${error.line ? ` (Line ${error.line})` : ''}
                    ${error.fix ? `<br><small style="color: var(--text-muted);">Fix: ${error.fix}</small>` : ''}
                </div>
            `).join('')}
        </div>
    `;
    
    assistantContent.innerHTML = html;
}

/**
 * Accept suggestion
 */
async function acceptSuggestion(improvedCode) {
    const currentCode = window.getCurrentCode ? window.getCurrentCode() : '';
    
    // Insert improved code
    if (window.insertCodeAtCursor && improvedCode) {
        window.setCode(improvedCode);
    }
    
    // Submit feedback
    try {
        await submitFeedback(currentCode, improvedCode, 'accept');
        showNotification('Suggestion accepted! CodeMind is learning your preferences.');
    } catch (error) {
        console.error('Error submitting feedback:', error);
    }
}

/**
 * Reject suggestion
 */
async function rejectSuggestion() {
    const currentCode = window.getCurrentCode ? window.getCurrentCode() : '';
    const assistantContent = document.getElementById('assistant-content');
    
    // Get the suggested code from the display
    const improvedCodeEl = assistantContent.querySelector('.improved-code');
    const improvedCode = improvedCodeEl ? improvedCodeEl.textContent : '';
    
    // Submit feedback
    try {
        await submitFeedback(currentCode, improvedCode, 'reject');
        showNotification('Suggestion rejected. CodeMind will avoid similar suggestions.');
        
        // Hide suggestion
        const suggestionCard = assistantContent.querySelector('.suggestion-card');
        if (suggestionCard) {
            suggestionCard.style.opacity = '0.5';
        }
    } catch (error) {
        console.error('Error submitting feedback:', error);
    }
}

/**
 * Ask for more info
 */
async function askMoreInfo() {
    const currentCode = window.getCurrentCode ? window.getCurrentCode() : '';
    const assistantContent = document.getElementById('assistant-content');
    
    const improvedCodeEl = assistantContent.querySelector('.improved-code');
    const improvedCode = improvedCodeEl ? improvedCodeEl.textContent : '';
    
    try {
        await submitFeedback(currentCode, improvedCode, 'ask_more');
        showNotification('Thanks for the feedback!');
    } catch (error) {
        console.error('Error submitting feedback:', error);
    }
}

/**
 * Show notification
 */
function showNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--bg-dark);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 16px 20px;
        color: var(--text-primary);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Export functions
window.displaySuggestion = displaySuggestion;
window.displayAnalysis = displayAnalysis;
window.displayErrors = displayErrors;
window.acceptSuggestion = acceptSuggestion;
window.rejectSuggestion = rejectSuggestion;
window.askMoreInfo = askMoreInfo;

