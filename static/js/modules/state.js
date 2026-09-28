/**
 * YouTube Uploader Pro - Reactive State Store
 * Centralized state container for frontend application.
 */

class AppState {
    constructor() {
        this._authToken = localStorage.getItem('authToken') || null;
        this._authMode = window.location.pathname.includes('signup') ? 'signup' : 'login';
        this._currentPage = 'dashboard';
        this._currentFilter = 'all';
        this._currentUser = null;
        this._socket = null;
        this._progressChart = null;
        this._refreshInterval = null;
        this._listeners = new Map();
    }

    get authToken() {
        return this._authToken;
    }

    set authToken(token) {
        this._authToken = token;
        if (token) {
            localStorage.setItem('authToken', token);
        } else {
            localStorage.removeItem('authToken');
        }
        this._notify('authToken', token);
    }

    get authMode() {
        return this._authMode;
    }

    set authMode(mode) {
        this._authMode = mode;
        this._notify('authMode', mode);
    }

    get currentPage() {
        return this._currentPage;
    }

    set currentPage(page) {
        this._currentPage = page;
        this._notify('currentPage', page);
    }

    get currentFilter() {
        return this._currentFilter;
    }

    set currentFilter(filter) {
        this._currentFilter = filter;
        this._notify('currentFilter', filter);
    }

    get currentUser() {
        return this._currentUser;
    }

    set currentUser(user) {
        this._currentUser = user;
        this._notify('currentUser', user);
    }

    get socket() {
        return this._socket;
    }

    set socket(s) {
        this._socket = s;
        this._notify('socket', s);
    }

    get progressChart() {
        return this._progressChart;
    }

    set progressChart(chart) {
        this._progressChart = chart;
    }

    subscribe(key, callback) {
        if (!this._listeners.has(key)) {
            this._listeners.set(key, new Set());
        }
        this._listeners.get(key).add(callback);
        return () => this._listeners.get(key).delete(callback);
    }

    _notify(key, value) {
        if (this._listeners.has(key)) {
            this._listeners.get(key).forEach(cb => {
                try {
                    cb(value);
                } catch (e) {
                    console.error(`Error in state listener for ${key}:`, e);
                }
            });
        }
    }

    startPolling(callback, intervalMs = 5000) {
        this.stopPolling();
        if (typeof callback === 'function') {
            this._refreshInterval = setInterval(callback, intervalMs);
        }
    }

    stopPolling() {
        if (this._refreshInterval) {
            clearInterval(this._refreshInterval);
            this._refreshInterval = null;
        }
    }
}

export const state = new AppState();
