/**
 * Upload Page JavaScript
 */

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
    selectedFiles = Array.from(files).filter(f => f.name.endsWith('.py'));
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
            showError('Please select at least one Python file');
            return;
        }
        
        hideError();
        showLoading('Uploading and analyzing files...');
        
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        
        try {
            const response = await fetch(`${API_BASE}/api/analyze-files`, {
                method: 'POST',
                body: formData
            });
            
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
        showLoading(`Analyzing ${username}'s repositories...`);
        
        try {
            const response = await fetch(`${API_BASE}/api/analyze-github`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                hideLoading();
                saveStyleProfile(data.report);
                displayReport(data.report);
            } else {
                hideLoading();
                showError(data.error || 'Analysis failed');
            }
        } catch (error) {
            hideLoading();
            showError('Network error: ' + error.message);
        }
    });
}

function displayReport(report) {
    const reportEl = document.getElementById('analysis-report');
    if (!reportEl) return;
    
    // Update report values
    document.getElementById('naming-style').textContent = report.naming_style || 'N/A';
    document.getElementById('naming-detail').textContent = `${report.naming_confidence || 0}% confidence`;
    
    document.getElementById('documentation').textContent = `${report.documentation_percentage || 0}%`;
    
    document.getElementById('type-hints').textContent = `${report.type_hints_percentage || 0}%`;
    
    document.getElementById('error-handling').textContent = report.error_handling_style || 'N/A';
    document.getElementById('error-detail').textContent = 'style';
    
    document.getElementById('code-quality').textContent = report.code_quality_score || 0;
    
    // Show report
    reportEl.style.display = 'block';
    reportEl.scrollIntoView({ behavior: 'smooth' });
}

