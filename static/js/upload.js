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
        showLoading('Uploading and analyzing files...');
        
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        
        try {
            // Use window.API_BASE if available, otherwise define it
            if (typeof window.API_BASE === 'undefined') {
                window.API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
                    ? 'http://localhost:8000'
                    : window.location.origin;
            }
            
            const response = await fetch(`${window.API_BASE}/api/analyze-files`, {
                method: 'POST',
                body: formData
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
            
            if (response.ok && data.success) {
                hideLoading();
                saveStyleProfile(data.report);
                displayReport(data.report);
            } else {
                hideLoading();
                showError(data.error || 'Upload failed');
            }
        } catch (error) {
            hideLoading();
            showError('Network error: ' + error.message);
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
        showLoading(`Starting analysis... 0%`);
        
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
                    
                    // Update text
                    const loadingTextEl = document.getElementById('loading-text');
                    if (loadingTextEl) {
                        loadingTextEl.textContent = `${status} ${percent}%`;
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
            
            clearInterval(progressInterval);
            
            if (response.ok && data.success) {
                hideLoading();
                saveStyleProfile(data.report);
                displayReport(data.report);
                
                // Show success message with timing info
                if (data.analysis_time) {
                    const successMsg = document.createElement('div');
                    successMsg.className = 'success-message';
                    successMsg.style.cssText = 'background: var(--success-color); color: white; padding: 10px; border-radius: 8px; margin: 10px 0;';
                    successMsg.textContent = `Analysis completed in ${data.analysis_time}s! Found ${data.report.files_analyzed || 0} files.`;
                    document.getElementById('analysis-report')?.parentElement?.insertBefore(successMsg, document.getElementById('analysis-report'));
                    setTimeout(() => successMsg.remove(), 5000);
                }
            } else {
                hideLoading();
                showError(data.error || 'Analysis failed');
            }
        } catch (error) {
            clearInterval(progressInterval);
            hideLoading();
            showError('Network error: ' + error.message);
        }
    });
}

function displayReport(report) {
    const reportEl = document.getElementById('analysis-report');
    if (!reportEl) return;
    
    // Update languages detected
    const languages = report.languages_detected || [];
    const primaryLang = report.primary_language || 'Unknown';
    document.getElementById('languages-detected').textContent = languages.length > 0 ? languages.join(', ') : primaryLang;
    document.getElementById('primary-language').textContent = `Primary: ${primaryLang}`;
    
    // Update report values
    document.getElementById('naming-style').textContent = report.naming_style || 'N/A';
    document.getElementById('naming-detail').textContent = report.naming_confidence ? `${report.naming_confidence}% confidence` : 'Detected';
    
    document.getElementById('documentation').textContent = `${Math.round(report.documentation_percentage || 0)}%`;
    
    document.getElementById('error-handling').textContent = report.error_handling_style || 'N/A';
    document.getElementById('error-detail').textContent = 'style';
    
    document.getElementById('code-quality').textContent = report.code_quality_score || 0;
    
    // Show report
    reportEl.style.display = 'block';
    reportEl.scrollIntoView({ behavior: 'smooth' });
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
                
                showSuccess('Style guide downloaded!');
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

