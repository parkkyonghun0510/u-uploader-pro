/**
 * YouTube Uploader Pro - Unified API Client
 * Secure network layer with auto-token injection, JSON serialization, and 401 interception.
 */

import { API_BASE } from './constants.js';
import { state } from './state.js';

export const _origFetch = window.fetch.bind(window);

let onUnauthorizedCallback = null;

export function setUnauthorizedHandler(callback) {
    onUnauthorizedCallback = callback;
}

/**
 * Enhanced fetch wrapper with automatic JWT injection & error interception.
 */
export async function secureFetch(url, options = {}) {
    const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url.startsWith('/') ? '' : '/'}${url}`;
    const opts = { ...options, headers: { ...(options.headers || {}) } };

    // Inject Bearer token if available and targeting API endpoints
    if (state.authToken && String(fullUrl).includes('/api/') && !opts.headers.Authorization) {
        opts.headers.Authorization = `Bearer ${state.authToken}`;
    }

    const response = await _origFetch(fullUrl, opts);

    // Check for 401 Unauthorized (exclude public auth endpoints)
    const isAuthRoute = String(fullUrl).includes('/api/auth/login') ||
                        String(fullUrl).includes('/api/auth/signup') ||
                        String(fullUrl).includes('/api/auth/forgot-password');

    if (response.status === 401 && String(fullUrl).includes('/api/') && !isAuthRoute) {
        if (state.authToken) {
            state.authToken = null;
            if (typeof onUnauthorizedCallback === 'function') {
                onUnauthorizedCallback();
            }
        }
    }

    return response;
}

// Monkey-patch window.fetch for backward compatibility
window.fetch = (url, opts) => secureFetch(url, opts);

export const api = {
    /**
     * GET request helper
     */
    async get(endpoint, options = {}) {
        const res = await secureFetch(endpoint, { method: 'GET', ...options });
        if (!res.ok) {
            const error = await res.json().catch(() => ({ error: `Request failed with status ${res.status}` }));
            throw new Error(error.error || error.message || `Status ${res.status}`);
        }
        return res.json();
    },

    /**
     * POST request helper
     */
    async post(endpoint, data = {}, options = {}) {
        const isFormData = data instanceof FormData;
        const headers = isFormData ? { ...(options.headers || {}) } : { 'Content-Type': 'application/json', ...(options.headers || {}) };
        const body = isFormData ? data : JSON.stringify(data);

        const res = await secureFetch(endpoint, {
            method: 'POST',
            headers,
            body,
            ...options
        });

        const json = await res.json().catch(() => ({}));
        if (!res.ok) {
            throw new Error(json.error || json.message || `Status ${res.status}`);
        }
        return json;
    },

    /**
     * DELETE request helper
     */
    async delete(endpoint, options = {}) {
        const res = await secureFetch(endpoint, { method: 'DELETE', ...options });
        const json = await res.json().catch(() => ({}));
        if (!res.ok) {
            throw new Error(json.error || json.message || `Status ${res.status}`);
        }
        return json;
    }
};
