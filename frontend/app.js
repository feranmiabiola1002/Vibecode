// app.js - Vibecode Frontend

// ─── API URL ──────────────────────────────────────────────────
const API_URL = (() => {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:5000/api';
    }
    if (window.location.hostname.includes('onrender.com')) {
        return 'https://vibecode-backend.onrender.com/api';
    }
    return '/api';
})();

console.log('🔗 API_URL:', API_URL);

// ─── DOM ──────────────────────────────────────────────────
const promptInput = document.getElementById('promptInput');
const languageSelect = document.getElementById('languageSelect');
const generateBtn = document.getElementById('generateBtn');
const deployBtn = document.getElementById('deployBtn');
const downloadBtn = document.getElementById('downloadBtn');
const copyBtn = document.getElementById('copyBtn');
const clearBtn = document.getElementById('clearBtn');
const codeOutput = document.getElementById('codeOutput');
const explanationOutput = document.getElementById('explanationOutput');
const languageBadge = document.getElementById('languageBadge');
const statusEl = document.getElementById('status');
const deployStatus = document.getElementById('deployStatus');

let currentCode = '';
let currentLanguage = 'python';

// ─── TOAST ──────────────────────────────────────────────────
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => { toast.className = 'toast'; }, 4000);
}

// ─── CHECK STATUS ──────────────────────────────────────────
async function checkStatus() {
    try {
        const r = await fetch(API_URL.replace('/api', '') + '/api/health');
        if (r.ok) {
            statusEl.textContent = '● Online';
            statusEl.style.color = '#48bb78';
        } else {
            statusEl.textContent = '● Offline';
            statusEl.style.color = '#ef5350';
        }
    } catch {
        statusEl.textContent = '● Offline';
        statusEl.style.color = '#ef5350';
    }
}
setInterval(checkStatus, 30000);
checkStatus();

// ─── GENERATE ──────────────────────────────────────────────
async function generateCode() {
    const prompt = promptInput.value.trim();
    const language = languageSelect.value;
    if (!prompt) {
        showToast('Please describe what code you need', 'warning');
        return;
    }

    generateBtn.disabled = true;
    generateBtn.textContent = '⏳...';
    codeOutput.innerHTML = '<div class="loading"></div>';

    try {
        const r = await fetch(`${API_URL}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, language })
        });
        const data = await r.json();

        if (data.code) {
            currentCode = data.code;
            currentLanguage = data.language || language;
            languageBadge.textContent = currentLanguage.toUpperCase();
            codeOutput.textContent = data.code;
            explanationOutput.innerHTML = data.explanation || 'No explanation.';
            showToast('✅ Code generated!', 'success');
        } else {
            codeOutput.innerHTML = `<div style="color:#ef5350;">❌ ${data.error || 'Failed'}</div>`;
            showToast('Generation failed', 'error');
        }
    } catch (e) {
        codeOutput.innerHTML = `<div style="color:#ef5350;">❌ Connection error: ${e.message}</div>`;
        showToast('Connection error', 'error');
    }

    generateBtn.disabled = false;
    generateBtn.textContent = '⚡ Generate';
}

// ─── DEPLOY ──────────────────────────────────────────────────
async function deployProject() {
    const prompt = promptInput.value.trim();
    if (!prompt) {
        showToast('Describe what you want to deploy', 'warning');
        return;
    }

    deployBtn.disabled = true;
    deployBtn.textContent = '⏳...';
    deployStatus.textContent = '🚀 Generating...';

    try {
        const r = await fetch(`${API_URL}/deploy`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        const project = await r.json();

        if (project.structure) {
            deployStatus.innerHTML = `
                ✅ Project <strong>${project.name}</strong> ready!
                <br>📦 ${Object.keys(project.structure).length} files
                <br>🚀 Deploy to: <strong>${project.platform}</strong>
                <br>🌐 <a href="${project.url}" target="_blank" style="color:#6c5ce7;">${project.url}</a>
            `;
            const backendCode = project.structure['backend.py'] || '';
            if (backendCode) {
                currentCode = backendCode;
                languageBadge.textContent = 'PYTHON';
                codeOutput.textContent = backendCode;
                explanationOutput.innerHTML = `🚀 Project: ${project.name}<br>Platform: ${project.platform}<br>${project.instructions}`;
            }
            showToast(`✅ Project "${project.name}" generated!`, 'success');
        } else {
            deployStatus.textContent = '❌ Deployment failed';
            showToast('Deployment failed', 'error');
        }
    } catch (e) {
        deployStatus.textContent = `❌ Error: ${e.message}`;
        showToast('Deployment error', 'error');
    }

    deployBtn.disabled = false;
    deployBtn.textContent = '🚀 Deploy';
}

// ─── DOWNLOAD ──────────────────────────────────────────────
async function downloadProject() {
    const prompt = promptInput.value.trim();
    if (!prompt) {
        showToast('Describe what to download', 'warning');
        return;
    }

    downloadBtn.disabled = true;
    downloadBtn.textContent = '⏳...';

    try {
        const r = await fetch(`${API_URL}/download`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        if (r.ok) {
            const blob = await r.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'vibecode-project.zip';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showToast('⬇️ Downloaded!', 'success');
        } else {
            showToast('Download failed', 'error');
        }
    } catch (e) {
        showToast('Download error: ' + e.message, 'error');
    }

    downloadBtn.disabled = false;
    downloadBtn.textContent = '⬇️ ZIP';
}

// ─── COPY ──────────────────────────────────────────────────
function copyCode() {
    if (!currentCode) {
        showToast('Generate code first', 'warning');
        return;
    }
    navigator.clipboard.writeText(currentCode).then(() => {
        showToast('📋 Copied!', 'success');
    }).catch(() => {
        const ta = document.createElement('textarea');
        ta.value = currentCode;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast('📋 Copied!', 'success');
    });
}

// ─── CLEAR ──────────────────────────────────────────────────
function clearOutput() {
    currentCode = '';
    codeOutput.innerHTML = '<div class="placeholder">Describe what you want and click Generate</div>';
    explanationOutput.innerHTML = '<span class="placeholder">Explanation will appear here...</span>';
    languageBadge.textContent = 'PYTHON';
    deployStatus.textContent = '';
    showToast('Cleared', 'info');
}

// ─── QUICK PROMPTS ──────────────────────────────────────────
document.querySelectorAll('[data-prompt]').forEach(btn => {
    btn.addEventListener('click', () => {
        promptInput.value = btn.dataset.prompt;
        if (btn.textContent.includes('🚀')) {
            deployProject();
        } else {
            generateCode();
        }
    });
});

// ─── EVENT LISTENERS ──────────────────────────────────────
generateBtn.addEventListener('click', generateCode);
deployBtn.addEventListener('click', deployProject);
downloadBtn.addEventListener('click', downloadProject);
copyBtn.addEventListener('click', copyCode);
clearBtn.addEventListener('click', clearOutput);

// ─── INIT ──────────────────────────────────────────────────
console.log('⚡ Vibecode initialized');
showToast('⚡ Vibecode ready!', 'info');
