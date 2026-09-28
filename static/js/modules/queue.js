/**
 * YouTube Uploader Pro - Upload Queue Controller
 * Manages active upload jobs, filtering, live progress tracking, and job inspection.
 */

import { api } from './api.js';
import { state } from './state.js';
import { updateStats, loadDashboard } from './dashboard.js';
import {
    showToast,
    openModal,
    closeModal,
    getFileName,
    formatDate
} from './ui.js';

export async function loadQueue() {
    try {
        const filter = state.currentFilter;
        const endpoint = filter === 'all' ? '/api/jobs' : `/api/jobs?status=${encodeURIComponent(filter)}`;
        const jobs = await api.get(endpoint);
        renderQueue(jobs);
    } catch (err) {
        console.error('Failed to load queue:', err);
    }
}

export function renderQueue(jobs = []) {
    const container = document.getElementById('queueList');
    if (!container) return;

    if (!Array.isArray(jobs) || jobs.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-layer-group"></i>
                <h3>Queue is Empty</h3>
                <p>No upload jobs matching filter "${state.currentFilter}".</p>
            </div>
        `;
        return;
    }

    container.innerHTML = jobs.map(job => {
        const isCompleted = job.status === 'completed';
        const isFailed = job.status === 'failed';
        const isCancellable = ['pending', 'scheduled', 'in_progress'].includes(job.status);
        const progressClass = isCompleted ? 'completed' : isFailed ? 'failed' : '';

        return `
            <div class="queue-item" data-id="${job.job_id}">
                <div class="queue-item-info">
                    <div class="queue-item-name">${getFileName(job.video_path)}</div>
                    <div class="queue-item-meta">
                        <span class="status-badge status-${job.status}">${job.status.replace('_', ' ')}</span>
                        ${job.schedule ? `<span>• Scheduled: ${job.schedule}</span>` : ''}
                        ${job.priority ? `<span>• Priority: ${job.priority}</span>` : ''}
                        <span>• Progress: ${Math.round(job.progress || 0)}%</span>
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-bar ${progressClass}" style="width: ${Math.min(100, Math.max(0, job.progress || 0))}%"></div>
                    </div>
                </div>
                <div class="queue-item-actions">
                    ${isFailed ? `
                        <button class="btn btn-sm btn-outline" onclick="retryJob('${job.job_id}')" title="Retry Upload">
                            <i class="fas fa-redo"></i>
                        </button>
                    ` : ''}
                    ${isCancellable ? `
                        <button class="btn btn-sm btn-outline text-danger" onclick="cancelJob('${job.job_id}')" title="Cancel Job">
                            <i class="fas fa-stop"></i>
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-icon" onclick="showJobDetails('${job.job_id}')" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

export function updateQueueUI(jobs) {
    if (state.currentPage === 'queue') {
        loadQueue();
    }
    updateStats(jobs);
}

export function updateJobProgress(data) {
    if (state.currentPage === 'queue') {
        loadQueue();
    }
    if (state.currentPage === 'dashboard') {
        loadDashboard();
    }
}

export async function cancelJob(jobId) {
    try {
        await api.post(`/api/jobs/${jobId}/cancel`);
        showToast('Job cancelled successfully', 'info');
        loadQueue();
    } catch (err) {
        showToast('Failed to cancel job: ' + err.message, 'error');
    }
}

export async function retryJob(jobId) {
    try {
        await api.post(`/api/jobs/${jobId}/retry`);
        showToast('Retry dispatched', 'info');
        loadQueue();
    } catch (err) {
        showToast('Failed to retry job: ' + err.message, 'error');
    }
}

export async function showJobDetails(jobId) {
    try {
        const job = await api.get(`/api/jobs/${jobId}`);
        const logsText = Array.isArray(job.logs) ? job.logs.join('\n') : (job.logs || 'No logs recorded');

        const bodyHtml = `
            <div class="job-detail-grid" style="display:flex;flex-direction:column;gap:14px">
                <div class="detail-row"><strong>File:</strong> <code>${getFileName(job.video_path)}</code></div>
                <div class="detail-row"><strong>Full Path:</strong> <small class="text-muted" style="word-break:break-all">${job.video_path || 'N/A'}</small></div>
                <div class="detail-row"><strong>Status:</strong> <span class="status-badge status-${job.status}">${job.status}</span></div>
                <div class="detail-row"><strong>Progress:</strong> ${Math.round(job.progress || 0)}%</div>
                <div class="detail-row"><strong>YouTube ID:</strong> <code>${job.video_id || 'Not assigned yet'}</code></div>
                <div class="detail-row"><strong>Created At:</strong> ${formatDate(job.created_at)}</div>
                <div class="detail-row"><strong>Priority:</strong> <span class="tag">${job.priority || 'normal'}</span></div>
                ${job.error_message ? `<div class="detail-row text-danger"><strong>Error:</strong> ${job.error_message}</div>` : ''}
                <div>
                    <strong>Execution Log Stream:</strong>
                    <pre style="background:var(--bg-input, #0f172a);color:var(--text-primary, #f8fafc);padding:12px;border-radius:8px;font-family:'JetBrains Mono',monospace;font-size:0.75rem;max-height:220px;overflow:auto;margin-top:6px;border:1px solid var(--border-color, rgba(255,255,255,0.08))">${logsText}</pre>
                </div>
            </div>
        `;

        const footerHtml = `
            ${job.status === 'failed' ? `<button class="btn btn-primary" onclick="retryJob('${jobId}'); closeModal();"><i class="fas fa-redo"></i> Retry</button>` : ''}
            <button class="btn btn-secondary" onclick="closeModal()">Close</button>
        `;

        openModal(`Job Details #${job.job_id.substring(0, 8)}`, bodyHtml, footerHtml);
    } catch (err) {
        showToast('Failed to load job details: ' + err.message, 'error');
    }
}

export async function clearCompleted() {
    try {
        // Optimistic refresh or request clear if server supports
        showToast('Refreshing queue...', 'info');
        await loadQueue();
    } catch (err) {
        showToast('Failed to clear queue', 'error');
    }
}

export function initQueueFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentFilter = btn.dataset.filter || 'all';
            loadQueue();
        });
    });

    const refreshQueueBtn = document.getElementById('refreshQueue');
    if (refreshQueueBtn) refreshQueueBtn.addEventListener('click', loadQueue);

    const clearCompletedBtn = document.getElementById('clearCompleted');
    if (clearCompletedBtn) clearCompletedBtn.addEventListener('click', clearCompleted);
}
