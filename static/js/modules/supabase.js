/**
 * YouTube Uploader Pro - Supabase Cloud Synchronization Service
 * Manages health checks, real-time database sync, cloud telemetry, and bucket uploads.
 */

import { api } from './api.js';
import { state } from './state.js';
import { updateUserBadge } from './auth.js';
import { showToast } from './ui.js';

export function initSupabase() {
    try {
        checkSupabaseConnection();
    } catch (e) {
        console.error('Supabase initialization warning:', e);
    }
}

export function initSupabasePanel() {
    const panel = document.getElementById('supabasePanel');
    const syncBtn = document.getElementById('supabaseSyncBtn');
    if (panel && syncBtn) {
        syncBtn.addEventListener('click', () => {
            panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
        });
        setTimeout(() => {
            panel.style.display = 'flex';
        }, 1200);
    }
}

export async function checkSupabaseConnection() {
    const statusEl = document.getElementById('supabaseStatus');
    try {
        const data = await api.get('/api/supabase/health');
        if (statusEl) {
            statusEl.textContent = data.supabase_connected ? '🟢 Connected' : '🔴 Disconnected';
            statusEl.className = data.supabase_connected ? 'status-connected' : 'status-disconnected';
        }
    } catch {
        if (statusEl) {
            statusEl.textContent = '🔴 Disconnected';
            statusEl.className = 'status-disconnected';
        }
    }
}

export async function syncToSupabase() {
    try {
        const data = await api.post('/api/supabase/sync');
        if (data.synced) {
            showToast('Database successfully synced to Supabase Cloud!', 'success');
            loadSupabaseProfile();
        } else {
            showToast('Sync completed with warnings', 'warning');
        }
    } catch (e) {
        showToast('Sync failed: ' + e.message, 'error');
    }
}

export async function loadSupabaseStats() {
    try {
        const data = await api.get('/api/supabase/dashboard');
        const statsEl = document.getElementById('supabaseStats');
        if (statsEl && data && data.stats) {
            statsEl.innerHTML = `
                <div class="stat-item">Accounts: ${data.accounts ? data.accounts.length : 0}</div>
                <div class="stat-item">Channels: ${data.stats.total_channels || 0}</div>
                <div class="stat-item">Templates: ${data.stats.total_templates || 0}</div>
                <div class="stat-item">Uploads: ${data.stats.total_uploads || 0}</div>
                <div class="stat-item">Completed: ${data.stats.completed_uploads || 0}</div>
            `;
        }
    } catch (e) {
        console.error('Failed to load Supabase telemetry:', e);
    }
}

export async function loadSupabaseProfile() {
    try {
        const profile = await api.get('/api/supabase/profile');
        if (profile && profile.display_name) {
            const statusEl = document.getElementById('supabaseStatus');
            if (statusEl) {
                statusEl.textContent = `🟢 ${profile.display_name}`;
            }
            updateUserBadge(profile);
        }
    } catch (err) {
        console.error('Failed to load Supabase profile:', err);
    }
}

export async function uploadToSupabaseStorage(filePath, bucket = 'videos', channelId = null) {
    try {
        const data = await api.post('/api/supabase/storage/upload', {
            file_path: filePath,
            bucket,
            channel_id: channelId
        });
        if (data.success) {
            showToast('Asset uploaded to Supabase Storage!', 'success');
            return data.url;
        }
    } catch (e) {
        showToast('Storage upload failed: ' + e.message, 'error');
    }
    return null;
}

export function subscribeToRealtime() {
    if (state.socket) {
        state.socket.emit('subscribe_upload_progress', {});
    }
}

export function requestSupabaseSync() {
    if (state.socket) {
        state.socket.emit('request_supabase_sync');
    }
}

export function requestNotifications() {
    if (state.socket) {
        state.socket.emit('request_notifications');
    }
}
