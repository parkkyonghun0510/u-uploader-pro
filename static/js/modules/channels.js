/**
 * YouTube Uploader Pro - Multi-Channel, OAuth & Studio Asset Hub
 * Manages Google OAuth, Supabase Channel accounts, upload templates, batching, and YouTube Data API v3.
 */

import { api } from './api.js';
import { API_BASE } from './constants.js';
import { state } from './state.js';
import { navigateTo } from './navigation.js';
import { populateChannelDropdown } from './upload.js';
import {
    showToast,
    openModal,
    closeModal
} from './ui.js';
export function initChannelTabs() {
    document.querySelectorAll('#channelTabs .tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('#channelTabs .tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const tabName = tab.dataset.tab;
            document.querySelectorAll('#accountsTab, #channelsTab, #templatesTab, #bulkTab').forEach(s => s.classList.add('hidden'));

            const target = document.getElementById(tabName + 'Tab');
            if (target) target.classList.remove('hidden');

            if (tabName === 'accounts') loadAccounts();
            if (tabName === 'channels') loadChannels();
            if (tabName === 'templates') loadTemplates();
            if (tabName === 'bulk') loadBatches();
        });
    });

    // Add Channel & Template buttons
    document.getElementById('addChannelBtn')?.addEventListener('click', openAddChannelModal);
    document.getElementById('addTemplateBtn')?.addEventListener('click', openAddTemplateModal);

    // Bulk upload pipelines
    initBatchVideoUpload();
    document.getElementById('bulkUploadForm')?.addEventListener('submit', handleBulkUpload);
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
        const userId = state.currentUser?.id || null;
        const data = await api.post('/api/oauth/google', {
            redirect_uri: redirectUri,
            user_id: userId
        });
        if (data.auth_url) {
            const popup = window.open(data.auth_url, 'Google OAuth', 'width=620,height=720');
            showToast('Google OAuth opened. Please authorize access in popup.', 'info');
            let completed = false;

            const handleCompletion = async (result) => {
                if (completed) return;
                completed = true;
                cleanup();

                if (result && result.status === 'success') {
                    showToast(result.message || 'YouTube account connected! Syncing YouTube Studio...', 'success');
                    try {
                        await syncStudioData();
                    } catch (e) {
                        console.warn('Auto studio sync warning:', e);
                        await loadAccounts();
                        await loadChannels();
                    }
                } else {
                    showToast(result?.error || 'Failed to connect YouTube account', 'error');
                    await loadAccounts();
                    await loadChannels();
                }
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

            // 2. Storage event listener (fallback across tabs/windows, immune to COOP)
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

            // Auto-cleanup after 5 minutes
            const cleanupTimer = setTimeout(() => {
                cleanup();
            }, 300000);

            const cleanup = () => {
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

// ===== Studio Sync Engine =====
export async function syncStudioData(accountId = null, channelId = null) {
    const syncBtns = document.querySelectorAll('#syncAccountsBtn, #syncChannelsBtn');
    syncBtns.forEach(b => {
        b.disabled = true;
        b.dataset.prevHtml = b.innerHTML;
        b.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing Studio...';
    });
    showToast('Fetching latest channels & YouTube Studio metrics...', 'info');

    try {
        const payload = {};
        if (accountId) payload.account_id = accountId;
        if (channelId) payload.channel_id = channelId;

        const res = await api.post('/api/youtube/sync-studio', payload);
        if (res.status === 'success' || res.success) {
            showToast(res.message || 'YouTube Studio sync complete!', 'success');
        } else {
            showToast(res.error || 'Studio sync finished with warnings', 'warning');
        }
    } catch (err) {
        showToast('Sync failed: ' + (err.message || 'Network error'), 'error');
    } finally {
        syncBtns.forEach(b => {
            b.disabled = false;
            if (b.dataset.prevHtml) b.innerHTML = b.dataset.prevHtml;
        });
        await loadAccounts();
        await loadChannels();
    }
}

export async function syncChannelStudio(channelId) {
    if (!channelId) return;
    showToast(`Syncing YouTube Studio for ${channelId}...`, 'info');
    try {
        const isAccount = channelId.startsWith('oauth-') || channelId.includes('@');
        const endpoint = isAccount
            ? `/api/channels/accounts/${encodeURIComponent(channelId)}/sync`
            : `/api/channels/${encodeURIComponent(channelId)}/sync`;
        const res = await api.post(endpoint);
        if (res.status === 'success' || res.success) {
            showToast(res.message || 'Sync completed successfully!', 'success');
            await loadAccounts();
            await loadChannels();
        } else {
            showToast(res.error || 'Sync completed with warnings', 'warning');
        }
    } catch (err) {
        showToast('Sync failed: ' + err.message, 'error');
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
                const existingEmails = new Set(accounts.map(a => a.email).filter(Boolean));
                const existingIds = new Set(accounts.map(a => a.account_id || a.id).filter(Boolean));
                supaAccs.forEach(sa => {
                    const aid = sa.id || sa.account_id;
                    if ((!sa.email || !existingEmails.has(sa.email)) && (!aid || !existingIds.has(aid))) {
                        accounts.push({
                            ...sa,
                            account_id: aid,
                            access_token: sa.google_access_token || sa.access_token,
                            refresh_token: sa.google_refresh_token || sa.refresh_token,
                            google_profile_image: sa.google_profile_image || sa.avatar_url
                        });
                        if (sa.email) existingEmails.add(sa.email);
                        if (aid) existingIds.add(aid);
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
                <div style="margin-top:16px;">
                    <button type="button" class="btn btn-primary btn-sm" onclick="connectGoogle()">
                        <i class="fab fa-google"></i> Connect with Google Now
                    </button>
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = accounts.map(acc => {
        const isOAuth = !!(acc.access_token || acc.google_access_token || (acc.id && String(acc.id).startsWith('oauth-')) || (acc.account_id && String(acc.account_id).startsWith('oauth-')));
        const safeName = (acc.display_name || 'YouTube Account').replace(/'/g, "\\'");
        const safeId = (acc.id || acc.account_id || acc.channel_id || '').replace(/'/g, "\\'");
        const channelId = acc.channel_id || (acc.youtube_channel && acc.youtube_channel.id) || (Array.isArray(acc.channels) && acc.channels[0]) || '';
        const profileImg = acc.google_profile_image || (acc.youtube_channel?.snippet?.thumbnails?.default?.url) || acc.thumbnail_url || '';
        const isRealChannel = channelId && String(channelId).startsWith('UC');
        const authParam = acc.email ? `?authuser=${encodeURIComponent(acc.email)}` : '';
        const studioHref = isRealChannel ? `https://studio.youtube.com/channel/${channelId}${authParam}` : `https://studio.youtube.com/${authParam}`;

        return `
            <div class="account-card">
                <div class="card-top-row">
                    <div class="account-avatar">
                        ${profileImg ? `<img src="${profileImg}" class="card-avatar-img" alt="${safeName}">` : `<i class="fab fa-youtube"></i>`}
                    </div>
                    <div class="account-info">
                        <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                            <h4>${acc.display_name || 'YouTube Account'}</h4>
                            <span class="status-badge ${acc.is_active !== false ? 'status-completed' : 'status-failed'}">
                                ${acc.is_active !== false ? 'Active' : 'Inactive'}
                            </span>
                            <span class="account-badge ${acc.account_type || 'personal'}">${(acc.account_type || 'personal').toUpperCase()}</span>
                        </div>
                        <p>${acc.email || 'Google Connected Channel'}</p>
                        <div class="engine-track-badges" style="margin-top:6px; display:flex; gap:8px; flex-wrap:wrap;">
                            <span class="track-badge ${isOAuth ? 'track-badge-oauth' : 'track-badge-inactive'}">
                                <i class="fab fa-google"></i> ${isOAuth ? 'Google OAuth: Active' : 'Offline'}
                            </span>
                        </div>
                    </div>
                    <button class="btn btn-sm btn-icon text-danger" onclick="deleteAccount('${safeId}')" title="Disconnect Account" style="background:rgba(239,68,68,0.1); border:none; width:34px; height:34px; border-radius:8px; cursor:pointer;">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>

                <!-- Action Toolbar for Connected Account -->
                <div class="card-actions-bar">
                    <button type="button" class="btn btn-primary btn-sm" onclick="uploadToAccount('${channelId || safeId}', '${safeName}')">
                        <i class="fas fa-cloud-upload-alt"></i> Upload Video
                    </button>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="syncStudioData('${safeId}')" title="Sync Channel & YouTube Studio Data">
                        <i class="fas fa-sync-alt text-primary"></i> Sync Studio
                    </button>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="viewChannelStats('${channelId || safeId}', '${safeName}')">
                        <i class="fas fa-chart-line"></i> Intelligence
                    </button>
                    <a href="${studioHref}" target="_blank" class="btn btn-secondary btn-sm" style="display:inline-flex; align-items:center; gap:6px; text-decoration:none;" title="Open YouTube Studio">
                        <i class="fab fa-youtube text-danger"></i> Studio <i class="fas fa-external-link-alt" style="font-size:10px;"></i>
                    </a>
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
    openModal(`📊 YouTube Studio: ${channelName || channelId}`, `
        <div style="text-align:center; padding:36px;">
            <i class="fas fa-circle-notch fa-spin fa-2x text-primary"></i>
            <p style="margin-top:12px; color:#94a3b8; font-size:14px;">Loading YouTube Studio dashboard & intelligence...</p>
        </div>
    `);

    try {
        let data = null;
        try {
            data = await api.get(`/api/channels/${encodeURIComponent(channelId)}/studio`);
        } catch {
            data = await api.get(`/api/youtube/studio/${encodeURIComponent(channelId)}`);
        }

        const ch = data?.channel || {};
        const kpis = data?.kpis || {};
        const recentVideos = Array.isArray(data?.recent_videos) ? data.recent_videos : [];
        const isRealCid = (ch.id || channelId || '').startsWith('UC');
        const accEmail = ch.email || data?.account_email || '';
        const authParam = accEmail ? `?authuser=${encodeURIComponent(accEmail)}` : '';
        const baseStudio = isRealCid ? `https://studio.youtube.com/channel/${ch.id || channelId}` : 'https://studio.youtube.com';
        const links = data?.studio_links || {
            dashboard: `${baseStudio}${authParam}`,
            videos: `${baseStudio}/videos/upload${authParam}`,
            analytics: `${baseStudio}/analytics/tab-overview${authParam}`,
            customization: `${baseStudio}/editing/sections${authParam}`,
            channel_switcher: `https://www.youtube.com/channel_switcher`,
            account_chooser: `https://accounts.google.com/AccountChooser?service=youtube&continue=${encodeURIComponent(baseStudio)}`
        };

        const title = ch.title || channelName || 'YouTube Channel';
        const handle = ch.handle || ch.custom_url || ch.id || channelId;
        const bannerUrl = ch.banner_url || '';
        const thumbUrl = ch.thumbnail_url || '';
        const subs = Number(kpis.subscribers || ch.subscribers || 0);
        const views = Number(kpis.views || ch.views || 0);
        const vids = Number(kpis.videos || ch.videos || 0);
        const avgViews = Number(kpis.avg_views_per_video || (vids > 0 ? Math.round(views / vids) : 0));
        const lastSync = ch.last_sync ? new Date(ch.last_sync).toLocaleString() : 'Just now';

        const bodyHtml = `
            <div style="display:flex; flex-direction:column; gap:18px;">
                <!-- Channel Header with optional Banner -->
                <div style="position:relative; border-radius:12px; overflow:hidden; border:1px solid rgba(255,255,255,0.08); background:var(--bg-card, #161b26);">
                    ${bannerUrl ? `
                        <div style="width:100%; height:110px; background:url('${bannerUrl}') center/cover no-repeat; position:relative;">
                            <div style="position:absolute; inset:0; background:linear-gradient(to bottom, transparent 40%, rgba(15,19,29,0.95) 100%);"></div>
                        </div>
                    ` : `
                        <div style="width:100%; height:70px; background:linear-gradient(135deg, #1e293b 0%, #0f172a 100%); position:relative;">
                            <div style="position:absolute; inset:0; background:radial-gradient(circle at top right, rgba(59,130,246,0.15), transparent 70%);"></div>
                        </div>
                    `}
                    <div style="padding:14px 18px; display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:12px; margin-top:${bannerUrl ? '-35px' : '-20px'}; position:relative;">
                        <div style="display:flex; align-items:center; gap:14px;">
                            ${thumbUrl ? `
                                <img src="${thumbUrl}" style="width:68px; height:68px; border-radius:50%; border:3px solid #0f172a; box-shadow:0 4px 14px rgba(0,0,0,0.4); object-fit:cover; background:#1e293b;">
                            ` : `
                                <div style="width:68px; height:68px; border-radius:50%; border:3px solid #0f172a; background:linear-gradient(135deg, #ef4444 0%, #dc2626 100%); display:flex; align-items:center; justify-content:center; color:#fff; font-size:26px; box-shadow:0 4px 14px rgba(239,68,68,0.3);">
                                    <i class="fab fa-youtube"></i>
                                </div>
                            `}
                            <div>
                                <h3 style="margin:0 0 4px 0; font-size:1.15rem; font-weight:700; color:var(--text-primary); display:flex; align-items:center; gap:8px;">
                                    ${title}
                                    <span style="font-size:11px; padding:2px 7px; border-radius:6px; background:rgba(16,185,129,0.15); color:#34d399; font-weight:500;">
                                        <i class="fas fa-check-circle"></i> Connected
                                    </span>
                                </h3>
                                <p style="margin:0; font-size:12px; color:var(--text-muted); font-family:monospace;">
                                    ${handle} • Synced: ${lastSync}
                                </p>
                            </div>
                        </div>
                        <div style="display:flex; gap:8px;">
                            <a href="${links.dashboard}" target="_blank" class="btn btn-sm btn-secondary" style="display:inline-flex; align-items:center; gap:6px; text-decoration:none;">
                                <i class="fab fa-youtube text-danger"></i> Studio Dashboard <i class="fas fa-external-link-alt" style="font-size:10px;"></i>
                            </a>
                        </div>
                    </div>
                </div>

                <!-- Account / Permission Guidance Banner -->
                <div style="background:rgba(59,130,246,0.08); border:1px solid rgba(59,130,246,0.22); border-radius:10px; padding:12px 16px; font-size:12px; line-height:1.45; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div style="display:flex; align-items:flex-start; gap:10px; color:#cbd5e1; max-width:540px;">
                        <i class="fas fa-shield-alt text-primary" style="margin-top:2px; font-size:15px; flex-shrink:0;"></i>
                        <div>
                            <strong style="color:#60a5fa;">Seeing "Oops, you don't have permission"?</strong><br>
                            Your browser opened YouTube under a different Google account or Brand profile. Switch your YouTube channel or choose the matching Google account below.
                        </div>
                    </div>
                    <div style="display:flex; gap:6px; flex-wrap:wrap;">
                        <a href="${links.channel_switcher || 'https://www.youtube.com/channel_switcher'}" target="_blank" class="btn btn-secondary btn-sm" style="font-size:11px; padding:4px 10px; text-decoration:none; display:inline-flex; align-items:center; gap:5px;" title="Switch YouTube Channel / Brand Account">
                            <i class="fas fa-random text-warning"></i> Switch Channel
                        </a>
                        <a href="${links.account_chooser || `https://accounts.google.com/AccountChooser?service=youtube&continue=${encodeURIComponent(links.dashboard)}`}" target="_blank" class="btn btn-secondary btn-sm" style="font-size:11px; padding:4px 10px; text-decoration:none; display:inline-flex; align-items:center; gap:5px;" title="Choose Google Account">
                            <i class="fas fa-user-circle text-info"></i> Switch Account
                        </a>
                    </div>
                </div>

                <!-- YouTube Studio Quick Access Links Bar -->
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:8px;">
                    <a href="${links.dashboard}" target="_blank" style="text-decoration:none; padding:8px 12px; border-radius:8px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); color:var(--text-secondary); font-size:12px; display:flex; align-items:center; justify-content:space-between; transition:all 0.2s;">
                        <span><i class="fas fa-tachometer-alt text-primary" style="margin-right:6px;"></i> Dashboard</span>
                        <i class="fas fa-external-link-alt" style="font-size:9px; color:var(--text-muted);"></i>
                    </a>
                    <a href="${links.videos}" target="_blank" style="text-decoration:none; padding:8px 12px; border-radius:8px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); color:var(--text-secondary); font-size:12px; display:flex; align-items:center; justify-content:space-between; transition:all 0.2s;">
                        <span><i class="fas fa-video text-success" style="margin-right:6px;"></i> Content</span>
                        <i class="fas fa-external-link-alt" style="font-size:9px; color:var(--text-muted);"></i>
                    </a>
                    <a href="${links.analytics}" target="_blank" style="text-decoration:none; padding:8px 12px; border-radius:8px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); color:var(--text-secondary); font-size:12px; display:flex; align-items:center; justify-content:space-between; transition:all 0.2s;">
                        <span><i class="fas fa-chart-pie text-warning" style="margin-right:6px;"></i> Analytics</span>
                        <i class="fas fa-external-link-alt" style="font-size:9px; color:var(--text-muted);"></i>
                    </a>
                    <a href="${links.customization}" target="_blank" style="text-decoration:none; padding:8px 12px; border-radius:8px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); color:var(--text-secondary); font-size:12px; display:flex; align-items:center; justify-content:space-between; transition:all 0.2s;">
                        <span><i class="fas fa-paint-brush" style="color:#a855f7; margin-right:6px;"></i> Customization</span>
                        <i class="fas fa-external-link-alt" style="font-size:9px; color:var(--text-muted);"></i>
                    </a>
                </div>

                <!-- KPI Metric Cards -->
                <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:10px;">
                    <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); padding:14px; border-radius:10px; text-align:center;">
                        <div style="font-size:20px; font-weight:800; color:#60a5fa;">${subs.toLocaleString()}</div>
                        <div style="font-size:11px; text-transform:uppercase; color:var(--text-muted); margin-top:4px; letter-spacing:0.04em;">Subscribers</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); padding:14px; border-radius:10px; text-align:center;">
                        <div style="font-size:20px; font-weight:800; color:#34d399;">${views.toLocaleString()}</div>
                        <div style="font-size:11px; text-transform:uppercase; color:var(--text-muted); margin-top:4px; letter-spacing:0.04em;">Total Views</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); padding:14px; border-radius:10px; text-align:center;">
                        <div style="font-size:20px; font-weight:800; color:#f59e0b;">${vids.toLocaleString()}</div>
                        <div style="font-size:11px; text-transform:uppercase; color:var(--text-muted); margin-top:4px; letter-spacing:0.04em;">Videos</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); padding:14px; border-radius:10px; text-align:center;">
                        <div style="font-size:20px; font-weight:800; color:#a78bfa;">${avgViews.toLocaleString()}</div>
                        <div style="font-size:11px; text-transform:uppercase; color:var(--text-muted); margin-top:4px; letter-spacing:0.04em;">Avg Views/Video</div>
                    </div>
                </div>

                <!-- Recent Uploads Section -->
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <h4 style="margin:0; font-size:13px; text-transform:uppercase; letter-spacing:0.5px; color:var(--text-muted);">
                            <i class="fas fa-play-circle text-primary" style="margin-right:6px;"></i> Latest Uploads & Performance
                        </h4>
                        <span style="font-size:12px; color:var(--text-muted);">${recentVideos.length} videos fetched</span>
                    </div>

                    ${recentVideos.length > 0 ? `
                        <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr)); gap:12px; max-height:360px; overflow-y:auto; padding-right:4px;">
                            ${recentVideos.map(v => {
                                const vTitle = v.title || 'Untitled Video';
                                const vThumb = v.thumbnail || '';
                                const vViews = Number(v.views || 0).toLocaleString();
                                const vLikes = Number(v.likes || 0).toLocaleString();
                                const vComments = Number(v.comments || 0).toLocaleString();
                                const vPrivacy = v.privacy_status || 'public';
                                const vPub = v.published_at ? new Date(v.published_at).toLocaleDateString() : '';
                                const privacyColor = vPrivacy === 'public' ? '#10b981' : (vPrivacy === 'unlisted' ? '#f59e0b' : '#6b7280');

                                return `
                                    <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:10px; overflow:hidden; display:flex; flex-direction:column; justify-content:space-between;">
                                        <div>
                                            <div style="position:relative; width:100%; aspect-ratio:16/9; background:#0f172a; overflow:hidden;">
                                                ${vThumb ? `<img src="${vThumb}" style="width:100%; height:100%; object-fit:cover;">` : '<div style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; color:#475569;"><i class="fas fa-video fa-2x"></i></div>'}
                                                <span style="position:absolute; bottom:6px; right:6px; background:rgba(0,0,0,0.8); color:#fff; font-size:10px; padding:2px 6px; border-radius:4px; font-weight:600;">
                                                    ${v.duration || 'VIDEO'}
                                                </span>
                                                <span style="position:absolute; top:6px; left:6px; background:${privacyColor}; color:#fff; font-size:10px; padding:2px 6px; border-radius:4px; font-weight:600; text-transform:uppercase;">
                                                    ${vPrivacy}
                                                </span>
                                            </div>
                                            <div style="padding:10px 12px;">
                                                <div style="font-size:13px; font-weight:600; line-height:1.35; height:36px; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;" title="${vTitle}">
                                                    ${vTitle}
                                                </div>
                                                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px; font-size:11px; color:var(--text-muted);">
                                                    <span><i class="fas fa-eye"></i> ${vViews}</span>
                                                    <span><i class="fas fa-thumbs-up"></i> ${vLikes}</span>
                                                    <span><i class="fas fa-comment"></i> ${vComments}</span>
                                                    <span>${vPub}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div style="padding:8px 12px; border-top:1px solid rgba(255,255,255,0.05); display:flex; justify-content:space-between; align-items:center; font-size:11px; background:rgba(255,255,255,0.01);">
                                            <a href="${v.studio_edit_url || `https://studio.youtube.com/video/${v.id}/edit`}" target="_blank" style="color:#60a5fa; text-decoration:none; display:inline-flex; align-items:center; gap:4px;">
                                                <i class="fas fa-sliders-h"></i> Studio Edit
                                            </a>
                                            <a href="${v.youtube_watch_url || `https://youtu.be/${v.id}`}" target="_blank" style="color:#ef4444; text-decoration:none; display:inline-flex; align-items:center; gap:4px;">
                                                <i class="fab fa-youtube"></i> Watch
                                            </a>
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    ` : `
                        <div style="text-align:center; padding:24px; background:rgba(255,255,255,0.02); border-radius:8px; border:1px dashed rgba(255,255,255,0.08);">
                            <i class="fas fa-inbox fa-2x" style="color:var(--text-muted); margin-bottom:8px;"></i>
                            <p style="margin:0; font-size:13px; color:var(--text-muted);">No videos published yet, or sync is in progress.</p>
                        </div>
                    `}
                </div>
            </div>
        `;

        const footerHtml = `
            <button type="button" class="btn btn-primary" onclick="closeModal(); uploadToAccount('${ch.id || channelId}', '${title.replace(/'/g, "\\'")}');">
                <i class="fas fa-cloud-upload-alt"></i> Upload Video to Channel
            </button>
            <button type="button" class="btn btn-secondary" onclick="syncChannelStudio('${ch.id || channelId}')">
                <i class="fas fa-sync-alt"></i> Sync Channel Now
            </button>
            <button type="button" class="btn btn-secondary" onclick="closeModal()">Close</button>
        `;

        openModal(`📊 YouTube Studio: ${title}`, bodyHtml, footerHtml);
    } catch (err) {
        openModal(`Channel Details`, `<p class="text-danger">Failed to load YouTube Studio data: ${err.message}</p>`);
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
                <div class="empty-icon-ring"><i class="fas fa-tv"></i></div>
                <h3>No channels configured</h3>
                <p>Connect a YouTube channel with Google OAuth above or click Add Channel.</p>
                <div style="margin-top:16px;">
                    <button type="button" class="btn btn-primary btn-sm" onclick="openAddChannelModal()">
                        <i class="fas fa-plus"></i> Add Channel
                    </button>
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = channels.map(ch => {
        const safeName = (ch.name || 'YouTube Channel').replace(/'/g, "\\'");
        const safeId = (ch.channel_id || '').replace(/'/g, "\\'");
        const subs = ch.subscriber_count || 0;
        const vids = ch.video_count || 0;
        const views = ch.view_count || 0;
        const thumb = ch.thumbnail_url || '';
        const isRealCid = ch.channel_id && String(ch.channel_id).startsWith('UC');
        const authParam = ch.account_email ? `?authuser=${encodeURIComponent(ch.account_email)}` : '';
        const chStudioHref = isRealCid ? `https://studio.youtube.com/channel/${ch.channel_id}${authParam}` : `https://studio.youtube.com/${authParam}`;

        return `
            <div class="channel-card">
                <div class="card-top-row">
                    <div class="channel-avatar">
                        ${thumb ? `<img src="${thumb}" class="card-avatar-img" alt="${safeName}">` : `<i class="fas fa-tv"></i>`}
                    </div>
                    <div class="channel-info">
                        <h4>${ch.name}</h4>
                        <p>${ch.handle || ch.channel_id} ${ch.description ? '• ' + ch.description.substring(0, 45) + '...' : ''}</p>
                    </div>
                    <button class="btn btn-sm btn-icon text-danger" onclick="deleteChannel('${safeId}')" title="Delete Channel" style="background:rgba(239,68,68,0.1); border:none; width:34px; height:34px; border-radius:8px; cursor:pointer;">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>

                <div class="card-metrics-grid">
                    <div class="card-metric-item">
                        <span class="card-metric-val" style="color:#60a5fa;">${subs.toLocaleString()}</span>
                        <span class="card-metric-lbl">Subscribers</span>
                    </div>
                    <div class="card-metric-item">
                        <span class="card-metric-val" style="color:#34d399;">${vids.toLocaleString()}</span>
                        <span class="card-metric-lbl">Videos</span>
                    </div>
                    <div class="card-metric-item">
                        <span class="card-metric-val" style="color:#a78bfa;">${views.toLocaleString()}</span>
                        <span class="card-metric-lbl">Views</span>
                    </div>
                </div>

                <div class="card-actions-bar">
                    <button type="button" class="btn btn-primary btn-sm" onclick="uploadToAccount('${safeId}', '${safeName}')">
                        <i class="fas fa-cloud-upload-alt"></i> Upload Video
                    </button>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="viewChannelStats('${safeId}', '${safeName}')">
                        <i class="fas fa-chart-line text-primary"></i> Studio Hub
                    </button>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="syncChannelStudio('${safeId}')" title="Sync YouTube Studio Metrics">
                        <i class="fas fa-sync-alt"></i> Sync
                    </button>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="openEditChannelModal('${safeId}')" title="Edit Channel Details">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <a href="${chStudioHref}" target="_blank" class="btn btn-secondary btn-sm" style="display:inline-flex; align-items:center; gap:5px; text-decoration:none;" title="Open in YouTube Studio">
                        <i class="fab fa-youtube text-danger"></i> Studio <i class="fas fa-external-link-alt" style="font-size:10px;"></i>
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

export function openAddChannelModal() {
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

export async function openEditChannelModal(channelId) {
    try {
        const ch = await api.get(`/api/channels/${encodeURIComponent(channelId)}`);
        const bodyHtml = `
            <form id="editChannelForm" onsubmit="event.preventDefault(); saveEditChannelFromModal('${encodeURIComponent(channelId)}');">
                <div class="form-group">
                    <label class="form-label">Channel ID</label>
                    <input type="text" class="form-control" value="${ch.channel_id || channelId}" readonly style="background:rgba(255,255,255,0.03); color:var(--text-muted); font-family:monospace;">
                </div>
                <div class="form-group">
                    <label class="form-label">Channel Name <span class="text-danger">*</span></label>
                    <input type="text" id="editChName" class="form-control" value="${(ch.name || '').replace(/"/g, '&quot;')}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Handle</label>
                    <input type="text" id="editChHandle" class="form-control" value="${(ch.handle || '').replace(/"/g, '&quot;')}" placeholder="@channel">
                </div>
                <div class="form-group">
                    <label class="form-label">Description</label>
                    <textarea id="editChDesc" class="form-control" rows="3">${ch.description || ''}</textarea>
                </div>
            </form>
        `;
        const footerHtml = `
            <button class="btn btn-primary" onclick="saveEditChannelFromModal('${encodeURIComponent(channelId)}')"><i class="fas fa-save"></i> Save Changes</button>
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        `;
        openModal('Edit Channel Details', bodyHtml, footerHtml);
    } catch (err) {
        showToast('Failed to load channel details: ' + err.message, 'error');
    }
}

export async function saveEditChannelFromModal(channelId) {
    const name = document.getElementById('editChName')?.value?.trim();
    const handle = document.getElementById('editChHandle')?.value?.trim();
    const description = document.getElementById('editChDesc')?.value?.trim();

    if (!name) {
        showToast('Channel name is required', 'warning');
        return;
    }

    try {
        await api.patch(`/api/channels/${encodeURIComponent(channelId)}`, {
            name,
            handle,
            description
        });
        showToast('Channel updated successfully!', 'success');
        closeModal();
        loadChannels();
    } catch (err) {
        showToast('Failed to update channel: ' + err.message, 'error');
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
                <div class="empty-icon-ring"><i class="fas fa-layer-group"></i></div>
                <h3>No metadata templates yet</h3>
                <p>Create templates to standardize titles, descriptions, and tags across uploads.</p>
                <div style="margin-top:16px;">
                    <button type="button" class="btn btn-primary btn-sm" onclick="openAddTemplateModal()">
                        <i class="fas fa-plus"></i> Create First Template
                    </button>
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = templates.map(t => {
        const tags = Array.isArray(t.tags) ? t.tags : [];
        return `
            <div class="template-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">
                    <div style="flex:1; min-width:0;">
                        <h4 style="margin:0 0 6px 0; font-size:16px; font-weight:700; color:var(--text-primary);">${t.name}</h4>
                        <p style="margin:0; font-size:13px; color:var(--text-muted); line-height:1.4;">${t.description_template ? t.description_template.substring(0, 85) + '...' : 'No description template'}</p>
                    </div>
                    <div style="display:flex; gap:6px;">
                        <button class="btn btn-sm btn-icon" onclick="openEditTemplateModal('${t.template_id}')" title="Edit Template" style="background:rgba(59,130,246,0.1); border:none; width:32px; height:32px; border-radius:8px; cursor:pointer; color:#60a5fa;">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-icon text-danger" onclick="deleteTemplate('${t.template_id}')" title="Delete Template" style="background:rgba(239,68,68,0.1); border:none; width:32px; height:32px; border-radius:8px; cursor:pointer;">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="template-tags" style="display:flex; flex-wrap:wrap; gap:6px; margin:12px 0;">
                    ${tags.length > 0 ? tags.map(tag => `<span class="tag" style="background:rgba(59,130,246,0.12); color:#60a5fa; padding:2px 8px; border-radius:6px; font-size:11px;">#${tag}</span>`).join('') : '<span style="font-size:12px; color:var(--text-muted);">No tag presets</span>'}
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; padding-top:10px; border-top:1px solid rgba(255,255,255,0.06); font-size:12px;">
                    <span class="badge" style="background:rgba(255,255,255,0.06); color:var(--text-secondary); text-transform:capitalize;">${t.privacy_status || 'private'}</span>
                    <span class="text-muted">Category ${t.category || '22'}</span>
                </div>
            </div>
        `;
    }).join('');
}

export function openAddTemplateModal() {
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

export async function openEditTemplateModal(templateId) {
    try {
        const t = await api.get(`/api/templates/${encodeURIComponent(templateId)}`);
        const tagsStr = Array.isArray(t.tags) ? t.tags.join(', ') : (t.tags || '');
        const bodyHtml = `
            <form id="editTemplateForm" onsubmit="event.preventDefault(); saveEditTemplateFromModal('${encodeURIComponent(templateId)}');">
                <div class="form-group">
                    <label class="form-label">Template Name <span class="text-danger">*</span></label>
                    <input type="text" id="editTmplName" class="form-control" value="${(t.name || '').replace(/"/g, '&quot;')}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Title Template</label>
                    <input type="text" id="editTmplTitle" class="form-control" value="${(t.title_template || '').replace(/"/g, '&quot;')}" placeholder="{video_title} - Episode {episode}">
                </div>
                <div class="form-group">
                    <label class="form-label">Description Template</label>
                    <textarea id="editTmplDesc" class="form-control" rows="4">${t.description_template || ''}</textarea>
                </div>
                <div class="form-group">
                    <label class="form-label">Tags (comma separated)</label>
                    <input type="text" id="editTmplTags" class="form-control" value="${tagsStr.replace(/"/g, '&quot;')}">
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                    <div class="form-group">
                        <label class="form-label">Privacy</label>
                        <select id="editTmplPrivacy" class="form-control">
                            <option value="private" ${t.privacy_status === 'private' ? 'selected' : ''}>Private</option>
                            <option value="unlisted" ${t.privacy_status === 'unlisted' ? 'selected' : ''}>Unlisted</option>
                            <option value="public" ${t.privacy_status === 'public' ? 'selected' : ''}>Public</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Category</label>
                        <input type="text" id="editTmplCat" class="form-control" value="${t.category || '22'}">
                    </div>
                </div>
            </form>
        `;
        const footerHtml = `
            <button class="btn btn-primary" onclick="saveEditTemplateFromModal('${encodeURIComponent(templateId)}')"><i class="fas fa-save"></i> Save Changes</button>
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        `;
        openModal('Edit Metadata Template', bodyHtml, footerHtml);
    } catch (err) {
        showToast('Failed to load template: ' + err.message, 'error');
    }
}

export async function saveEditTemplateFromModal(templateId) {
    const name = document.getElementById('editTmplName')?.value?.trim();
    const titleTpl = document.getElementById('editTmplTitle')?.value?.trim();
    const descTpl = document.getElementById('editTmplDesc')?.value?.trim();
    const tags = (document.getElementById('editTmplTags')?.value || '')
        .split(',')
        .map(t => t.trim())
        .filter(Boolean);
    const privacy = document.getElementById('editTmplPrivacy')?.value || 'private';
    const category = document.getElementById('editTmplCat')?.value || '22';

    if (!name) {
        showToast('Template name is required', 'warning');
        return;
    }

    try {
        await api.patch(`/api/templates/${encodeURIComponent(templateId)}`, {
            name,
            title_template: titleTpl,
            description_template: descTpl,
            tags,
            privacy_status: privacy,
            category
        });
        showToast('Template updated successfully!', 'success');
        closeModal();
        loadTemplates();
    } catch (err) {
        showToast('Failed to update template: ' + err.message, 'error');
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
        const total = b.total_videos || (Array.isArray(b.video_paths) ? b.video_paths.length : 0);
        const percent = total > 0 ? Math.min(100, Math.round(((b.uploaded_count || 0) / total) * 100)) : 0;
        return `
            <div class="batch-card" style="margin-bottom:12px; padding:16px; border-radius:10px; background:var(--bg-card,#161b26); border:1px solid rgba(255,255,255,0.06);">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <h4 style="margin:0; font-size:15px; font-weight:600;"><i class="fas fa-boxes text-primary"></i> ${b.name}</h4>
                        <small class="text-muted">${b.created_at ? new Date(b.created_at).toLocaleString() : ''}</small>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span class="status-badge status-${b.status}">${b.status}</span>
                        <button type="button" class="btn btn-sm text-danger" style="background:none; border:none; cursor:pointer;" onclick="deleteBatch('${b.batch_id}')" title="Delete Batch">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="batch-progress" style="margin:12px 0 8px 0; background:rgba(255,255,255,0.08); border-radius:6px; height:8px; overflow:hidden;">
                    <div class="batch-progress-bar" style="width: ${percent}%; height:100%; background:var(--primary, #3b82f6); transition:width 0.3s ease;"></div>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:12px;" class="text-muted">
                    <span>${b.uploaded_count || 0}/${total} uploaded • ${b.failed_count || 0} failed</span>
                    <span>${percent}%</span>
                </div>
            </div>
        `;
    }).join('');
}

export async function deleteBatch(batchId) {
    if (!confirm('Are you sure you want to delete this batch from history?')) return;
    try {
        await api.delete(`/api/batches/${batchId}`);
        showToast('Batch removed from history', 'info');
        loadBatches();
    } catch (err) {
        showToast('Failed to delete batch: ' + err.message, 'error');
    }
}
window.deleteBatch = deleteBatch;

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
        showToast(`Initializing batch "${name}"...`, 'info');

        // 1. Create batch record in ChannelManager
        const batch = await api.post('/api/batches', {
            name,
            channel_id: channelId,
            template_id: templateId,
            priority: priority,
            total_videos: selectedBatchFiles.length
        });

        const batchId = batch.batch_id || '';
        showToast(`Queueing ${selectedBatchFiles.length} videos...`, 'info');

        // 2. Dispatch each video file as an UploadJob linked to batch_id
        for (let i = 0; i < selectedBatchFiles.length; i++) {
            const file = selectedBatchFiles[i];
            const formData = new FormData();
            formData.append('video', file);
            formData.append('channel_id', channelId);
            formData.append('priority', priority);
            if (templateId) formData.append('template_id', templateId);
            formData.append('metadata', JSON.stringify({
                batch_id: batchId,
                batch_name: name,
                video_index: i + 1,
                total_videos: selectedBatchFiles.length
            }));
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

// Global window bindings for inline onclick attributes and modals
Object.assign(window, {
    uploadToAccount,
    viewChannelStats,
    syncStudioData,
    syncChannelStudio,
    deleteAccount,
    addAccount,
    openAddAccountModal,
    closeAddAccountModal,
    openAddChannelModal,
    deleteChannel,
    saveChannelFromModal,
    openEditChannelModal,
    saveEditChannelFromModal,
    openAddTemplateModal,
    deleteTemplate,
    saveTemplateFromModal,
    openEditTemplateModal,
    saveEditTemplateFromModal,
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
    loadBatches,
    deleteBatch
});
