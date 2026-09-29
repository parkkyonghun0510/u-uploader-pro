/**
 * YouTube Uploader Pro - Multi-Channel, OAuth & Studio Asset Hub
 * Manages Google OAuth, Supabase Channel accounts, upload templates, batching, and YouTube Data API v3.
 */

import { api } from './api.js';
import { API_BASE } from './constants.js';
import {
    showToast,
    openModal,
    closeModal
} from './ui.js';
import {
    saveYouTubeApiKey,
    loadYouTubeChannels,
    searchYouTubeVideos
} from './youtube.js';

export function initChannelTabs() {
    document.querySelectorAll('#channelTabs .tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('#channelTabs .tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const tabName = tab.dataset.tab;
            document.querySelectorAll('#accountsTab, #channelsTab, #templatesTab, #bulkTab, #youtubeTab').forEach(s => s.classList.add('hidden'));

            const target = document.getElementById(tabName + 'Tab');
            if (target) target.classList.remove('hidden');

            if (tabName === 'accounts') loadAccounts();
            if (tabName === 'channels') loadChannels();
            if (tabName === 'templates') loadTemplates();
            if (tabName === 'bulk') loadBatches();
        });
    });

    // Add Channel button
    document.getElementById('addChannelBtn')?.addEventListener('click', () => {
        const bodyHtml = `
            <form id="addChannelForm">
                <div class="form-group"><label class="form-label">Account</label><select id="chAccount" class="form-control"></select></div>
                <div class="form-group"><label class="form-label">Channel Name</label><input type="text" id="chName" class="form-control" placeholder="Gaming Central" required></div>
                <div class="form-group"><label class="form-label">Handle</label><input type="text" id="chHandle" class="form-control" placeholder="@gamingcentral"></div>
                <div class="form-group"><label class="form-label">Description</label><textarea id="chDesc" class="form-control" placeholder="Daily gaming streams and video uploads"></textarea></div>
            </form>
        `;
        const footerHtml = `
            <button class="btn btn-primary" onclick="saveChannelFromModal()">Add Channel</button>
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        `;
        openModal('Add Channel', bodyHtml, footerHtml);
        loadAccountsForSelect('chAccount');
    });

    // Add Template button
    document.getElementById('addTemplateBtn')?.addEventListener('click', () => {
        const bodyHtml = `
            <form id="addTemplateForm">
                <div class="form-group"><label class="form-label">Channel</label><select id="tmplChannel" class="form-control"></select></div>
                <div class="form-group"><label class="form-label">Template Name</label><input type="text" id="tmplName" class="form-control" placeholder="Series Upload Preset" required></div>
                <div class="form-group"><label class="form-label">Title Template</label><input type="text" id="tmplTitle" class="form-control" placeholder="{video_title} - Episode {episode}"></div>
                <div class="form-group"><label class="form-label">Description Template</label><textarea id="tmplDesc" class="form-control" placeholder="{video_description}\n\nSubscribe for more!"></textarea></div>
                <div class="form-group"><label class="form-label">Tags (comma separated)</label><input type="text" id="tmplTags" class="form-control" placeholder="gaming, letsplay, walkthrough"></div>
            </form>
        `;
        const footerHtml = `
            <button class="btn btn-primary" onclick="saveTemplateFromModal()">Save Template</button>
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        `;
        openModal('Create Template', bodyHtml, footerHtml);
        loadAccountsForSelect('tmplChannel');
    });

    // Bulk upload and YouTube API buttons
    document.getElementById('bulkUploadForm')?.addEventListener('submit', handleBulkUpload);
    document.getElementById('saveApiKey')?.addEventListener('click', saveYouTubeApiKey);
    document.getElementById('loadMyChannels')?.addEventListener('click', loadYouTubeChannels);
    document.getElementById('searchYouTube')?.addEventListener('click', searchYouTubeVideos);
}

// ===== Google OAuth2 & Config =====
export function initOAuth() {
    const connectBtn = document.getElementById('connectGoogleBtn');
    if (connectBtn) {
        connectBtn.addEventListener('click', connectGoogle);
    }
}

export async function openConfigOAuthModal() {
    try {
        const configData = await api.get('/api/youtube/oauth/config');
        const redirectUri = window.location.origin + '/api/youtube/oauth/callback';
        const existingClientId = configData?.client?.client_id || '';
        const isConfigured = configData?.configured || false;

        const bodyHtml = `
            <form id="configOAuthForm" onsubmit="event.preventDefault(); saveOAuthCredentialsFromModal();">
                <div class="form-group">
                    <label class="form-label"><i class="fas fa-link text-primary"></i> Authorized Redirect URI</label>
                    <div style="display:flex; gap:8px;">
                        <input type="text" id="oauthRedirectUri" class="form-control" value="${redirectUri}" readonly style="background:var(--bg-secondary, #1a1a24); font-family:monospace; font-size:13px;">
                        <button type="button" class="btn btn-secondary" style="white-space:nowrap;" onclick="navigator.clipboard.writeText(document.getElementById('oauthRedirectUri').value); showToast('Redirect URI copied to clipboard!', 'success');">
                            <i class="fas fa-copy"></i> Copy
                        </button>
                    </div>
                    <small class="form-help">In <a href="https://console.cloud.google.com/apis/credentials" target="_blank" style="color:var(--accent,#4f8cff);">Google Cloud Console</a> &gt; Credentials &gt; OAuth 2.0 Client ID, add this exact URI under <b>Authorized redirect URIs</b>.</small>
                </div>
                <div class="form-group">
                    <label class="form-label">Client ID <span class="text-danger">*</span></label>
                    <input type="text" id="oauthClientId" class="form-control" placeholder="e.g. 123456789-xxx.apps.googleusercontent.com" value="${existingClientId}" required>
                    ${isConfigured ? `<small class="text-success"><i class="fas fa-check-circle"></i> Active client configured (${configData.client.name || 'YouTube Upload Pro'})</small>` : ''}
                </div>
                <div class="form-group">
                    <label class="form-label">Client Secret <span class="text-danger">*</span></label>
                    <input type="password" id="oauthClientSecret" class="form-control" placeholder="${isConfigured ? '•••••••• (Enter new to replace)' : 'e.g. GOCSPX-xxxxxx'}" ${isConfigured ? '' : 'required'}>
                </div>
                <div class="form-group">
                    <label class="form-label">Client / App Name</label>
                    <input type="text" id="oauthAppName" class="form-control" value="${configData?.client?.name || 'YouTube Upload Pro'}">
                </div>
            </form>
        `;
        const footerHtml = `
            <button type="button" class="btn btn-primary" onclick="saveOAuthCredentialsFromModal()"><i class="fas fa-save"></i> Save Credentials</button>
            <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        `;
        openModal('Configure Google OAuth 2.0 Credentials', bodyHtml, footerHtml);
    } catch (err) {
        showToast('Failed to load OAuth config: ' + err.message, 'error');
    }
}

export async function saveOAuthCredentialsFromModal() {
    const clientId = document.getElementById('oauthClientId')?.value?.trim();
    const clientSecret = document.getElementById('oauthClientSecret')?.value?.trim();
    const appName = document.getElementById('oauthAppName')?.value?.trim() || 'YouTube Upload Pro';

    if (!clientId) {
        showToast('Client ID is required', 'warning');
        return;
    }
    if (!clientSecret) {
        showToast('Client Secret is required', 'warning');
        return;
    }

    try {
        const res = await api.post('/api/youtube/oauth/register', {
            client_id: clientId,
            client_secret: clientSecret,
            name: appName
        });
        showToast(res.message || 'Google OAuth credentials saved!', 'success');
        closeModal();
    } catch (err) {
        showToast('Failed to save OAuth credentials: ' + err.message, 'error');
    }
}

export async function openBrowserLoginModal() {
    try {
        let profiles = [];
        try {
            profiles = await api.get('/api/channels/browser-profiles');
        } catch {
            profiles = [];
        }

        const profileRows = profiles.length > 0
            ? profiles.map(p => `
                <tr style="border-bottom:1px solid var(--border-color,#2d3248);">
                    <td style="padding:8px;font-weight:600;"><i class="fas fa-folder text-primary"></i> ${p.name}</td>
                    <td style="padding:8px;font-family:monospace;font-size:12px;color:var(--text-muted,#8a94a6);">${p.path}</td>
                    <td style="padding:8px;">
                        ${p.has_cookies
                            ? '<span class="badge badge-success" style="background:#10b981;color:#fff;padding:2px 8px;border-radius:4px;"><i class="fas fa-check"></i> Session Ready</span>'
                            : '<span class="badge badge-warning" style="background:#f59e0b;color:#fff;padding:2px 8px;border-radius:4px;"><i class="fas fa-exclamation-triangle"></i> No Cookies Yet</span>'}
                    </td>
                </tr>
            `).join('')
            : `<tr><td colspan="3" style="padding:12px;text-align:center;color:var(--text-muted,#8a94a6);">No profiles found yet. Run the login command below to initialize your first profile.</td></tr>`;

        const bodyHtml = `
            <div style="line-height:1.6;">
                <p>Selenium automates YouTube Studio video uploads directly in Firefox without YouTube API quota limits or verified project restrictions.</p>

                <h4 style="margin-top:16px;margin-bottom:8px;"><i class="fas fa-terminal text-primary"></i> Quick Login Command:</h4>
                <div style="background:var(--bg-secondary,#1a1a24);padding:12px;border-radius:8px;border:1px solid var(--border-color,#2d3248);margin-bottom:16px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                        <span style="font-size:12px;color:var(--text-muted,#8a94a6);">Run in terminal from project root:</span>
                        <button class="btn btn-sm btn-secondary" onclick="navigator.clipboard.writeText('python upload.py --login --profile default'); showToast('Command copied!','success');">
                            <i class="fas fa-copy"></i> Copy
                        </button>
                    </div>
                    <code style="color:#38bdf8;font-size:14px;word-break:break-all;">python upload.py --login --profile default</code>
                </div>

                <div style="background:rgba(59,130,246,0.08);border-left:3px solid #3b82f6;padding:12px;border-radius:4px;margin-bottom:16px;">
                    <strong>Steps:</strong>
                    <ol style="margin:6px 0 0 16px;padding:0;">
                        <li>Firefox launches automatically with the profile.</li>
                        <li>Log in to your YouTube / Google account and verify channel access.</li>
                        <li>Return to terminal and press <code>[Enter]</code> to save cookies.</li>
                        <li>Your channel profile is now permanently authenticated for automated uploads!</li>
                    </ol>
                </div>

                <h4 style="margin-bottom:8px;"><i class="fas fa-layer-group text-primary"></i> Detected Browser Profiles:</h4>
                <div style="max-height:160px;overflow-y:auto;border:1px solid var(--border-color,#2d3248);border-radius:6px;">
                    <table style="width:100%;border-collapse:collapse;font-size:13px;">
                        <thead>
                            <tr style="background:var(--bg-secondary,#1a1a24);text-align:left;border-bottom:1px solid var(--border-color,#2d3248);">
                                <th style="padding:8px;">Profile Name</th>
                                <th style="padding:8px;">Directory</th>
                                <th style="padding:8px;">Status</th>
                            </tr>
                        </thead>
                        <tbody>${profileRows}</tbody>
                    </table>
                </div>
            </div>
        `;

        const footerHtml = `
            <button type="button" class="btn btn-secondary" onclick="closeModal()">Close</button>
        `;
        openModal('Selenium Browser Session Guide', bodyHtml, footerHtml);
    } catch (err) {
        showToast('Error displaying browser session guide: ' + err.message, 'error');
    }
}

export async function connectGoogle() {
    try {
        const redirectUri = window.location.origin + '/api/youtube/oauth/callback';
        const data = await api.post('/api/oauth/google', { redirect_uri: redirectUri });
        if (data.auth_url) {
            const popup = window.open(data.auth_url, 'Google OAuth', 'width=620,height=720');
            showToast('Google OAuth opened. Please authorize access in popup.', 'info');
            const clientId = data.client_id || '';

            const onMessage = (event) => {
                if (event.data && event.data.type === 'OAUTH_COMPLETE') {
                    clearInterval(checkAuth);
                    window.removeEventListener('message', onMessage);
                    if (event.data.status === 'success') {
                        showToast(event.data.message || 'YouTube account connected successfully!', 'success');
                    } else {
                        showToast(event.data.error || 'Failed to connect YouTube account', 'error');
                    }
                    try { if (popup && !popup.closed) popup.close(); } catch {}
                    loadAccounts();
                }
            };
            window.addEventListener('message', onMessage);

            const checkAuth = setInterval(async () => {
                if (!popup || popup.closed) {
                    clearInterval(checkAuth);
                    window.removeEventListener('message', onMessage);
                    loadAccounts();
                    return;
                }
                try {
                    const url = popup.location.href;
                    if (url.includes('/api/youtube/oauth/callback')) {
                        clearInterval(checkAuth);
                        window.removeEventListener('message', onMessage);
                        const code = new URL(url).searchParams.get('code');
                        const stateParam = new URL(url).searchParams.get('state');
                        const callbackRes = await api.get(`/api/youtube/oauth/callback?code=${code}&state=${stateParam}&client_id=${encodeURIComponent(clientId)}&redirect_uri=${encodeURIComponent(redirectUri)}`);
                        if (callbackRes.message) {
                            showToast(callbackRes.message, 'success');
                            try { popup.close(); } catch {}
                            loadAccounts();
                        } else if (callbackRes.error) {
                            showToast(`Error: ${callbackRes.error}`, 'error');
                            try { popup.close(); } catch {}
                        }
                    }
                } catch {
                    // Cross-origin restriction while Google flow is in progress
                }
            }, 1000);
        } else {
            if (data.needs_configuration || (data.error && data.error.includes('not configured'))) {
                showToast('Google OAuth credentials not configured yet. Opening setup...', 'info');
                openConfigOAuthModal();
            } else {
                showToast(data.error || 'Failed to initialize authorization URL', 'error');
            }
        }
    } catch (err) {
        if (err.message && err.message.includes('not configured')) {
            showToast('Google OAuth credentials not configured yet. Opening setup...', 'info');
            openConfigOAuthModal();
        } else {
            showToast('Google connection failed: ' + err.message, 'error');
        }
    }
}

// ===== Dual-Engine Connection Command Hub Status =====
export function copyLoginCommand() {
    const cmd = document.getElementById('loginCliCommand')?.innerText || 'python upload.py --login --profile default';
    navigator.clipboard.writeText(cmd).then(() => {
        showToast('Login command copied to clipboard!', 'success');
    });
}

export function copyRedirectUri() {
    const uri = document.getElementById('hubRedirectUriDisplay')?.innerText || (window.location.origin + '/api/youtube/oauth/callback');
    navigator.clipboard.writeText(uri).then(() => {
        showToast('Redirect URI copied to clipboard!', 'success');
    });
}

export async function updateConnectionHubStatus() {
    // 1. Studio Profiles Status
    const studioStatusEl = document.getElementById('studioSessionStatus');
    const profilesSummaryEl = document.getElementById('detectedProfilesSummary');
    try {
        const profiles = await api.get('/api/channels/browser-profiles');
        if (studioStatusEl && profilesSummaryEl) {
            const readyProfiles = profiles.filter(p => p.has_cookies);
            if (readyProfiles.length > 0) {
                studioStatusEl.className = 'engine-status-pill status-pill-ready';
                studioStatusEl.innerHTML = `<span class="status-dot"></span> Session Ready (${readyProfiles.length} active)`;
            } else {
                studioStatusEl.className = 'engine-status-pill status-pill-warning';
                studioStatusEl.innerHTML = `<span class="status-dot"></span> Sign-in Required`;
            }
            profilesSummaryEl.innerHTML = `<i class="fas fa-folder-open text-primary"></i> ${profiles.length} browser profile${profiles.length === 1 ? '' : 's'} (${readyProfiles.length} authenticated)`;
        }
    } catch {
        if (studioStatusEl) {
            studioStatusEl.className = 'engine-status-pill status-pill-loading';
            studioStatusEl.innerHTML = `<span class="status-dot"></span> Standby`;
        }
    }

    // 2. OAuth Status
    const oauthStatusEl = document.getElementById('oauthEngineStatus');
    const redirectDisplayEl = document.getElementById('hubRedirectUriDisplay');
    const currentRedirect = window.location.origin + '/api/youtube/oauth/callback';
    if (redirectDisplayEl) {
        redirectDisplayEl.innerText = currentRedirect;
    }

    try {
        const configData = await api.get('/api/youtube/oauth/config');
        if (oauthStatusEl) {
            if (configData && configData.configured) {
                oauthStatusEl.className = 'engine-status-pill status-pill-ready';
                oauthStatusEl.innerHTML = `<span class="status-dot"></span> Configured (${configData.client?.name || 'Active'})`;
            } else {
                oauthStatusEl.className = 'engine-status-pill status-pill-warning';
                oauthStatusEl.innerHTML = `<span class="status-dot"></span> Credentials Needed`;
            }
        }
    } catch {
        if (oauthStatusEl) {
            oauthStatusEl.className = 'engine-status-pill status-pill-loading';
            oauthStatusEl.innerHTML = `<span class="status-dot"></span> Unconfigured`;
        }
    }
}

// ===== Accounts Management =====
export async function loadAccounts() {
    updateConnectionHubStatus();
    try {
        let accounts = [];
        try {
            accounts = await api.get('/api/supabase/accounts');
        } catch {
            // fallback to local channel manager accounts
            try {
                accounts = await api.get('/api/channels/accounts');
            } catch {
                accounts = [];
            }
        }
        const badge = document.getElementById('accountCountBadge');
        if (badge) {
            badge.innerText = `${accounts.length} Account${accounts.length === 1 ? '' : 's'}`;
        }
        renderAccounts(accounts);
    } catch (err) {
        console.error('Failed to load accounts:', err);
    }
}

export function renderAccounts(accounts = []) {
    const container = document.getElementById('accountsList');
    if (!container) return;

    if (!Array.isArray(accounts) || accounts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon-ring"><i class="fab fa-youtube"></i></div>
                <h3>No channels connected</h3>
                <p>Run <code>python upload.py --login</code> for Studio uploads or click "Connect with Google" above.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = accounts.map(acc => {
        const isOAuth = !!(acc.access_token || (acc.id && String(acc.id).startsWith('oauth-')));
        return `
            <div class="account-card">
                <div class="account-avatar">
                    <i class="fas fa-${isOAuth ? 'tv' : 'user'}"></i>
                </div>
                <div class="account-info">
                    <h4>${acc.display_name || 'Account'}</h4>
                    <p>${acc.email || 'Local channel account'}</p>
                    <div class="engine-track-badges" style="margin-top:6px;">
                        <span class="track-badge track-badge-studio">
                            <i class="fas fa-film"></i> Studio Direct: Ready
                        </span>
                        <span class="track-badge ${isOAuth ? 'track-badge-oauth' : 'track-badge-inactive'}">
                            <i class="fab fa-google"></i> ${isOAuth ? 'Data API: Synced' : 'Data API: Offline'}
                        </span>
                    </div>
                </div>
                <span class="account-badge ${acc.account_type || 'personal'}">${(acc.account_type || 'personal').toUpperCase()}</span>
                <span class="status-badge ${acc.is_active ? 'status-completed' : 'status-failed'}">${acc.is_active ? 'Active' : 'Inactive'}</span>
                <button class="btn btn-sm btn-icon text-danger" onclick="deleteAccount('${acc.id}')" title="Disconnect Account">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
    }).join('');
}

export async function deleteAccount(accountId) {
    if (!confirm('Are you sure you want to disconnect this account?')) return;
    try {
        await api.delete(`/api/supabase/accounts/${accountId}`);
        showToast('Account removed successfully', 'info');
        loadAccounts();
    } catch (err) {
        showToast('Failed to remove account: ' + err.message, 'error');
    }
}

export async function addAccount() {
    const email = document.getElementById('accEmail')?.value?.trim() || '';
    const name = document.getElementById('accName')?.value?.trim() || '';
    const type = document.getElementById('accType')?.value || 'personal';

    if (!email || !name) {
        showToast('Please enter both name and email', 'warning');
        return;
    }

    try {
        await api.post('/api/supabase/accounts', { email, display_name: name, account_type: type });
        showToast('Account registered!', 'success');
        closeAddAccountModal();
        loadAccounts();
    } catch (err) {
        showToast('Failed to add account: ' + err.message, 'error');
    }
}

export function openAddAccountModal() {
    const modal = document.getElementById('addAccountModal');
    if (modal) modal.classList.remove('hidden');
}

export function closeAddAccountModal() {
    const modal = document.getElementById('addAccountModal');
    if (modal) modal.classList.add('hidden');
}

// ===== Channel Management =====
export async function loadChannels() {
    try {
        const channels = await api.get('/api/channels');
        renderChannels(channels);
    } catch (err) {
        console.error('Failed to load channels:', err);
    }
}

export function renderChannels(channels = []) {
    const container = document.getElementById('channelsList');
    if (!container) return;

    if (!Array.isArray(channels) || channels.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-tv"></i>
                <h3>No channels configured</h3>
                <p>Add a channel to target upload queues and automate distribution</p>
            </div>
        `;
        return;
    }

    container.innerHTML = channels.map(ch => `
        <div class="channel-card">
            <div class="channel-avatar"><i class="fas fa-tv"></i></div>
            <div class="channel-info">
                <h4>${ch.name}</h4>
                <p>${ch.handle || ch.channel_id} • ${ch.description ? ch.description.substring(0, 50) + '...' : 'No description'}</p>
            </div>
            <div class="channel-meta">
                <div class="channel-meta-item"><div class="number">${(ch.subscriber_count || 0).toLocaleString()}</div><div class="label">Subscribers</div></div>
                <div class="channel-meta-item"><div class="number">${(ch.video_count || 0).toLocaleString()}</div><div class="label">Videos</div></div>
            </div>
            <button class="btn btn-sm btn-icon text-danger" onclick="deleteChannel('${ch.channel_id}')" title="Delete Channel"><i class="fas fa-trash"></i></button>
        </div>
    `).join('');
}

export async function deleteChannel(channelId) {
    if (!confirm('Are you sure you want to remove this channel?')) return;
    try {
        await api.delete(`/api/channels/${channelId}`);
        showToast('Channel removed', 'info');
        loadChannels();
    } catch (err) {
        showToast('Failed to delete channel: ' + err.message, 'error');
    }
}

export async function saveChannelFromModal() {
    const accountId = document.getElementById('chAccount')?.value;
    const name = document.getElementById('chName')?.value?.trim();
    const handle = document.getElementById('chHandle')?.value?.trim();
    const desc = document.getElementById('chDesc')?.value?.trim();

    if (!name) {
        showToast('Channel name is required', 'warning');
        return;
    }

    try {
        await api.post('/api/channels', {
            account_id: accountId,
            channel_id: name.toLowerCase().replace(/\s+/g, '-'),
            name,
            handle,
            description: desc,
            is_managed: true
        });
        showToast('Channel created!', 'success');
        closeModal();
        loadChannels();
    } catch (err) {
        showToast('Failed to create channel: ' + err.message, 'error');
    }
}

// ===== Template Management =====
export async function loadTemplates() {
    try {
        const templates = await api.get('/api/templates');
        renderTemplates(templates);
    } catch (err) {
        console.error('Failed to load templates:', err);
    }
}

export function renderTemplates(templates = []) {
    const container = document.getElementById('templatesList');
    if (!container) return;

    if (!Array.isArray(templates) || templates.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-layer-group"></i>
                <h3>No templates yet</h3>
                <p>Standardize recurring titles, descriptions, and tag presets</p>
            </div>
        `;
        return;
    }

    container.innerHTML = templates.map(t => {
        const tags = Array.isArray(t.tags) ? t.tags : [];
        return `
            <div class="template-card">
                <h4>${t.name}</h4>
                <p>${t.description_template ? t.description_template.substring(0, 80) + '...' : 'No description template'}</p>
                <div class="template-tags">${tags.map(tag => `<span class="tag">${tag}</span>`).join('')}</div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px">
                    <small class="text-muted">${t.privacy_status || 'private'} • Category ${t.category || '22'}</small>
                    <button class="btn btn-sm btn-icon text-danger" onclick="deleteTemplate('${t.template_id}')" title="Delete Template"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        `;
    }).join('');
}

export async function deleteTemplate(templateId) {
    if (!confirm('Are you sure you want to delete this template?')) return;
    try {
        await api.delete(`/api/templates/${templateId}`);
        showToast('Template deleted', 'info');
        loadTemplates();
    } catch (err) {
        showToast('Failed to delete template: ' + err.message, 'error');
    }
}

export async function saveTemplateFromModal() {
    const channelId = document.getElementById('tmplChannel')?.value;
    const name = document.getElementById('tmplName')?.value?.trim();
    const titleTpl = document.getElementById('tmplTitle')?.value?.trim();
    const descTpl = document.getElementById('tmplDesc')?.value?.trim();
    const tags = (document.getElementById('tmplTags')?.value || '')
        .split(',')
        .map(t => t.trim())
        .filter(Boolean);

    if (!name || !channelId) {
        showToast('Please specify a template name and select a channel', 'warning');
        return;
    }

    try {
        await api.post('/api/templates', {
            channel_id: channelId,
            name,
            title_template: titleTpl,
            description_template: descTpl,
            tags
        });
        showToast('Template saved successfully!', 'success');
        closeModal();
        loadTemplates();
    } catch (err) {
        showToast('Failed to save template: ' + err.message, 'error');
    }
}

// ===== Batch Uploads & YouTube API v3 =====
export async function loadBatches() {
    try {
        const batches = await api.get('/api/batches');
        renderBatches(batches);
        loadBatchChannels();
    } catch (err) {
        console.error('Failed to load batches:', err);
    }
}

export function renderBatches(batches = []) {
    const container = document.getElementById('batchList');
    if (!container) return;

    if (!Array.isArray(batches) || batches.length === 0) {
        container.innerHTML = '<p class="text-muted" style="padding:16px 0;">No active batch pipelines</p>';
        return;
    }

    container.innerHTML = batches.map(b => {
        const percent = b.total_videos > 0 ? Math.round((b.uploaded_count / b.total_videos) * 100) : 0;
        return `
            <div class="batch-card">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <h4>${b.name}</h4>
                    <span class="status-badge status-${b.status}">${b.status}</span>
                </div>
                <div class="batch-progress"><div class="batch-progress-bar" style="width: ${percent}%"></div></div>
                <p class="text-muted">${b.uploaded_count}/${b.total_videos} videos uploaded • ${b.failed_count || 0} failed</p>
            </div>
        `;
    }).join('');
}

export async function loadBatchChannels() {
    try {
        const channels = await api.get('/api/channels');
        const select = document.getElementById('batchChannel');
        if (select) {
            select.innerHTML = '<option value="">Select channel</option>' +
                channels.map(c => `<option value="${c.channel_id}">${c.name}</option>`).join('');
        }
    } catch (err) {
        console.error('Failed to load channels for batch:', err);
    }
}

export async function handleBulkUpload(e) {
    e.preventDefault();
    const name = document.getElementById('batchName')?.value?.trim();
    const channelId = document.getElementById('batchChannel')?.value;

    if (!name || !channelId) {
        showToast('Batch name and channel are required', 'warning');
        return;
    }

    try {
        await api.post('/api/batches', {
            name,
            channel_id: channelId,
            account_id: '',
            video_paths: [],
            priority: 'normal'
        });
        showToast('Batch pipeline initialized!', 'success');
        loadBatches();
    } catch (err) {
        showToast('Failed to create batch: ' + err.message, 'error');
    }
}

export async function loadAccountsForSelect(selectId) {
    try {
        const accounts = await api.get('/api/channels/accounts');
        const select = document.getElementById(selectId);
        if (select && Array.isArray(accounts)) {
            select.innerHTML = accounts.map(a => `<option value="${a.account_id}">${a.display_name}</option>`).join('');
        }
    } catch (err) {
        console.error(`Failed to load accounts for ${selectId}:`, err);
    }
}

export { saveYouTubeApiKey, loadYouTubeChannels, searchYouTubeVideos };
