/**
 * Upload Page JavaScript
 */

// Ensure utility functions are available (from app.js)
if (typeof showError === 'undefined') {
    function showError(message) {
        const errorEl = document.getElementById('error-message');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
        }
    }
}

if (typeof showSuccess === 'undefined') {
    function showSuccess(message) {
        // Create or use success message element
        let successEl = document.getElementById('success-message');
        if (!successEl) {
            successEl = document.createElement('div');
            successEl.id = 'success-message';
            successEl.className = 'success-message';
            successEl.style.cssText = 'display: none; padding: 12px; background: #10b981; color: white; border-radius: 6px; margin-bottom: 12px;';
            const container = document.querySelector('.container') || document.body;
            container.insertBefore(successEl, container.firstChild);
        }
        successEl.textContent = message;
        successEl.style.display = 'block';
        setTimeout(() => {
            successEl.style.display = 'none';
        }, 3000);
    }
}

if (typeof getStyleProfile === 'undefined') {
    // Use the async version from app.js if available, otherwise fallback
    async function getStyleProfile() {
        // Try to use the global function from app.js
        if (typeof window.getStyleProfile === 'function') {
            return await window.getStyleProfile();
        }
        // Fallback to localStorage
        const profile = localStorage.getItem('codemind_style_profile');
        return profile ? JSON.parse(profile) : null;
    }
    window.getStyleProfile = getStyleProfile;
}

if (typeof saveStyleProfile === 'undefined') {
    // Use the version from app.js if available, otherwise fallback
    function saveStyleProfile(profile) {
        // Try to use the global function from app.js
        if (typeof window.saveStyleProfile === 'function') {
            window.saveStyleProfile(profile);
            return;
        }
        // Fallback to localStorage
        localStorage.setItem('codemind_style_profile', JSON.stringify(profile));
    }
    window.saveStyleProfile = saveStyleProfile;
}

if (typeof hideError === 'undefined') {
    function hideError() {
        const errorEl = document.getElementById('error-message');
        if (errorEl) {
            errorEl.style.display = 'none';
        }
    }
}

if (typeof hideLoading === 'undefined') {
    function hideLoading() {
        const loadingEl = document.getElementById('loading');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
    }
}

let selectedFiles = [];

// File input and button
const fileInput = document.getElementById('file-input');
const chooseFilesBtn = document.getElementById('choose-files-btn');
const uploadBtn = document.getElementById('upload-btn');
const uploadArea = document.getElementById('upload-area');
const fileList = document.getElementById('file-list');
const fileItems = document.getElementById('file-items');

// GitHub elements
const githubUsernameInput = document.getElementById('github-username');
const analyzeGithubBtn = document.getElementById('analyze-github-btn');

// Choose Files button
if (chooseFilesBtn) {
    chooseFilesBtn.addEventListener('click', () => {
        fileInput.click();
    });
}

// Upload area click
if (uploadArea) {
    uploadArea.addEventListener('click', (e) => {
        if (e.target !== chooseFilesBtn) {
            fileInput.click();
        }
    });
}

// File input change
if (fileInput) {
    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFiles(e.target.files);
        }
    });
}

function handleFiles(files) {
    // Accept all common code file extensions
    const codeExtensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
                           '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
                           '.m', '.sh', '.bash', '.html', '.css', '.scss', '.vue', '.svelte',
                           '.dart', '.lua', '.pl', '.pm', '.sql'];
    
    selectedFiles = Array.from(files).filter(f => {
        const ext = '.' + f.name.split('.').pop().toLowerCase();
        return codeExtensions.includes(ext);
    });
    displayFiles();
}

function displayFiles() {
    if (selectedFiles.length === 0) {
        fileList.style.display = 'none';
        uploadBtn.style.display = 'none';
        return;
    }
    
    fileList.style.display = 'block';
    uploadBtn.style.display = 'block';
    
    fileItems.innerHTML = selectedFiles.map((file, index) => `
        <div class="file-item">
            <span>📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)</span>
            <button onclick="removeFile(${index})" style="background: var(--error-color); color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer;">Remove</button>
        </div>
    `).join('');
}

window.removeFile = function(index) {
    selectedFiles.splice(index, 1);
    displayFiles();
};

// Upload button
if (uploadBtn) {
    uploadBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) {
            showError('Please select at least one code file');
            return;
        }
        
        hideError();
        showLoading('Analyzing your code...', 'This may take 10-20 seconds');
        
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        
        let sessionId = null;
        let progressInterval = null;
        
        try {
            // Use window.API_BASE if available, otherwise define it
            if (typeof window.API_BASE === 'undefined') {
                window.API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
                    ? 'http://localhost:8000'
                    : window.location.origin;
            }
            
            // Start progress polling
            progressInterval = setInterval(async () => {
                try {
                    if (sessionId) {
                        const progressResponse = await fetch(`${window.API_BASE}/api/file-upload-progress?session_id=${encodeURIComponent(sessionId)}`);
                        if (progressResponse.ok) {
                            const progressData = await progressResponse.json();
                            const percent = progressData.percent || 0;
                            const status = progressData.status || 'Processing...';
                            
                            // Update progress bar
                            const progressFill = document.getElementById('progress-fill');
                            if (progressFill) {
                                progressFill.style.width = `${percent}%`;
                                progressFill.style.transition = 'width 0.3s ease';
                            }
                            
                            // Update text
                            const loadingTextEl = document.getElementById('loading-text');
                            const loadingSubtitleEl = document.getElementById('loading-subtitle');
                            if (loadingTextEl) {
                                loadingTextEl.textContent = status;
                            }
                            if (loadingSubtitleEl) {
                                loadingSubtitleEl.textContent = `${percent}% complete`;
                            }
                        }
                    }
                } catch (error) {
                    // Ignore progress polling errors
                    console.log('Progress polling error:', error);
                }
            }, 500); // Poll every 500ms for smooth updates
            
            const response = await fetch(`${window.API_BASE}/api/analyze-files`, {
                method: 'POST',
                body: formData
            });
            
            // Check if response is JSON
            const contentType = response.headers.get('content-type') || '';
            if (!contentType.includes('application/json')) {
                const text = await response.text();
                console.error('Non-JSON response:', text.substring(0, 200));
                if (progressInterval) clearInterval(progressInterval);
                hideLoading();
                showError('Server error. Please try again.');
                return;
            }
            
            const data = await response.json();
            
            // Get session ID for progress tracking
            if (data.session_id) {
                sessionId = data.session_id;
            }
            
            if (response.ok && data.success) {
                // Wait a moment for final progress update
                await new Promise(resolve => setTimeout(resolve, 500));
                if (progressInterval) clearInterval(progressInterval);
                
                hideLoading();
                saveStyleProfile(data.report);
                displayReport(data.report);
                showToast('Code analyzed successfully!', 'success');
            } else {
                if (progressInterval) clearInterval(progressInterval);
                hideLoading();
                showError(data.error || 'Upload failed');
                showToast(data.error || 'Upload failed', 'error');
            }
        } catch (error) {
            if (progressInterval) clearInterval(progressInterval);
            hideLoading();
            showError('Network error: ' + error.message);
            showToast('Network error: ' + error.message, 'error');
        }
    });
}

// GitHub analysis
if (analyzeGithubBtn) {
    analyzeGithubBtn.addEventListener('click', async () => {
        const username = githubUsernameInput.value.trim();
        
        if (!username) {
            showError('Please enter a GitHub username');
            return;
        }
        
        hideError();
        showLoading('Analyzing your GitHub profile health...', 'Checking repositories for good practices and areas of improvement');
        
        // Poll for progress updates
        const progressInterval = setInterval(async () => {
            try {
                if (typeof window.API_BASE === 'undefined') {
                    window.API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
                        ? 'http://localhost:8000'
                        : window.location.origin;
                }
                
                const progressResponse = await fetch(`${window.API_BASE}/api/github-progress/${encodeURIComponent(username)}`);
                if (progressResponse.ok) {
                    const progressData = await progressResponse.json();
                    const percent = progressData.percent || 0;
                    const status = progressData.status || 'Processing...';
                    
                    // Update progress bar
                    const progressFill = document.getElementById('progress-fill');
                    if (progressFill) {
                        progressFill.style.width = `${percent}%`;
                        progressFill.style.transition = 'width 0.3s ease';
                    }
                    
                    // Update text with percentage
                    const loadingTextEl = document.getElementById('loading-text');
                    const loadingSubtitleEl = document.getElementById('loading-subtitle');
                    
                    if (loadingTextEl) {
                        loadingTextEl.textContent = status;
                    }
                    
                    if (loadingSubtitleEl) {
                        loadingSubtitleEl.textContent = `Checking repositories for good practices and areas of improvement... ${percent}% completed`;
                    }
                }
            } catch (error) {
                // Ignore progress polling errors
                console.log('Progress polling error:', error);
            }
        }, 500); // Poll every 500ms for smooth updates
        
        try {
            // Use window.API_BASE if available, otherwise define it
            if (typeof window.API_BASE === 'undefined') {
                window.API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
                    ? 'http://localhost:8000'
                    : window.location.origin;
            }
            
            const response = await fetch(`${window.API_BASE}/api/analyze-github`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username })
            });
            
            // Check if response is JSON
            const contentType = response.headers.get('content-type') || '';
            if (!contentType.includes('application/json')) {
                const text = await response.text();
                console.error('Non-JSON response:', text.substring(0, 200));
                hideLoading();
                showError('Server error. Please try again.');
                return;
            }
            
            const data = await response.json();
            
            // Set progress to 100% before clearing
            const loadingSubtitleEl = document.getElementById('loading-subtitle');
            if (loadingSubtitleEl) {
                loadingSubtitleEl.textContent = 'Checking repositories for good practices and areas of improvement... 100% completed';
            }
            const progressFill = document.getElementById('progress-fill');
            if (progressFill) {
                progressFill.style.width = '100%';
            }
            
            // Wait a moment to show 100%
            await new Promise(resolve => setTimeout(resolve, 500));
            
            clearInterval(progressInterval);
            
            if (response.ok && data.success) {
                hideLoading();
                saveStyleProfile(data.report);
                displayReport(data.report);
                
                // Show success toast
                const fileCount = data.report.files_analyzed || 0;
                const timeMsg = data.analysis_time ? ` in ${data.analysis_time}s` : '';
                showToast(`Analysis completed${timeMsg}! Found ${fileCount} files.`, 'success');
            } else {
                hideLoading();
                const errorMsg = data.error || 'Analysis failed';
                let fullErrorMsg = errorMsg;
                
                // Add suggestions if available
                if (data.suggestions && Array.isArray(data.suggestions)) {
                    fullErrorMsg += '\n\nSuggestions:\n' + data.suggestions.map((s, i) => `${i + 1}. ${s}`).join('\n');
                }
                
                // Add rate limit info if available
                if (data.details && data.details.rate_limit) {
                    const rl = data.details.rate_limit;
                    if (rl.remaining !== undefined && rl.limit !== undefined) {
                        fullErrorMsg += `\n\nRate Limit: ${rl.remaining}/${rl.limit} requests remaining`;
                    }
                }
                
                showError(fullErrorMsg);
                showToast(errorMsg, 'error');
                
                // Log full error for debugging
                console.error('GitHub analysis error:', data);
            }
        } catch (error) {
            clearInterval(progressInterval);
            hideLoading();
            showError('Network error: ' + error.message);
            showToast('Network error: ' + error.message, 'error');
        }
    });
}

// Toast Notification System
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        // Create toast container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
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
    
    document.getElementById('toast-container').appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.animation = 'slideInRight 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

// Enhanced Loading Functions
function showLoading(message = 'Loading...', subtitle = '') {
    const overlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    const loadingSubtitle = document.getElementById('loading-subtitle');
    
    if (overlay) {
        if (loadingText) loadingText.textContent = message;
        if (loadingSubtitle) loadingSubtitle.textContent = subtitle;
        overlay.classList.add('active');
    } else {
        // Fallback to old loading
        const loadingEl = document.getElementById('loading');
        if (loadingEl) {
            loadingEl.style.display = 'flex';
        }
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
    
    // Also hide old loading
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
}

// Display Visual DNA Report
function displayDNAReport(report) {
    // Hide upload section
    const uploadSection = document.querySelector('.upload-section');
    if (uploadSection) {
        uploadSection.style.display = 'none';
    }
    
    // Show DNA report
    const reportDiv = document.getElementById('dna-report');
    if (!reportDiv) return;
    
    reportDiv.style.display = 'block';
    reportDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Get values from report
    const namingStyle = report.naming_style || 'snake_case';
    const namingConfidence = report.naming_confidence || 0;
    const docPercentage = Math.round(report.documentation_percentage || 0);
    const typesPercentage = Math.round(report.type_hints_percentage || 0);
    const qualityScore = Math.round(report.code_quality_score || 0);
    
    // Animate progress bars
    setTimeout(() => {
        const namingProgress = document.getElementById('naming-progress');
        const docProgress = document.getElementById('doc-progress');
        const typesProgress = document.getElementById('types-progress');
        
        if (namingProgress) {
            namingProgress.style.width = namingConfidence + '%';
        }
        if (docProgress) {
            docProgress.style.width = docPercentage + '%';
        }
        if (typesProgress) {
            typesProgress.style.width = typesPercentage + '%';
        }
    }, 100);
    
    // Animate quality circle
    setTimeout(() => {
        const circle = document.getElementById('quality-circle');
        if (circle) {
            const circumference = 2 * Math.PI * 45; // r = 45
            const offset = circumference - (circumference * qualityScore / 100);
            circle.style.strokeDashoffset = offset;
        }
    }, 300);
    
    // Animate score number
    const scoreEl = document.getElementById('quality-score');
    if (scoreEl) {
        let current = 0;
        const increment = qualityScore / 50;
        const timer = setInterval(() => {
            current += increment;
            if (current >= qualityScore) {
                current = qualityScore;
                clearInterval(timer);
            }
            scoreEl.textContent = Math.round(current);
        }, 30);
    }
    
    // Update text values
    const namingValue = document.getElementById('naming-value');
    if (namingValue) {
        namingValue.textContent = `${namingStyle} (${namingConfidence}%)`;
    }
    
    const docValue = document.getElementById('doc-value');
    if (docValue) {
        docValue.textContent = `${docPercentage}%`;
    }
    
    const typesValue = document.getElementById('types-value');
    if (typesValue) {
        typesValue.textContent = `${typesPercentage}%`;
    }
    
    // Update insights
    const insights = generateInsights(report);
    const insight1 = document.getElementById('insight-1-text');
    const insight2 = document.getElementById('insight-2-text');
    const insight3 = document.getElementById('insight-3-text');
    
    if (insight1 && insights[0]) insight1.textContent = insights[0];
    if (insight2 && insights[1]) insight2.textContent = insights[1];
    if (insight3 && insights[2]) insight3.textContent = insights[2];
    
    // Save to localStorage
    localStorage.setItem('styleProfile', JSON.stringify(report));
    if (typeof saveStyleProfile === 'function') {
        saveStyleProfile(report);
    }
}

function generateInsights(report) {
    const insights = [];
    
    // Check if this is a minimal/no-code report
    const hasCode = (report.total_functions && report.total_functions > 0) || 
                    (report.total_lines && report.total_lines > 10);
    
    if (!hasCode) {
        insights.push('📝 Upload code files to get detailed analysis');
        insights.push('💡 Try uploading Python, JavaScript, or other code files');
        insights.push('🚀 Start coding to build your style profile');
        return insights;
    }
    
    // Positive insights
    if (report.naming_confidence && report.naming_confidence > 80) {
        insights.push(`✅ Consistent ${report.naming_style || 'naming'} style`);
    } else if (report.naming_confidence && report.naming_confidence > 0) {
        insights.push(`📝 Using ${report.naming_style || 'mixed'} naming style`);
    }
    
    if (report.documentation_percentage && report.documentation_percentage > 70) {
        insights.push('📚 Strong documentation habits');
    } else if (report.documentation_percentage && report.documentation_percentage > 0) {
        insights.push('💡 Some documentation found');
    } else if (report.total_functions && report.total_functions > 0) {
        insights.push('📝 Opportunity: Add docstrings to functions');
    }
    
    // Type hints insights
    if (report.type_hints_percentage && report.type_hints_percentage > 70) {
        insights.push('🎯 Excellent type hint usage');
    } else if (report.type_hints_percentage && report.type_hints_percentage > 0) {
        insights.push('💡 Some type hints found');
    } else if (report.total_functions && report.total_functions > 0) {
        insights.push('🎯 Opportunity: Add type hints for better code clarity');
    }
    
    // Quality score insights
    if (report.code_quality_score && report.code_quality_score > 80) {
        insights.push('⭐ High code quality score');
    } else if (report.code_quality_score && report.code_quality_score > 60) {
        insights.push('👍 Good code structure');
    } else if (report.code_quality_score && report.code_quality_score > 40) {
        insights.push('📈 Room for improvement');
    } else if (report.code_quality_score && report.code_quality_score > 0) {
        insights.push('🚀 Start adding functions and documentation');
    }
    
    // Fill remaining slots with helpful tips
    while (insights.length < 3) {
        if (report.total_functions === 0 && report.total_lines > 0) {
            insights.push('💡 Consider organizing code into functions');
        } else if (report.total_functions > 0 && report.documentation_percentage === 0) {
            insights.push('📝 Add docstrings to improve code quality');
        } else {
            insights.push('✨ Keep coding to build your unique style');
        }
    }
    
    return insights.slice(0, 3);
}

function goToEditor() {
    window.location.href = '/editor';
}

function showDetailedReport() {
    const dnaReport = document.getElementById('dna-report');
    const analysisReport = document.getElementById('analysis-report');
    
    if (dnaReport) dnaReport.style.display = 'none';
    if (analysisReport) {
        analysisReport.style.display = 'block';
        analysisReport.scrollIntoView({ behavior: 'smooth' });
    }
}

function displayReport(report) {
    // First show DNA report
    displayDNAReport(report);
    
    // Display health report if available
    if (report.health_report) {
        displayHealthReport(report.health_report, report.language_percentages, report.ai_suggestions);
    }
    
    // Also update the detailed report
    const reportEl = document.getElementById('analysis-report');
    if (!reportEl) return;
    
    // Update languages detected
    const languages = report.languages_detected || [];
    const primaryLang = report.primary_language || 'Unknown';
    const langEl = document.getElementById('languages-detected');
    const primaryLangEl = document.getElementById('primary-language');
    
    // Use language_percentages if available
    if (report.language_percentages) {
        const langPercs = report.language_percentages;
        const langList = Object.keys(langPercs).map(lang => `${lang} (${langPercs[lang]}%)`).join(', ');
        if (langEl) {
            langEl.textContent = langList || 'Unknown';
        }
        if (primaryLangEl) {
            const primary = Object.keys(langPercs).reduce((a, b) => langPercs[a] > langPercs[b] ? a : b, '');
            primaryLangEl.textContent = `Primary: ${primary} (${langPercs[primary]}%)`;
        }
    } else {
        if (langEl) {
            langEl.textContent = languages.length > 0 ? languages.join(', ') : primaryLang;
        }
        if (primaryLangEl) {
            primaryLangEl.textContent = `Primary: ${primaryLang}`;
        }
    }
    
    // Update report values
    const namingStyleEl = document.getElementById('naming-style');
    const namingDetailEl = document.getElementById('naming-detail');
    
    if (namingStyleEl) {
        namingStyleEl.textContent = report.naming_style || 'N/A';
    }
    if (namingDetailEl) {
        namingDetailEl.textContent = report.naming_confidence ? `${report.naming_confidence}% confidence` : 'Detected';
    }
    
    const docEl = document.getElementById('documentation');
    if (docEl) {
        docEl.textContent = `${Math.round(report.documentation_percentage || 0)}%`;
    }
    
    const errorEl = document.getElementById('error-handling');
    const errorDetailEl = document.getElementById('error-detail');
    
    if (errorEl) {
        errorEl.textContent = report.error_handling_style || 'N/A';
    }
    if (errorDetailEl) {
        errorDetailEl.textContent = 'style';
    }
    
    const qualityEl = document.getElementById('code-quality');
    if (qualityEl) {
        qualityEl.textContent = report.code_quality_score || 0;
    }
}

function displayHealthReport(healthReport, languagePercentages, aiSuggestions) {
    // Create or get health report section
    let healthSection = document.getElementById('health-report');
    if (!healthSection) {
        healthSection = document.createElement('div');
        healthSection.id = 'health-report';
        healthSection.className = 'health-report';
        healthSection.style.display = 'none';
        
        // Insert after DNA report
        const dnaReport = document.getElementById('dna-report');
        if (dnaReport && dnaReport.parentNode) {
            dnaReport.parentNode.insertBefore(healthSection, dnaReport.nextSibling);
        } else {
            document.body.appendChild(healthSection);
        }
    }
    
    const goodPct = healthReport.good_percentage || 0;
    const badPct = healthReport.bad_percentage || 0;
    const healthScore = healthReport.health_score || 0;
    
    // Group patterns by category
    const goodPatterns = healthReport.good_patterns || [];
    const badPatterns = healthReport.bad_patterns || [];
    
    // Calculate category percentages
    const goodByCategory = {};
    const badByCategory = {};
    let totalGoodWeight = 0;
    let totalBadWeight = 0;
    
    goodPatterns.forEach(pattern => {
        const cat = pattern.category || 'other';
        if (!goodByCategory[cat]) {
            goodByCategory[cat] = { count: 0, weight: 0, patterns: [] };
        }
        goodByCategory[cat].count++;
        goodByCategory[cat].weight += pattern.weight || 0;
        goodByCategory[cat].patterns.push(pattern);
        totalGoodWeight += pattern.weight || 0;
    });
    
    badPatterns.forEach(pattern => {
        const cat = pattern.category || 'other';
        if (!badByCategory[cat]) {
            badByCategory[cat] = { count: 0, weight: 0, patterns: [] };
        }
        badByCategory[cat].count++;
        badByCategory[cat].weight += pattern.weight || 0;
        badByCategory[cat].patterns.push(pattern);
        totalBadWeight += pattern.weight || 0;
    });
    
    // Calculate percentages for each category
    const goodCategoryPercs = {};
    const badCategoryPercs = {};
    
    Object.keys(goodByCategory).forEach(cat => {
        goodCategoryPercs[cat] = totalGoodWeight > 0 
            ? ((goodByCategory[cat].weight / totalGoodWeight) * 100).toFixed(1)
            : 0;
    });
    
    Object.keys(badByCategory).forEach(cat => {
        badCategoryPercs[cat] = totalBadWeight > 0
            ? ((badByCategory[cat].weight / totalBadWeight) * 100).toFixed(1)
            : 0;
    });
    
    // Format category names
    const formatCategoryName = (cat) => {
        return cat.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    };
    
    healthSection.innerHTML = `
        <div class="health-report-container">
            <h2 class="health-title">📊 GitHub Profile Health Report</h2>
            
            <div class="health-score-section">
                <div class="health-score-circle">
                    <div class="health-score-value">${healthScore}</div>
                    <div class="health-score-label">/100</div>
                </div>
                <div class="health-percentages">
                    <div class="health-percentage good">
                        <span class="percentage-label">✅ Good Patterns</span>
                        <span class="percentage-value">${goodPct.toFixed(1)}%</span>
                    </div>
                    <div class="health-percentage bad">
                        <span class="percentage-label">❌ Bad Patterns</span>
                        <span class="percentage-value">${badPct.toFixed(1)}%</span>
                    </div>
                </div>
            </div>
            
            <!-- Detailed Good Patterns Breakdown -->
            ${Object.keys(goodByCategory).length > 0 ? `
            <div class="patterns-breakdown-section">
                <h3>✅ Good Patterns Breakdown</h3>
                <div class="patterns-grid">
                    ${Object.entries(goodByCategory).map(([cat, data]) => `
                        <div class="pattern-category-card good">
                            <div class="category-header">
                                <span class="category-name">${formatCategoryName(cat)}</span>
                                <span class="category-percentage">${goodCategoryPercs[cat]}%</span>
                            </div>
                            <div class="category-stats">
                                <span class="stat-item">${data.count} pattern${data.count !== 1 ? 's' : ''}</span>
                                <span class="stat-item">Weight: ${data.weight}</span>
                            </div>
                            <div class="category-patterns">
                                ${data.patterns.slice(0, 5).map(p => `
                                    <div class="pattern-item">
                                        <span class="pattern-icon">✓</span>
                                        <span class="pattern-desc">${p.description || p.pattern}</span>
                                    </div>
                                `).join('')}
                                ${data.patterns.length > 5 ? `<div class="pattern-more">+${data.patterns.length - 5} more</div>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            <!-- Detailed Bad Patterns Breakdown -->
            ${Object.keys(badByCategory).length > 0 ? `
            <div class="patterns-breakdown-section">
                <h3>❌ Bad Patterns Breakdown</h3>
                <div class="patterns-grid">
                    ${Object.entries(badByCategory).map(([cat, data]) => `
                        <div class="pattern-category-card bad">
                            <div class="category-header">
                                <span class="category-name">${formatCategoryName(cat)}</span>
                                <span class="category-percentage">${badCategoryPercs[cat]}%</span>
                            </div>
                            <div class="category-stats">
                                <span class="stat-item">${data.count} issue${data.count !== 1 ? 's' : ''}</span>
                                <span class="stat-item">Weight: ${data.weight}</span>
                            </div>
                            <div class="category-patterns">
                                ${data.patterns.slice(0, 5).map(p => `
                                    <div class="pattern-item">
                                        <span class="pattern-icon">⚠</span>
                                        <span class="pattern-desc">${p.description || p.pattern}</span>
                                        ${p.path ? `<span class="pattern-path">${p.path}</span>` : ''}
                                    </div>
                                `).join('')}
                                ${data.patterns.length > 5 ? `<div class="pattern-more">+${data.patterns.length - 5} more</div>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            ${languagePercentages ? `
            <div class="languages-section">
                <h3>Languages Used</h3>
                <div class="languages-list">
                    ${Object.entries(languagePercentages).map(([lang, pct]) => `
                        <div class="language-item">
                            <span class="language-name">${lang}</span>
                            <span class="language-percentage">${pct}%</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            ${aiSuggestions ? `
            <div class="ai-suggestions-section">
                <h3>🤖 AI-Powered Recommendations</h3>
                ${aiSuggestions.summary ? `<p class="suggestion-summary">${aiSuggestions.summary}</p>` : ''}
                
                ${aiSuggestions.suggestions && aiSuggestions.suggestions.length > 0 ? `
                <div class="suggestions-list">
                    <h4>Top Suggestions</h4>
                    <ul>
                        ${aiSuggestions.suggestions.slice(0, 5).map(s => `<li>${s}</li>`).join('')}
                    </ul>
                </div>
                ` : ''}
                
                ${aiSuggestions.roadmap && aiSuggestions.roadmap.length > 0 ? `
                <div class="roadmap-list">
                    <h4>Improvement Roadmap</h4>
                    <ol>
                        ${aiSuggestions.roadmap.slice(0, 5).map(s => `<li>${s}</li>`).join('')}
                    </ol>
                </div>
                ` : ''}
            </div>
            ` : ''}
            
            <div class="health-actions">
                <button class="btn btn-primary" onclick="downloadHealthPDF()">📥 Download PDF Report</button>
            </div>
        </div>
    `;
    
    healthSection.style.display = 'block';
    healthSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Store health data for PDF download
    window.currentHealthData = {
        health_data: {
            ...healthReport,
            language_percentages: languagePercentages,
            ai_suggestions: aiSuggestions
        }
    };
}

async function downloadHealthPDF() {
    if (!window.currentHealthData) {
        showToast('No health data available', 'error');
        return;
    }
    
    try {
        showLoading('Generating PDF...', 'Please wait');
        
        const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:8000'
            : window.location.origin;
        
        const response = await fetch(`${API_BASE}/api/export-github-health-pdf`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(window.currentHealthData)
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `github-health-report-${window.currentHealthData.health_data.username || 'user'}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            showToast('PDF downloaded successfully!', 'success');
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to generate PDF', 'error');
        }
    } catch (error) {
        showToast('Error generating PDF: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Export Style Guide
const exportStyleGuideBtn = document.getElementById('export-style-guide-btn');
if (exportStyleGuideBtn) {
    exportStyleGuideBtn.addEventListener('click', async () => {
        const styleProfile = getStyleProfile();
        
        if (!styleProfile) {
            showError('No style profile found. Please analyze code first.');
            return;
        }
        
        try {
            // Use window.API_BASE if available, otherwise define it
            if (typeof window.API_BASE === 'undefined') {
                window.API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
                    ? 'http://localhost:8000'
                    : window.location.origin;
            }
            
            const response = await fetch(`${window.API_BASE}/api/export-style-guide`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    style_profile: styleProfile
                })
            });
            
            // Check if response is a file download (markdown) or JSON
            const contentType = response.headers.get('content-type') || '';
            
            if (response.ok && contentType.includes('text/markdown')) {
                // Server returns file directly - download it
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                
                // Get filename from Content-Disposition header or use default
                const contentDisposition = response.headers.get('content-disposition');
                let filename = 'codemind-style-guide.md';
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
                    if (filenameMatch) {
                        filename = filenameMatch[1];
                    }
                }
                a.download = filename;
                
                document.body.appendChild(a);
                a.click();
                
                // Clean up
                setTimeout(() => {
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                }, 100);
                
                showToast('Style guide downloaded!', 'success');
            } else {
                // Try to parse as JSON for error message
                try {
                    const data = await response.json();
                    showError(data.error || 'Failed to export style guide');
                } catch {
                    showError('Failed to export style guide');
                }
            }
        } catch (error) {
            showError('Network error: ' + error.message);
        }
    });
}

