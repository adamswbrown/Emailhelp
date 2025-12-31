// Email Triage App - JavaScript

let currentEmails = [];
let currentFilter = null;
let autoRefreshInterval = null;
let currentReplyEmailId = null;

// Initialize app
async function init() {
    console.log('Initializing Email Triage App...');
    
    // Load templates
    await loadTemplates();
    
    // Load emails
    await refreshEmails();
    
    // Start auto-refresh
    startAutoRefresh();
}

// Load quick reply templates
async function loadTemplates() {
    try {
        const templatesJson = await pywebview.api.get_templates();
        const templates = JSON.parse(templatesJson);
        
        const container = document.getElementById('templates-container');
        container.innerHTML = '';
        
        for (const [id, template] of Object.entries(templates)) {
            const btn = document.createElement('button');
            btn.className = 'template-btn';
            btn.textContent = template.name;
            btn.onclick = () => useTemplate(id);
            container.appendChild(btn);
        }
    } catch (error) {
        console.error('Failed to load templates:', error);
    }
}

// Use a quick reply template
async function useTemplate(templateId) {
    try {
        const result = await pywebview.api.get_template_body(templateId);
        const data = JSON.parse(result);
        
        const textarea = document.getElementById('reply-body');
        textarea.value = data.body;
        textarea.focus();
    } catch (error) {
        console.error('Failed to load template:', error);
        alert('Failed to load template');
    }
}

// Refresh emails from database
async function refreshEmails() {
    try {
        updateStatus('Loading emails...');
        
        const emailsJson = await pywebview.api.get_emails(null, 100, 7, currentFilter);
        currentEmails = JSON.parse(emailsJson);
        
        renderEmails();
        updateCounts();
        updateStatus(`Last updated: ${new Date().toLocaleTimeString()}`);
    } catch (error) {
        console.error('Failed to load emails:', error);
        updateStatus('Error loading emails');
        document.getElementById('emails-container').innerHTML = `
            <div class="empty-state">
                <h3>Error loading emails</h3>
                <p>${error.message || 'Unknown error'}</p>
                <button onclick="refreshEmails()" class="btn-primary" style="margin-top: 20px;">Try Again</button>
            </div>
        `;
    }
}

// Render emails to UI
function renderEmails() {
    const container = document.getElementById('emails-container');
    
    if (currentEmails.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>📭 No emails found</h3>
                <p>All caught up!</p>
            </div>
        `;
        return;
    }
    
    // Group by category
    const grouped = {
        'ACTION': [],
        'FYI': [],
        'IGNORE': []
    };
    
    currentEmails.forEach(email => {
        if (grouped[email.category]) {
            grouped[email.category].push(email);
        }
    });
    
    let html = '';
    
    // Render ACTION emails
    if (grouped['ACTION'].length > 0) {
        html += `
            <div class="category-section">
                <div class="category-header">
                    <span>🔴 ACTION - Needs Your Attention (${grouped['ACTION'].length})</span>
                </div>
                ${grouped['ACTION'].map(email => renderEmailCard(email)).join('')}
            </div>
        `;
    }
    
    // Render FYI emails
    if (grouped['FYI'].length > 0 && (!currentFilter || currentFilter === 'FYI')) {
        html += `
            <div class="category-section">
                <div class="category-header">
                    <span>🟡 FYI - Informational (${grouped['FYI'].length})</span>
                </div>
                ${grouped['FYI'].map(email => renderEmailCard(email)).join('')}
            </div>
        `;
    }
    
    // Render IGNORE emails
    if (grouped['IGNORE'].length > 0 && (!currentFilter || currentFilter === 'IGNORE')) {
        html += `
            <div class="category-section">
                <div class="category-header">
                    <span>⚪ IGNORE - Bulk/Automated (${grouped['IGNORE'].length})</span>
                </div>
                ${grouped['IGNORE'].map(email => renderEmailCard(email)).join('')}
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Render individual email card
function renderEmailCard(email) {
    const scoreClass = `score-${email.category.toLowerCase()}`;
    
    // Format signals
    const signalsHtml = Object.entries(email.signals)
        .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
        .map(([name, points]) => `${name}(${points >= 0 ? '+' : ''}${points})`)
        .join(', ');
    
    return `
        <div class="email-card" data-email-id="${email.id}">
            <div class="email-header">
                <div>
                    <div class="email-from">${escapeHtml(email.from)}</div>
                </div>
                <div class="email-meta">
                    <span class="email-score ${scoreClass}">${email.score}</span>
                    <span>${email.time_ago}</span>
                </div>
            </div>
            
            <div class="email-subject">${escapeHtml(email.subject)}</div>
            <div class="email-preview">${escapeHtml(email.preview)}</div>
            <div class="email-signals">${signalsHtml}</div>
            
            <div class="email-actions">
                <button class="btn-action btn-primary-action" onclick="showReplyModal('${email.id}'); event.stopPropagation();">
                    ✉️ Reply
                </button>
                <button class="btn-action" onclick="exportToGPT('${email.id}', false); event.stopPropagation();">
                    📋 Copy to GPT
                </button>
                <button class="btn-action" onclick="exportToGPT('${email.id}', true); event.stopPropagation();">
                    🤖 Draft with GPT
                </button>
                <button class="btn-action" onclick="markDone('${email.id}'); event.stopPropagation();">
                    ✅ Mark Done
                </button>
            </div>
        </div>
    `;
}

// Update category counts
function updateCounts() {
    const counts = {
        'ACTION': 0,
        'FYI': 0,
        'IGNORE': 0
    };
    
    currentEmails.forEach(email => {
        if (counts[email.category] !== undefined) {
            counts[email.category]++;
        }
    });
    
    document.getElementById('action-count').textContent = counts['ACTION'];
    document.getElementById('fyi-count').textContent = counts['FYI'];
    document.getElementById('ignore-count').textContent = counts['IGNORE'];
    document.getElementById('total-count').textContent = currentEmails.length;
}

// Update status text
function updateStatus(text) {
    document.getElementById('status-text').textContent = text;
}

// Filter by category
async function filterCategory(category) {
    currentFilter = category;
    await refreshEmails();
}

// Show reply modal
async function showReplyModal(emailId) {
    currentReplyEmailId = emailId;
    
    const email = currentEmails.find(e => e.id == emailId);
    if (!email) {
        alert('Email not found');
        return;
    }
    
    document.getElementById('reply-to').textContent = email.from;
    document.getElementById('reply-subject').textContent = `Re: ${email.subject}`;
    document.getElementById('reply-body').value = '';
    
    const modal = document.getElementById('reply-modal');
    modal.classList.add('active');
}

// Close reply modal
function closeReplyModal() {
    const modal = document.getElementById('reply-modal');
    modal.classList.remove('active');
    currentReplyEmailId = null;
}

// Send reply
async function sendReply() {
    if (!currentReplyEmailId) return;
    
    const replyBody = document.getElementById('reply-body').value.trim();
    if (!replyBody) {
        alert('Please enter a reply message');
        return;
    }
    
    try {
        updateStatus('Sending reply...');
        
        const resultJson = await pywebview.api.send_reply(currentReplyEmailId, replyBody, false);
        const result = JSON.parse(resultJson);
        
        if (result.success) {
            alert('✅ Reply sent successfully!');
            closeReplyModal();
            await refreshEmails();
        } else {
            alert(`❌ Failed to send: ${result.message}`);
        }
        
        updateStatus('Ready');
    } catch (error) {
        console.error('Failed to send reply:', error);
        alert('Failed to send reply: ' + error.message);
        updateStatus('Error');
    }
}

// Open reply window in Mail.app
async function openReplyInMail() {
    if (!currentReplyEmailId) return;
    
    const replyBody = document.getElementById('reply-body').value.trim();
    
    try {
        const resultJson = await pywebview.api.open_reply_window(currentReplyEmailId, replyBody);
        const result = JSON.parse(resultJson);
        
        if (result.success) {
            alert('✅ Reply window opened in Mail.app');
            closeReplyModal();
        } else {
            alert(`❌ Failed: ${result.message}`);
        }
    } catch (error) {
        console.error('Failed to open reply window:', error);
        alert('Failed to open reply window');
    }
}

// Export to GPT
async function exportToGPT(emailId, forDraft) {
    try {
        const resultJson = await pywebview.api.export_to_gpt(emailId, forDraft);
        const result = JSON.parse(resultJson);
        
        if (result.success) {
            // Show notification
            updateStatus('✅ ' + result.message);
            setTimeout(() => updateStatus('Ready'), 3000);
        } else {
            alert('Failed to export: ' + result.message);
        }
    } catch (error) {
        console.error('Failed to export to GPT:', error);
        alert('Failed to export to GPT');
    }
}

// Draft with GPT from reply modal
async function draftWithGPT() {
    if (!currentReplyEmailId) return;
    
    await exportToGPT(currentReplyEmailId, true);
    alert('📋 Email context copied to clipboard!\n\nPaste into ChatGPT to get a draft reply, then paste it back here.');
}

// Mark email as done
async function markDone(emailId) {
    try {
        const resultJson = await pywebview.api.mark_done(emailId);
        const result = JSON.parse(resultJson);
        
        if (result.success) {
            await refreshEmails();
        } else {
            alert('Failed to mark as done');
        }
    } catch (error) {
        console.error('Failed to mark as done:', error);
        alert('Failed to mark as done');
    }
}

// Auto-refresh
function startAutoRefresh() {
    const checkbox = document.getElementById('auto-refresh');
    if (checkbox.checked) {
        // Refresh every 3 minutes
        autoRefreshInterval = setInterval(refreshEmails, 3 * 60 * 1000);
    }
}

function toggleAutoRefresh() {
    const checkbox = document.getElementById('auto-refresh');
    
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
    
    if (checkbox.checked) {
        startAutoRefresh();
    }
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', init);
