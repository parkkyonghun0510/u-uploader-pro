/**
 * YouTube Uploader Pro - Multi-Channel, OAuth & Studio Asset Hub
 * Manages Google OAuth, Supabase Channel accounts, upload templates, batching, and YouTube Data API v3.
 */

import { api } from './api.js';
import { API_BASE } from './constants.js';
import { navigateTo } from './navigation.js';
import { populateChannelDropdown } from './upload.js';
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
            <form id="addChannelForm" onsubmit="event.preventDefault(); saveChannelFromModal();">
                <div class="form-group"><label class="form-label">Linked Account</label><select id="chAccount" class="form-control"></select></div>
                <div class="form-group"><label class="form-label">Channel Name <span class="text-danger">*</span></label><input type="text" id="chName" class="form-control" placeholder="Gaming Central" required></div>
                <div class="form-group"><label class="form-label">Channel ID <small class="text-muted">(Optional, e.g. UCxxxx)</small></label><input type="text" id="chId" class="form-control" placeholder="Leave blank to auto-generate"></div>
                <div class="form-group"><label class="form-label">Handle</label><input type="text" id="chHandle" class="form-control" placeholder="@gamingcentral"></div>
                <div class="form-group"><label class="form-label">Description</label><textarea id="chDesc" class="form-control" placeholder="Daily gaming streams and video uploads"></textarea></div>
            </form>
        `;
        const footerHtml = `
            <button class="btn btn-primary" onclick="saveChannelFromModal()"><i class="fas fa-plus"></i> Add Channel</button>
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        `;
        openModal('Add YouTube Channel', bodyHtml, footerHtml);
        loadAccountsForSelect('chAccount');
    });

    // Add Template button
    document.getElementById('addTemplateBtn')?.addEventListener('click', () => {
        const bodyHtml = `
            <form id="addTemplateForm" onsubmit="event.preventDefault(); saveTemplateFromModal();">
                <div class="form-group"><label class="form-label">Channel <span class="text-danger">*</span></label><select id="tmplChannel" class="form-control" required></select></div>
                <div class="form-group"><label class="form-label">Template Name <span class="text-danger">*</span></label><input type="text" id="tmplName" class="form-control" placeholder="Series Upload Preset" required></div>
                <div class="form-group"><label class="form-label">Title Template</label><input type="text" id="tmplTitle" class="form-control" placeholder="{video_title} - Episode {episode}"></div>
                <div class="form-group"><label class="form-label">Description Template</label><textarea id="tmplDesc" class="form-control" placeholder="{video_description}\n\nSubscribe for more!"></textarea></div>
                <div class="form-group"><label class="form-label">Tags (comma separated)</label><input type="text" id="tmplTags" class="form-control" placeholder="gaming, letsplay, walkthrough"></div>
            </form>
        `;
        const footerHtml = `
            <button class="btn btn-primary" onclick="saveTemplateFromModal()"><i class="fas fa-save"></i> Save Template</button>
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        `;
        openModal('Create Template', bodyHtml, footerHtml);
        loadChannelsForSelect('tmplChannel');
    });

    // Bulk upload and YouTube API buttons
    initBatchVideoUpload();
    document.getElementById('bulkUploadForm')?.addEventListener('submit', handleBulkUpload);
    document.getElementById('saveApiKey')?.addEventListener('click', saveYouTubeApiKey);
    document.getElementById('loadMyChannels')?.addEventListener('click', loadYouTubeChannels);
    document.getElementById('searchYouTube')?.addEventListener('click', searchYouTubeVideos);
    initYouTubeApiStatus();
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
            let completed = false;

            const handleCompletion = (result) => {
                if (completed) return;
                completed = true;
                cleanup();
                if (result && result.status === 'success') {
                    showToast(result.message || 'YouTube account connected successfully!', 'success');
                } else {
                    showToast(result?.error || 'Failed to connect YouTube account', 'error');
                }
                try {
                    if (popup && !popup.closed) popup.close();
                } catch (e) {}
                loadAccounts();
            };

            // 1. BroadcastChannel (safe across windows on same origin, immune to COOP)
            let bc = null;
            try {
                bc = new BroadcastChannel('youtube_oauth_channel');
                bc.onmessage = (event) => {
                    if (event.data && event.data.type === 'OAUTH_COMPLETE') {
                        handleCompletion(event.data);
                    }
                };
            } catch (e) {}

            // 2. Storage event listener (fallback across tabs/windows)
            const onStorage = (event) => {
                if (event.key === 'youtube_oauth_status' && event.newValue) {
                    try {
                        const parsed = JSON.parse(event.newValue);
                        localStorage.removeItem('youtube_oauth_status');
                        handleCompletion(parsed);
                    } catch (e) {}
                }
            };
            window.addEventListener('storage', onStorage);

            // 3. postMessage listener
            const onMessage = (event) => {
                if (event.data && event.data.type === 'OAUTH_COMPLETE') {
                    handleCompletion(event.data);
                }
            };
            window.addEventListener('message', onMessage);

            // 4. Safe polling fallback with COOP exception handling
            const checkTimer = setInterval(() => {
                if (completed) {
                    clearInterval(checkTimer);
                    return;
                }
                try {
                    if (popup && popup.closed) {
                        clearInterval(checkTimer);
                        setTimeout(() => {
                            if (!completed) {
                                handleCompletion({ status: 'success', message: 'Updating connected channels...' });
                            }
                        }, 500);
                    }
                } catch (e) {
                    // Suppress Cross-Origin-Opener-Policy browser warning
                }
            }, 1000);

            // Auto-cleanup after 5 minutes
            const cleanupTimer = setTimeout(() => {
                cleanup();
            }, 300000);

            const cleanup = () => {
                clearInterval(checkTimer);
                clearTimeout(cleanupTimer);
                window.removeEventListener('storage', onStorage);
                window.removeEventListener('message', onMessage);
                if (bc) {
                    try { bc.close(); } catch (e) {}
                }
            };
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
            const localAccs = await api.get('/api/channels/accounts');
            if (Array.isArray(localAccs)) accounts = localAccs;
        } catch (e) {
            console.warn('Could not fetch local accounts:', e);
        }

        try {
            const supaAccs = await api.get('/api/supabase/accounts');
            if (Array.isArray(supaAccs) && supaAccs.length > 0) {
                const existingEmails = new Set(accounts.map(a => a.email || a.id));
                supaAccs.forEach(sa => {
                    if (!existingEmails.has(sa.email) && !existingEmails.has(sa.id)) {
                        accounts.push(sa);
                    }
                });
            }
        } catch (e) {
            // Supabase session not active or not authenticated
        }

        const badge = document.getElementById('accountCountBadge');
        if (badge) {
            badge.innerText = `${accounts.length} Account${accounts.length === 1 ? '' : 's'}`;
        }
        renderAccounts(accounts);
        loadChannels(accounts);
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
                <p>Click "Connect with Google" above to link your YouTube channel and unlock upload and analytics features.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = accounts.map(acc => {
        const isOAuth = !!(acc.access_token || (acc.id && String(acc.id).startsWith('oauth-')));
        const safeName = (acc.display_name || 'YouTube Account').replace(/'/g, "\\'");
        const safeId = (acc.id || acc.channel_id || '').replace(/'/g, "\\'");
        const channelId = acc.channel_id || (acc.youtube_channel && acc.youtube_channel.id) || '';

        return `
            <div class="account-card" style="display:flex; flex-direction:column; gap:12px; padding:16px; margin-bottom:12px; border-radius:12px; border:1px solid rgba(255,255,255,0.08); background:var(--bg-card, #161b26);">
                <div style="display:flex; align-items:center; gap:14px; width:100%;">
                    <div class="account-avatar" style="width:48px; height:48px; border-radius:50%; background:linear-gradient(135deg, #ef4444, #dc2626); display:flex; align-items:center; justify-content:center; color:#fff; font-size:22px; flex-shrink:0;">
                        <i class="fab fa-youtube"></i>
                    </div>
                    <div class="account-info" style="flex:1; min-width:0;">
                        <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                            <h4 style="margin:0; font-size:16px; font-weight:600;">${acc.display_name || 'YouTube Account'}</h4>
                            <span class="status-badge ${acc.is_active !== false ? 'status-completed' : 'status-failed'}" style="font-size:11px;">
                                ${acc.is_active !== false ? 'Active' : 'Inactive'}
                            </span>
                            <span class="account-badge ${acc.account_type || 'personal'}" style="font-size:10px;">${(acc.account_type || 'personal').toUpperCase()}</span>
                        </div>
                        <p style="margin:4px 0 0; color:var(--text-muted, #94a3b8); font-size:13px; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">
                            ${acc.email || 'Google Connected Channel'}
                        </p>
                        <div class="engine-track-badges" style="margin-top:6px; display:flex; gap:8px; flex-wrap:wrap;">
                            <span class="track-badge ${isOAuth ? 'track-badge-oauth' : 'track-badge-inactive'}" style="font-size:11px; padding:2px 8px; border-radius:4px; background:rgba(34,197,94,0.15); color:#22c55e;">
                                <i class="fab fa-google"></i> ${isOAuth ? 'Google OAuth: Connected' : 'Google: Offline'}
                            </span>
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <button class="btn btn-sm btn-icon text-danger" onclick="deleteAccount('${safeId}')" title="Disconnect Account" style="background:rgba(239,68,68,0.1); border:none; width:34px; height:34px; border-radius:8px; cursor:pointer;">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>

                <!-- Action Toolbar for Connected Account -->
                <div style="display:flex; gap:8px; flex-wrap:wrap; padding-top:12px; border-top:1px solid rgba(255,255,255,0.06);">
                    <button type="button" class="btn btn-primary btn-sm" onclick="uploadToAccount('${safeId}', '${safeName}')">
                        <i class="fas fa-cloud-upload-alt"></i> Upload Video
                    </button>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="viewChannelStats('${channelId || safeId}', '${safeName}')">
                        <i class="fas fa-chart-line"></i> View Stats & Videos
                    </button>
                    ${channelId ? `
                        <a href="https://www.youtube.com/channel/${channelId}" target="_blank" class="btn btn-secondary btn-sm" style="display:inline-flex; align-items:center; gap:6px; text-decoration:none;">
                            <i class="fab fa-youtube text-danger"></i> Open on YouTube <i class="fas fa-external-link-alt" style="font-size:10px;"></i>
                        </a>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

export function uploadToAccount(channelId, channelName) {
    navigateTo('upload');
    setTimeout(() => {
        const select = document.getElementById('uploadChannelSelect');
        if (select) {
            select.value = channelId;
        }
        showToast(`Target channel selected: ${channelName}`, 'info');
    }, 150);
}
window.uploadToAccount = uploadToAccount;

export async function viewChannelStats(channelId, channelName) {
    openModal(`📊 Channel Intelligence: ${channelName}`, `
        <div style="text-align:center; padding:32px;">
            <i class="fas fa-circle-notch fa-spin fa-2x text-primary"></i>
            <p style="margin-top:12px; color:#94a3b8;">Loading YouTube metrics and recent uploads...</p>
        </div>
    `);

    try {
        let details = null;
        try {
            details = await api.get(`/api/youtube/channels/${encodeURIComponent(channelId)}`);
        } catch {
            const allCh = await api.get('/api/youtube/channels');
            if (Array.isArray(allCh) && allCh.length > 0) {
                details = allCh[0];
            }
        }

        const resolvedId = details?.id || channelId;
        let videos = [];
        try {
            videos = await api.get(`/api/youtube/channels/${encodeURIComponent(resolvedId)}/videos?max_results=6`);
        } catch {}

        const snippet = details?.snippet || {};
        const stats = details?.statistics || {};
        const thumb = snippet?.thumbnails?.medium?.url || snippet?.thumbnails?.default?.url || '';

        const bodyHtml = `
            <div style="display:flex; flex-direction:column; gap:20px;">
                <div style="display:flex; align-items:center; gap:16px; background:rgba(255,255,255,0.03); padding:16px; border-radius:10px;">
                    ${thumb ? `<img src="${thumb}" style="width:60px; height:60px; border-radius:50%; border:2px solid #ef4444; object-fit:cover;">` : '<div style="width:60px; height:60px; border-radius:50%; background:#ef4444; display:flex; align-items:center; justify-content:center; font-size:24px; color:#fff;"><i class="fab fa-youtube"></i></div>'}
                    <div>
                        <h3 style="margin:0 0 4px 0; font-size:18px;">${snippet.title || channelName}</h3>
                        <p style="margin:0; color:#94a3b8; font-size:13px;">${snippet.customUrl || resolvedId}</p>
                    </div>
                </div>

                <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:12px;">
                    <div style="background:rgba(255,255,255,0.04); padding:14px; border-radius:8px; text-align:center;">
                        <div style="font-size:20px; font-weight:700; color:#3b82f6;">${Number(stats.subscriberCount || 0).toLocaleString()}</div>
                        <div style="font-size:12px; color:#94a3b8; margin-top:4px;">Subscribers</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.04); padding:14px; border-radius:8px; text-align:center;">
                        <div style="font-size:20px; font-weight:700; color:#10b981;">${Number(stats.viewCount || 0).toLocaleString()}</div>
                        <div style="font-size:12px; color:#94a3b8; margin-top:4px;">Total Views</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.04); padding:14px; border-radius:8px; text-align:center;">
                        <div style="font-size:20px; font-weight:700; color:#f59e0b;">${Number(stats.videoCount || 0).toLocaleString()}</div>
                        <div style="font-size:12px; color:#94a3b8; margin-top:4px;">Videos</div>
                    </div>
                </div>

                <div>
                    <h4 style="margin:0 0 12px 0; font-size:13px; text-transform:uppercase; letter-spacing:0.5px; color:#94a3b8;">Recent Channel Videos</h4>
                    ${Array.isArray(videos) && videos.length > 0 ? `
                        <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(180px, 1fr)); gap:12px;">
                            ${videos.map(v => {
                                const vTitle = v.snippet?.title || 'Video';
                                const vThumb = v.snippet?.thumbnails?.medium?.url || v.snippet?.thumbnails?.default?.url || '';
                                const vidId = v.id?.videoId || v.id;
                                return `
                                    <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:8px; overflow:hidden;">
                                        ${vThumb ? `<img src="${vThumb}" style="width:100%; aspect-ratio:16/9; object-fit:cover;">` : ''}
                                        <div style="padding:10px;">
                                            <div style="font-size:12px; font-weight:500; line-height:1.3; height:32px; overflow:hidden;" title="${vTitle}">${vTitle}</div>
                                            ${vidId ? `<a href="https://youtu.be/${vidId}" target="_blank" style="font-size:11px; color:#3b82f6; text-decoration:none; margin-top:6px; display:inline-block;"><i class="fab fa-youtube"></i> Watch Video</a>` : ''}
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    ` : '<p style="color:#64748b; font-size:13px;">No recent videos found or YouTube Data API quota reached.</p>'}
                </div>
            </div>
        `;
        const footerHtml = `
            <button type="button" class="btn btn-primary" onclick="closeModal(); uploadToAccount('${channelId}', '${channelName}');">
                <i class="fas fa-cloud-upload-alt"></i> Upload Video to this Channel
            </button>
            <button type="button" class="btn btn-secondary" onclick="closeModal()">Close</button>
        `;
        openModal(`📊 Channel Intelligence: ${channelName}`, bodyHtml, footerHtml);
    } catch (err) {
        openModal(`Channel Details`, `<p class="text-danger">Failed to load channel details: ${err.message}</p>`);
    }
}
window.viewChannelStats = viewChannelStats;

export async function deleteAccount(accountId) {
    if (!confirm('Are you sure you want to disconnect this account?')) return;
    try {
        try {
            await api.delete(`/api/channels/accounts/${accountId}`);
        } catch {
            await api.delete(`/api/supabase/accounts/${accountId}`);
        }
        showToast('Account removed successfully', 'info');
        loadAccounts();
    } catch (err) {
        showToast('Failed to remove account: ' + err.message, 'error');
    }
}
window.deleteAccount = deleteAccount;

export async function addAccount() {
    const email = document.getElementById('accEmail')?.value?.trim() || '';
    const name = document.getElementById('accName')?.value?.trim() || '';
    const type = document.getElementById('accType')?.value || 'personal';

    if (!email || !name) {
        showToast('Please enter both name and email', 'warning');
        return;
    }

    try {
        try {
            await api.post('/api/channels/accounts', { email, display_name: name, account_type: type });
        } catch {
            await api.post('/api/supabase/accounts', { email, display_name: name, account_type: type });
        }
        showToast('Account registered successfully!', 'success');
        closeModal();
        closeAddAccountModal();
        loadAccounts();
    } catch (err) {
        showToast('Failed to add account: ' + err.message, 'error');
    }
}

export function openAddAccountModal() {
    const bodyHtml = `
        <form id="addAccountForm" onsubmit="event.preventDefault(); addAccount();">
            <div class="form-group">
                <label class="form-label">Email Address <span class="text-danger">*</span></label>
                <input type="email" id="accEmail" class="form-control" placeholder="creator@gmail.com" required>
            </div>
            <div class="form-group">
                <label class="form-label">Display Name / Channel Name <span class="text-danger">*</span></label>
                <input type="text" id="accName" class="form-control" placeholder="Gaming Central or Studio Name" required>
            </div>
            <div class="form-group">
                <label class="form-label">Account Type</label>
                <select id="accType" class="form-control">
                    <option value="personal">Personal Channel</option>
                    <option value="brand">Brand Channel</option>
                    <option value="business">Business Account</option>
                </select>
            </div>
        </form>
    `;
    const footerHtml = `
        <button type="button" class="btn btn-primary" onclick="addAccount()"><i class="fas fa-plus"></i> Add Account</button>
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
    `;
    openModal('Register YouTube Account', bodyHtml, footerHtml);
}

export function closeAddAccountModal() {
    closeModal();
    const modal = document.getElementById('addAccountModal');
    if (modal) modal.classList.add('hidden');
}

// ===== Channel Management =====
export async function loadChannels(accounts = []) {
    try {
        let channels = [];
        try {
            const chs = await api.get('/api/channels');
            if (Array.isArray(chs)) channels = chs;
        } catch (e) {
            console.warn('Could not fetch channels:', e);
        }

        renderChannels(channels);
        populateChannelDropdown(channels, accounts);
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
                <p>Connect a YouTube channel with Google OAuth above or click Add Channel.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = channels.map(ch => {
        const safeName = (ch.name || 'YouTube Channel').replace(/'/g, "\\'");
        const safeId = (ch.channel_id || '').replace(/'/g, "\\'");

        return `
            <div class="channel-card" style="display:flex; flex-direction:column; gap:12px; padding:16px; margin-bottom:12px; border-radius:12px; border:1px solid rgba(255,255,255,0.08); background:var(--bg-card, #161b26);">
                <div style="display:flex; align-items:center; gap:14px; width:100%;">
                    <div class="channel-avatar" style="width:48px; height:48px; border-radius:50%; background:linear-gradient(135deg, #ef4444, #b91c1c); display:flex; align-items:center; justify-content:center; color:#fff; font-size:22px; flex-shrink:0;">
                        <i class="fas fa-tv"></i>
                    </div>
                    <div class="channel-info" style="flex:1; min-width:0;">
                        <h4 style="margin:0; font-size:16px; font-weight:600;">${ch.name}</h4>
                        <p style="margin:4px 0 0; color:var(--text-muted, #94a3b8); font-size:13px; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">
                            ${ch.handle || ch.channel_id} ${ch.description ? '• ' + ch.description.substring(0, 50) + '...' : ''}
                        </p>
                    </div>
                    <div class="channel-meta" style="display:flex; gap:16px;">
                        <div class="channel-meta-item" style="text-align:right;"><div class="number" style="font-weight:700; font-size:15px; color:#3b82f6;">${(ch.subscriber_count || 0).toLocaleString()}</div><div class="label" style="font-size:11px; color:#94a3b8;">Subscribers</div></div>
                        <div class="channel-meta-item" style="text-align:right;"><div class="number" style="font-weight:700; font-size:15px; color:#10b981;">${(ch.video_count || 0).toLocaleString()}</div><div class="label" style="font-size:11px; color:#94a3b8;">Videos</div></div>
                    </div>
                    <button class="btn btn-sm btn-icon text-danger" onclick="deleteChannel('${safeId}')" title="Delete Channel" style="background:rgba(239,68,68,0.1); border:none; width:34px; height:34px; border-radius:8px; cursor:pointer;">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>

                <div style="display:flex; gap:8px; flex-wrap:wrap; padding-top:12px; border-top:1px solid rgba(255,255,255,0.06);">
                    <button type="button" class="btn btn-primary btn-sm" onclick="uploadToAccount('${safeId}', '${safeName}')">
                        <i class="fas fa-cloud-upload-alt"></i> Upload Video
                    </button>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="viewChannelStats('${safeId}', '${safeName}')">
                        <i class="fas fa-chart-line"></i> View Stats & Videos
                    </button>
                    <a href="https://www.youtube.com/${ch.handle ? ch.handle : 'channel/' + ch.channel_id}" target="_blank" class="btn btn-secondary btn-sm" style="display:inline-flex; align-items:center; gap:6px; text-decoration:none;">
                        <i class="fab fa-youtube text-danger"></i> YouTube <i class="fas fa-external-link-alt" style="font-size:10px;"></i>
                    </a>
                </div>
            </div>
        `;
    }).join('');
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
    const customId = document.getElementById('chId')?.value?.trim();
    const handle = document.getElementById('chHandle')?.value?.trim();
    const desc = document.getElementById('chDesc')?.value?.trim();

    if (!name) {
        showToast('Channel name is required', 'warning');
        return;
    }

    const channelId = customId || name.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-');

    try {
        await api.post('/api/channels', {
            account_id: accountId,
            channel_id: channelId,
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
let selectedBatchFiles = [];

export function initBatchVideoUpload() {
    const addBtn = document.getElementById('addBatchVideos');
    if (!addBtn) return;

    let hiddenInput = document.getElementById('batchFileInput');
    if (!hiddenInput) {
        hiddenInput = document.createElement('input');
        hiddenInput.type = 'file';
        hiddenInput.id = 'batchFileInput';
        hiddenInput.multiple = true;
        hiddenInput.accept = 'video/*';
        hiddenInput.style.display = 'none';
        document.body.appendChild(hiddenInput);

        hiddenInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            files.forEach(f => {
                if (!selectedBatchFiles.some(bf => bf.name === f.name && bf.size === f.size)) {
                    selectedBatchFiles.push(f);
                }
            });
            renderBatchVideoList();
        });
    }

    addBtn.onclick = () => hiddenInput.click();
}

export function renderBatchVideoList() {
    const listEl = document.getElementById('batchVideoList');
    if (!listEl) return;
    if (selectedBatchFiles.length === 0) {
        listEl.innerHTML = '<p class="text-muted">No files added yet</p>';
        return;
    }
    listEl.innerHTML = selectedBatchFiles.map((f, idx) => `
        <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.04); padding:8px 12px; margin-bottom:6px; border-radius:6px; font-size:13px;">
            <span><i class="fas fa-file-video text-primary"></i> <b>${f.name}</b> <small class="text-muted">(${(f.size / (1024*1024)).toFixed(1)} MB)</small></span>
            <button type="button" class="btn btn-sm text-danger" style="background:none; border:none; cursor:pointer;" onclick="removeBatchFile(${idx})">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');
}

export function removeBatchFile(index) {
    selectedBatchFiles.splice(index, 1);
    renderBatchVideoList();
}
window.removeBatchFile = removeBatchFile;

export async function loadBatches() {
    try {
        const batches = await api.get('/api/batches');
        renderBatches(batches);
        loadBatchChannels();
        loadBatchTemplates();
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
            <div class="batch-card" style="margin-bottom:12px; padding:16px; border-radius:10px; background:var(--bg-card,#161b26); border:1px solid rgba(255,255,255,0.06);">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <h4 style="margin:0;">${b.name}</h4>
                    <span class="status-badge status-${b.status}">${b.status}</span>
                </div>
                <div class="batch-progress" style="margin:10px 0;"><div class="batch-progress-bar" style="width: ${percent}%;"></div></div>
                <p class="text-muted" style="margin:0; font-size:12px;">${b.uploaded_count || 0}/${b.total_videos || 0} videos uploaded • ${b.failed_count || 0} failed</p>
            </div>
        `;
    }).join('');
}

export async function loadBatchChannels() {
    try {
        const channels = await api.get('/api/channels');
        const select = document.getElementById('batchChannel');
        if (select && Array.isArray(channels)) {
            select.innerHTML = '<option value="">Select target channel</option>' +
                channels.map(c => `<option value="${c.channel_id}">📺 ${c.name} (${c.handle || c.channel_id})</option>`).join('');
        }
    } catch (err) {
        console.error('Failed to load channels for batch:', err);
    }
}

export async function loadBatchTemplates() {
    try {
        const templates = await api.get('/api/templates');
        const select = document.getElementById('batchTemplate');
        if (select && Array.isArray(templates)) {
            select.innerHTML = '<option value="">No template</option>' +
                templates.map(t => `<option value="${t.template_id}">${t.name}</option>`).join('');
        }
    } catch (err) {
        console.error('Failed to load templates for batch:', err);
    }
}

export async function handleBulkUpload(e) {
    e.preventDefault();
    const name = document.getElementById('batchName')?.value?.trim();
    const channelId = document.getElementById('batchChannel')?.value;
    const templateId = document.getElementById('batchTemplate')?.value || null;
    const priority = document.getElementById('batchPriority')?.value || 'normal';

    if (!name || !channelId) {
        showToast('Batch name and target channel are required', 'warning');
        return;
    }

    if (selectedBatchFiles.length === 0) {
        showToast('Please click "Add Videos to Batch" and choose at least one video file', 'warning');
        return;
    }

    try {
        showToast(`Queueing batch "${name}" (${selectedBatchFiles.length} videos)...`, 'info');

        for (const file of selectedBatchFiles) {
            const formData = new FormData();
            formData.append('video', file);
            formData.append('channel_id', channelId);
            formData.append('priority', priority);
            if (templateId) formData.append('template_id', templateId);
            formData.append('metadata', JSON.stringify({ batch_name: name }));
            await api.post('/api/jobs', formData);
        }

        showToast(`🚀 Successfully queued batch "${name}" with ${selectedBatchFiles.length} videos!`, 'success');
        selectedBatchFiles = [];
        renderBatchVideoList();
        document.getElementById('bulkUploadForm')?.reset();
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
            select.innerHTML = accounts.map(a => {
                const id = a.account_id || a.id;
                return `<option value="${id}">${a.display_name} (${a.email || 'Account'})</option>`;
            }).join('');
        }
    } catch (err) {
        console.error(`Failed to load accounts for ${selectId}:`, err);
    }
}

export async function loadChannelsForSelect(selectId) {
    try {
        const channels = await api.get('/api/channels');
        const select = document.getElementById(selectId);
        if (select && Array.isArray(channels)) {
            select.innerHTML = '<option value="">Select Channel</option>' +
                channels.map(c => `<option value="${c.channel_id}">${c.name} (${c.handle || c.channel_id})</option>`).join('');
        }
    } catch (err) {
        console.error(`Failed to load channels for ${selectId}:`, err);
    }
}

export async function initYouTubeApiStatus() {
    try {
        const status = await api.get('/api/youtube/auth');
        const input = document.getElementById('apiKeyInput');
        if (status && status.configured && input) {
            input.placeholder = `Configured (${status.api_key_masked || 'Active'})`;
        }
    } catch {}
}

// Global window bindings for inline onclick attributes and modals
Object.assign(window, {
    uploadToAccount,
    viewChannelStats,
    deleteAccount,
    addAccount,
    openAddAccountModal,
    closeAddAccountModal,
    deleteChannel,
    saveChannelFromModal,
    deleteTemplate,
    saveTemplateFromModal,
    removeBatchFile,
    openConfigOAuthModal,
    saveOAuthCredentialsFromModal,
    connectGoogle,
    copyLoginCommand,
    copyRedirectUri,
    openBrowserLoginModal,
    loadAccounts,
    loadChannels,
    loadTemplates,
    loadBatches
});

export { saveYouTubeApiKey, loadYouTubeChannels, searchYouTubeVideos };
