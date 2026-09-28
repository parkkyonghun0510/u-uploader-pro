/**
 * YouTube Uploader Pro - YouTube Data API v3 Explorer
 * Direct integration with Google Cloud YouTube Data API v3.
 */

import { api } from './api.js';
import { showToast } from './ui.js';

export async function saveYouTubeApiKey() {
    const key = document.getElementById('apiKeyInput')?.value?.trim();
    if (!key) {
        showToast('Please enter an API key', 'warning');
        return;
    }
    try {
        await api.post('/api/youtube/auth', { api_key: key });
        showToast('YouTube Data API key configured!', 'success');
    } catch (err) {
        showToast('Failed to connect YouTube API: ' + err.message, 'error');
    }
}

export async function loadYouTubeChannels() {
    try {
        const channels = await api.get('/api/youtube/channels');
        const resEl = document.getElementById('youtubeResults');
        if (resEl) {
            resEl.innerHTML = `<p class="text-muted" style="margin-bottom:12px;">Discovered ${channels.length} live channels</p>` +
                channels.map(c => `
                    <div class="account-card" style="margin-bottom:8px">
                        <div class="account-avatar"><i class="fas fa-tv"></i></div>
                        <div class="account-info">
                            <h4>${c.snippet?.title || c.id}</h4>
                            <p>${parseInt(c.statistics?.subscriberCount || 0).toLocaleString()} subscribers</p>
                        </div>
                    </div>
                `).join('');
        }
    } catch (err) {
        showToast('Failed to fetch YouTube channels: ' + err.message, 'error');
    }
}

export async function searchYouTubeVideos() {
    const query = prompt('Search YouTube videos:');
    if (!query) return;
    try {
        const videos = await api.get(`/api/youtube/search?q=${encodeURIComponent(query)}&type=video`);
        const resEl = document.getElementById('youtubeResults');
        if (resEl) {
            resEl.innerHTML = videos.map(v => `
                <div class="channel-card" style="margin-bottom:8px">
                    <div class="channel-avatar"><i class="fas fa-video"></i></div>
                    <div class="channel-info">
                        <h4>${v.snippet?.title || 'Video'}</h4>
                        <p>ID: <code>${v.id?.videoId || 'N/A'}</code></p>
                    </div>
                </div>
            `).join('');
        }
    } catch (err) {
        showToast('Search query failed: ' + err.message, 'error');
    }
}
