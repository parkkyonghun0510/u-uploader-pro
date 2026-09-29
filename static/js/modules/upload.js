/**
 * YouTube Uploader Pro - Upload Operations & Form Processing
 * Handles file inputs, JSON metadata validation, job submission, history, and profiles.
 */

import { api } from './api.js';
import { navigateTo } from './navigation.js';
import {
    showToast,
    openModal,
    closeModal,
    getFileName,
    formatDate
} from './ui.js';

export function initFileInputs() {
    ['videoFile', 'metaFile', 'thumbFile'].forEach(id => {
        const input = document.getElementById(id);
        const display = document.getElementById(id + 'Display');
        if (input && display) {
            input.addEventListener('change', () => {
                if (input.files.length > 0) {
                    display.innerHTML = `
                        <i class="fas fa-check-circle" style="color:var(--accent-success, #10b981)"></i>
                        <span style="font-weight:500;">${input.files[0].name}</span>
                    `;
                }
            });
        }
    });

    const metaFile = document.getElementById('metaFile');
    if (metaFile) {
        metaFile.addEventListener('change', (e) => {
            const file = e.target.files[0];
            const previewEl = document.getElementById('metaPreview');
            if (!file || !previewEl) return;

            const reader = new FileReader();
            reader.onload = (event) => {
                try {
                    const meta = JSON.parse(event.target.result);
                    previewEl.innerHTML = `
                        <div class="meta-preview-card">
                            <div><strong>Title:</strong> ${meta.title || '<span class="text-muted">N/A</span>'}</div>
                            <div><strong>Description:</strong> ${meta.description ? meta.description.substring(0, 100) + '...' : '<span class="text-muted">N/A</span>'}</div>
                            <div><strong>Tags:</strong> ${Array.isArray(meta.tags) ? meta.tags.join(', ') : '<span class="text-muted">N/A</span>'}</div>
                            <div><strong>Schedule:</strong> ${meta.schedule || '<span class="text-muted">Immediate</span>'}</div>
                            <div><strong>Playlist:</strong> ${meta.playlist_title || '<span class="text-muted">None</span>'}</div>
                        </div>
                    `;
                } catch {
                    previewEl.innerHTML = '<p class="text-danger"><i class="fas fa-exclamation-triangle"></i> Invalid JSON metadata schema</p>';
                }
            };
            reader.readAsText(file);
        });
    }
}

export async function handleUpload(e) {
    e.preventDefault();
    const videoInput = document.getElementById('videoFile');
    const metaInput = document.getElementById('metaFile');
    const thumbInput = document.getElementById('thumbFile');
    const scheduleInput = document.getElementById('scheduleInput');
    const priorityInput = document.getElementById('priorityInput');

    if (!videoInput || !videoInput.files.length) {
        showToast('Please select a video file to upload', 'warning');
        return;
    }

    const metadata = {};
    if (metaInput && metaInput.files.length) {
        try {
            const reader = new FileReader();
            await new Promise((resolve, reject) => {
                reader.onload = resolve;
                reader.onerror = reject;
                reader.readAsText(metaInput.files[0]);
            });
            const meta = JSON.parse(reader.result);
            metadata.title = meta.title;
            metadata.description = meta.description;
            metadata.tags = meta.tags;
            metadata.schedule = meta.schedule;
            metadata.playlist_title = meta.playlist_title;
        } catch {
            showToast('Invalid metadata JSON file format', 'error');
            return;
        }
    }

    const channelInput = document.getElementById('uploadChannelSelect');

    const jobData = {
        video_path: videoInput.files[0].path || videoInput.files[0].name,
        metadata_path: metaInput && metaInput.files.length ? metaInput.files[0].name : null,
        thumbnail_path: thumbInput && thumbInput.files.length ? thumbInput.files[0].name : null,
        schedule: (scheduleInput && scheduleInput.value) ? scheduleInput.value : null,
        priority: (priorityInput && priorityInput.value) ? priorityInput.value : 'normal',
        channel_id: (channelInput && channelInput.value) ? channelInput.value : null,
        metadata: metadata
    };

    try {
        const result = await api.post('/api/jobs', jobData);
        showToast(`🚀 Upload queued! Job ID: ${result.job_id || 'Active'}`, 'success');
        navigateTo('queue');
    } catch (err) {
        showToast(`Upload failed: ${err.message}`, 'error');
    }
}

export function populateChannelDropdown(channels = [], accounts = []) {
    const select = document.getElementById('uploadChannelSelect');
    if (!select) return;

    const currentVal = select.value;
    select.innerHTML = '<option value="">Default Studio Profile</option>';

    // Add managed channels
    channels.forEach(ch => {
        const opt = document.createElement('option');
        opt.value = ch.channel_id;
        opt.textContent = `📺 ${ch.name} (${ch.handle || ch.channel_id})`;
        select.appendChild(opt);
    });

    // Add accounts as options if no specific channel
    accounts.forEach(acc => {
        if (!channels.some(c => c.account_id === acc.id)) {
            const opt = document.createElement('option');
            opt.value = acc.id;
            opt.textContent = `👤 ${acc.display_name} (${acc.email || 'Google Account'})`;
            select.appendChild(opt);
        }
    });

    if (currentVal) select.value = currentVal;
}

export async function loadHistory() {
    try {
        const history = await api.get('/api/history');
        renderHistory(history);
    } catch (err) {
        console.error('Failed to load history:', err);
    }
}

export function renderHistory(history = []) {
    const tbody = document.getElementById('historyTableBody');
    if (!tbody) return;

    if (!Array.isArray(history) || history.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted" style="padding: 32px 0;">No completed upload history recorded yet</td></tr>';
        return;
    }

    tbody.innerHTML = history.map(item => `
        <tr>
            <td><strong>${getFileName(item.video_path)}</strong></td>
            <td><span class="status-badge status-${item.status}">${item.status.replace('_', ' ')}</span></td>
            <td><code>${item.video_id || 'N/A'}</code></td>
            <td>${formatDate(item.created_at)}</td>
            <td>${Math.round(item.progress || 0)}%</td>
        </tr>
    `).join('');
}

export async function loadProfiles() {
    try {
        const profiles = await api.get('/api/profiles');
        renderProfiles(profiles);
    } catch (err) {
        console.error('Failed to load profiles:', err);
    }
}

export function renderProfiles(profiles = []) {
    const grid = document.getElementById('profilesGrid');
    if (!grid) return;

    if (!Array.isArray(profiles) || profiles.length === 0) {
        grid.innerHTML = '<div class="empty-state"><i class="fas fa-id-card"></i><h3>No profiles configured</h3><p>Save recurring upload configurations for quick reuse</p></div>';
        return;
    }

    grid.innerHTML = profiles.map(p => `
        <div class="profile-card">
            <h4>${p.name || 'Profile'}</h4>
            <p>${p.description || 'No description provided'}</p>
            <p style="margin-top:8px;font-size:0.8rem;color:var(--text-muted)">Created: ${p.created_at || 'N/A'}</p>
            <div style="margin-top:12px;display:flex;gap:8px">
                <button class="btn btn-sm btn-outline text-danger" onclick="deleteProfile('${p.name}')" title="Delete Profile">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

export function showAddProfileModal() {
    const bodyHtml = `
        <form id="addProfileForm">
            <div class="form-group">
                <label class="form-label">Profile Name</label>
                <input type="text" id="profileName" class="form-control" placeholder="Gaming Shorts Profile" required>
            </div>
            <div class="form-group">
                <label class="form-label">Description</label>
                <input type="text" id="profileDesc" class="form-control" placeholder="Automated presets for gaming highlight clips">
            </div>
            <div class="form-group">
                <label class="form-label">Default Video Directory</label>
                <input type="text" id="profilePath" class="form-control" placeholder="/Users/mac/Videos/Rendered">
            </div>
        </form>
    `;
    const footerHtml = `
        <button class="btn btn-primary" onclick="saveProfileFromModal()">Save Profile</button>
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
    `;

    openModal('Create Upload Profile', bodyHtml, footerHtml);
}

export async function saveProfileFromModal() {
    const nameEl = document.getElementById('profileName');
    const descEl = document.getElementById('profileDesc');
    const pathEl = document.getElementById('profilePath');

    const name = nameEl ? nameEl.value.trim() : '';
    const desc = descEl ? descEl.value.trim() : '';
    const path = pathEl ? pathEl.value.trim() : '';

    if (!name) {
        showToast('Please enter a profile name', 'warning');
        return;
    }

    try {
        await api.post('/api/profiles', { name, description: desc, default_path: path });
        showToast('Profile saved successfully!', 'success');
        closeModal();
        loadProfiles();
    } catch (err) {
        showToast('Failed to save profile: ' + err.message, 'error');
    }
}

export async function deleteProfile(name) {
    if (!confirm(`Are you sure you want to delete profile "${name}"?`)) return;
    try {
        await api.delete(`/api/profiles/${encodeURIComponent(name)}`);
        showToast('Profile deleted', 'info');
        loadProfiles();
    } catch (err) {
        showToast('Failed to delete profile: ' + err.message, 'error');
    }
}

export async function saveSettings(e) {
    e.preventDefault();
    const settings = {
        max_retries: document.getElementById('maxRetries')?.value,
        retry_delay: document.getElementById('retryDelay')?.value,
        theme: document.getElementById('themeSelect')?.value || 'dark',
        auto_login: document.getElementById('autoLogin')?.checked || false,
        notifications: document.getElementById('notifications')?.checked || false
    };

    try {
        await api.post('/api/config', settings);
        document.body.className = settings.theme === 'light' ? 'light-theme' : 'dark-theme';
        showToast('System configuration saved!', 'success');
    } catch (err) {
        showToast('Failed to save settings: ' + err.message, 'error');
    }
}

export function initForms() {
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) uploadForm.addEventListener('submit', handleUpload);

    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            showToast('Syncing system state...', 'info');
        });
    }

    const refreshHistoryBtn = document.getElementById('refreshHistory');
    if (refreshHistoryBtn) refreshHistoryBtn.addEventListener('click', loadHistory);

    const addProfileBtn = document.getElementById('addProfileBtn');
    if (addProfileBtn) addProfileBtn.addEventListener('click', showAddProfileModal);

    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) settingsForm.addEventListener('submit', saveSettings);

    const modalClose = document.getElementById('modalClose');
    if (modalClose) modalClose.addEventListener('click', closeModal);

    const modalOverlay = document.getElementById('modalOverlay');
    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) closeModal();
        });
    }

    initFileInputs();
}
