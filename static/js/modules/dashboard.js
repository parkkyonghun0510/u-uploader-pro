/**
 * YouTube Uploader Pro - Studio Dashboard Controller
 * Real-time metric counters, activity timeline stream, and Chart.js telemetry.
 */

import { api } from './api.js';
import { state } from './state.js';
import {
    animateNumber,
    formatDate,
    getFileName,
    getStatusColor,
    getStatusIcon,
    getProgressColor
} from './ui.js';

export async function loadDashboard() {
    try {
        const jobs = await api.get('/api/jobs');
        updateStats(jobs);
        updateActivity(jobs);
        initProgressChart(jobs);
    } catch (err) {
        console.error('Failed to load dashboard metrics:', err);
    }
}

export function updateStats(jobs = []) {
    if (!Array.isArray(jobs)) return;

    const total = jobs.length;
    const completed = jobs.filter(j => j.status === 'completed').length;
    const active = jobs.filter(j => j.status === 'in_progress').length;
    const failed = jobs.filter(j => j.status === 'failed').length;

    animateNumber('totalUploaded', total);
    animateNumber('completedCount', completed);
    animateNumber('activeCount', active);
    animateNumber('failedCount', failed);

    const badge = document.getElementById('queueBadge');
    if (badge) {
        badge.textContent = total;
    }
}

export function updateDashboardStats(stats) {
    if (!stats) return;
    if (stats.total !== undefined) animateNumber('totalUploaded', stats.total);
    if (stats.completed !== undefined) animateNumber('completedCount', stats.completed);
    if (stats.active !== undefined) animateNumber('activeCount', stats.active);
    if (stats.failed !== undefined) animateNumber('failedCount', stats.failed);
}

export function updateActivity(jobs = []) {
    const container = document.getElementById('recentActivity');
    if (!container) return;

    if (!Array.isArray(jobs) || jobs.length === 0) {
        container.innerHTML = `
            <div class="empty-state-mini">
                <i class="fas fa-satellite-dish text-muted"></i>
                <p class="text-muted">No upload activity recorded yet</p>
            </div>
        `;
        return;
    }

    const recent = jobs.slice(0, 6);
    container.innerHTML = recent.map(job => `
        <div class="activity-item">
            <div class="activity-icon" style="color: ${getStatusColor(job.status)}">
                <i class="fas ${getStatusIcon(job.status)}"></i>
            </div>
            <div class="activity-text">
                <div class="activity-title">${getFileName(job.video_path)}</div>
                <small class="text-muted">
                    <span class="status-badge status-${job.status}">${job.status.replace('_', ' ')}</span>
                    ${job.progress > 0 ? ` • ${Math.round(job.progress)}%` : ''}
                    • ${formatDate(job.created_at)}
                </small>
            </div>
        </div>
    `).join('');
}

export function initProgressChart(jobs = []) {
    const ctx = document.getElementById('progressChart');
    if (!ctx || typeof Chart === 'undefined') return;

    if (state.progressChart) {
        state.progressChart.destroy();
        state.progressChart = null;
    }

    const safeJobs = Array.isArray(jobs) ? jobs : [];
    const recentJobs = safeJobs.slice(-10);
    const labels = recentJobs.map(j => getFileName(j.video_path).substring(0, 18));
    const data = recentJobs.map(j => j.progress || 0);
    const colors = recentJobs.map(j => getProgressColor(j.status));

    const computedStyle = getComputedStyle(document.documentElement);
    const textColor = computedStyle.getPropertyValue('--text-muted').trim() || '#94a3b8';

    state.progressChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.length ? labels : ['No Jobs'],
            datasets: [{
                label: 'Progress (%)',
                data: data.length ? data : [0],
                backgroundColor: colors.length ? colors : ['rgba(148, 163, 184, 0.3)'],
                borderRadius: 6,
                barThickness: 18
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleFont: { family: "'Plus Jakarta Sans', sans-serif" },
                    bodyFont: { family: "'JetBrains Mono', monospace" },
                    padding: 10,
                    cornerRadius: 8
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        color: textColor,
                        font: { family: "'JetBrains Mono', monospace", size: 11 },
                        callback: val => `${val}%`
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        color: textColor,
                        font: { family: "'Plus Jakarta Sans', sans-serif", size: 10 },
                        maxRotation: 25
                    }
                }
            }
        }
    });
}
