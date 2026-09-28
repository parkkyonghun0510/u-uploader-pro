/**
 * YouTube Uploader Pro - WebSocket Real-Time Telemetry
 * Socket.IO client handling bi-directional real-time events, job updates, and sync pushes.
 */

import { state } from './state.js';
import { updateQueueUI, updateJobProgress } from './queue.js';
import { updateStats, updateDashboardStats } from './dashboard.js';
import { renderAccounts, renderChannels } from './channels.js';
import { loadSupabaseProfile } from './supabase.js';
import { showToast } from './ui.js';

export function updateConnectionStatus(connected) {
    const el = document.getElementById('connectionStatus');
    if (!el) return;

    if (connected) {
        el.innerHTML = '<span class="status-dot"></span> Studio Live';
    } else {
        el.innerHTML = '<span class="status-dot" style="background:var(--accent-danger, #ef4444)"></span> Disconnected';
    }
}

export function initSocket() {
    if (typeof io === 'undefined') {
        console.warn('Socket.IO CDN not loaded. Real-time telemetry disabled.');
        return null;
    }

    const socket = io({
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: Infinity
    });

    state.socket = socket;

    socket.on('connect', () => {
        updateConnectionStatus(true);
        socket.emit('request_jobs');
        socket.emit('request_channels');
    });

    socket.on('disconnect', () => {
        updateConnectionStatus(false);
    });

    socket.on('connection', () => {
        updateConnectionStatus(true);
    });

    socket.on('jobs_update', (jobs) => {
        updateQueueUI(jobs);
        updateStats(jobs);
    });

    socket.on('upload_progress', (data) => {
        updateJobProgress(data);
        if (data.status === 'completed') {
            showToast(`✅ Upload complete: ${data.video_id || 'Video'}`, 'success');
        } else if (data.status === 'failed') {
            showToast(`❌ Upload failed: ${data.error_message || 'Unknown error'}`, 'error');
        }
    });

    socket.on('channels_update', (data) => {
        if (data) {
            renderAccounts(data.accounts || []);
            renderChannels(data.channels || []);
        }
    });

    socket.on('analytics_update', (stats) => {
        updateDashboardStats(stats);
    });

    socket.on('supabase_status', (data) => {
        const statusEl = document.getElementById('supabaseStatus');
        if (statusEl && data) {
            statusEl.textContent = data.connected ? '🟢 Connected' : '🔴 Disconnected';
            statusEl.className = data.connected ? 'status-connected' : 'status-disconnected';
        }
    });

    socket.on('sync_complete', (data) => {
        showToast(`Synced ${data.accounts || 0} accounts, ${data.channels || 0} channels, ${data.jobs || 0} jobs`, 'success');
        loadSupabaseProfile();
    });

    socket.on('supabase_sync', () => {
        loadSupabaseProfile();
    });

    socket.on('sync_error', (data) => {
        showToast('Sync error: ' + (data.error || 'Unknown error'), 'error');
    });

    socket.on('notifications', (notifications) => {
        if (Array.isArray(notifications) && notifications.length > 0) {
            const unread = notifications.filter(n => !n.is_read).length;
            if (unread > 0) {
                showToast(`🔔 ${unread} new notification${unread > 1 ? 's' : ''}`, 'info');
            }
        }
    });

    return socket;
}
