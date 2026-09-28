/**
 * YouTube Uploader Pro - UI System & Visual Feedback
 * Dynamic alerts, animated toasts, modal manager, and text formatters.
 */

import { STATUS_COLORS, STATUS_ICONS, PROGRESS_COLORS } from './constants.js';

/**
 * Toast Notification System
 */
export function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const iconClass = STATUS_ICONS[type] || 'fa-info-circle';

    toast.innerHTML = `
        <i class="fas ${iconClass}"></i>
        <span class="toast-message">${message}</span>
        <button class="toast-close" aria-label="Close">&times;</button>
    `;

    const closeBtn = toast.querySelector('.toast-close');
    const dismiss = () => {
        toast.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    };

    if (closeBtn) closeBtn.onclick = dismiss;

    container.appendChild(toast);
    setTimeout(dismiss, 4200);
}

/**
 * Modal Manager
 */
export function openModal(title, bodyHtml, footerHtml = '') {
    const overlay = document.getElementById('modalOverlay');
    const titleEl = document.getElementById('modalTitle');
    const bodyEl = document.getElementById('modalBody');
    const footerEl = document.getElementById('modalFooter');

    if (!overlay || !bodyEl) return;

    if (titleEl) titleEl.textContent = title;
    bodyEl.innerHTML = bodyHtml;
    if (footerEl) footerEl.innerHTML = footerHtml;

    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

export function closeModal() {
    const overlay = document.getElementById('modalOverlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
    document.body.style.overflow = '';
}

/**
 * Animated Number Counter (Tick Effect)
 */
export function animateNumber(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    const current = parseInt(el.textContent.replace(/[^0-9]/g, '')) || 0;
    if (current === target) return;

    const diff = target - current;
    const steps = 25;
    let step = 0;

    const interval = setInterval(() => {
        step++;
        const val = Math.round(current + (diff * (step / steps)));
        el.textContent = val.toLocaleString();
        if (step >= steps) {
            el.textContent = target.toLocaleString();
            clearInterval(interval);
        }
    }, 24);
}

/**
 * Extract clean filename from a path
 */
export function getFileName(path) {
    if (!path) return 'Unknown file';
    return path.split('/').pop().split('\\').pop();
}

/**
 * Get CSS color variable for job/connection status
 */
export function getStatusColor(status) {
    return STATUS_COLORS[status] || 'var(--text-muted, #94a3b8)';
}

/**
 * Get FontAwesome icon class for a status
 */
export function getStatusIcon(status) {
    return STATUS_ICONS[status] || 'fa-circle';
}

/**
 * Get rgba color for charts & progress indicators
 */
export function getProgressColor(status) {
    return PROGRESS_COLORS[status] || 'rgba(100, 116, 139, 0.7)';
}

/**
 * Human-friendly date and time formatter
 */
export function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;
        return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) + ' ' +
               d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
        return dateStr;
    }
}

/**
 * Format bytes into human-readable sizes (KB, MB, GB)
 */
export function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}
