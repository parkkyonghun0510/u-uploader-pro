/**
 * YouTube Uploader Pro - Frontend Constants
 * Design System, Endpoints & Metadata Mappings
 */

export const API_BASE = window.location.origin.includes('http')
    ? window.location.origin
    : 'http://localhost:8080';

export const SUPABASE_URL = 'https://aisbzppswxqknjvntaaa.supabase.co';
export const SUPABASE_ANON_KEY = 'sb_publishable__LERUIuVlqzUksHA3-AU3g_GSW-YxoE';

export const STATUS_COLORS = {
    completed: 'var(--accent-success, #10b981)',
    failed: 'var(--accent-danger, #ef4444)',
    in_progress: 'var(--accent-primary, #3b82f6)',
    pending: 'var(--accent-warning, #f59e0b)',
    scheduled: '#8b5cf6',
    cancelled: 'var(--text-muted, #94a3b8)'
};

export const STATUS_ICONS = {
    completed: 'fa-check-circle',
    failed: 'fa-times-circle',
    in_progress: 'fa-spinner fa-spin',
    pending: 'fa-clock',
    scheduled: 'fa-calendar-alt',
    cancelled: 'fa-ban',
    info: 'fa-info-circle',
    success: 'fa-check-circle',
    warning: 'fa-exclamation-triangle',
    error: 'fa-exclamation-circle'
};

export const PROGRESS_COLORS = {
    completed: 'rgba(34, 197, 94, 0.75)',
    failed: 'rgba(239, 68, 68, 0.75)',
    in_progress: 'rgba(59, 130, 246, 0.75)',
    pending: 'rgba(245, 158, 11, 0.75)',
    scheduled: 'rgba(139, 92, 246, 0.75)',
    cancelled: 'rgba(100, 116, 139, 0.75)'
};

export const PAGE_TITLES = {
    dashboard: 'Dashboard',
    upload: 'New Upload',
    queue: 'Upload Queue',
    history: 'Upload History',
    profiles: 'Upload Profiles',
    settings: 'Settings',
    channels: 'Channel Management'
};

export const PAGE_DOM_MAP = {
    dashboard: 'dashboardPage',
    upload: 'uploadPage',
    queue: 'queuePage',
    history: 'historyPage',
    profiles: 'profilesPage',
    settings: 'settingsPage',
    channels: 'channelsPage'
};
