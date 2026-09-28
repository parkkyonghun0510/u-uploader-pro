/**
 * YouTube Uploader Pro - Main Application Orchestrator
 * Modular ES architecture coordinating telemetry, authentication, routing, and upload pipelines.
 */

import { state } from './modules/state.js';
import { setUnauthorizedHandler } from './modules/api.js';
import { showToast, closeModal, openModal } from './modules/ui.js';
import {
    checkAuthUser,
    showAuthScreen,
    hideAuthScreen,
    setAuthMode,
    showAuthAlert,
    togglePasswordVisibility,
    showAuthModal,
    logout,
    initAuthHandlers
} from './modules/auth.js';
import { initNavigation, navigateTo } from './modules/navigation.js';
import { initSocket } from './modules/socket.js';
import { loadDashboard } from './modules/dashboard.js';
import {
    loadQueue,
    cancelJob,
    retryJob,
    showJobDetails,
    clearCompleted,
    initQueueFilters
} from './modules/queue.js';
import {
    initForms,
    loadHistory,
    loadProfiles,
    saveProfileFromModal,
    deleteProfile
} from './modules/upload.js';
import {
    initChannelTabs,
    initOAuth,
    connectGoogle,
    openConfigOAuthModal,
    saveOAuthCredentialsFromModal,
    openBrowserLoginModal,
    copyLoginCommand,
    copyRedirectUri,
    updateConnectionHubStatus,
    loadAccounts,
    deleteAccount,
    addAccount,
    openAddAccountModal,
    closeAddAccountModal,
    loadChannels,
    deleteChannel,
    saveChannelFromModal,
    loadTemplates,
    deleteTemplate,
    saveTemplateFromModal,
    loadBatches,
    saveYouTubeApiKey,
    loadYouTubeChannels,
    searchYouTubeVideos
} from './modules/channels.js';
import {
    initSupabase,
    initSupabasePanel,
    syncToSupabase,
    loadSupabaseStats,
    loadSupabaseProfile,
    requestSupabaseSync,
    uploadToSupabaseStorage
} from './modules/supabase.js';

/**
 * Global Polling Orchestrator
 */
function refreshAll() {
    if (state.currentPage === 'dashboard') loadDashboard();
    if (state.currentPage === 'queue') loadQueue();
    if (state.currentPage === 'history') loadHistory();
}

function handlePageChange(page) {
    if (page === 'dashboard') loadDashboard();
    if (page === 'queue') loadQueue();
    if (page === 'history') loadHistory();
    if (page === 'profiles') loadProfiles();
    if (page === 'channels') {
        loadAccounts();
        loadChannels();
        loadTemplates();
        loadBatches();
    }
}

/**
 * Handle 401 Session Expiry
 */
setUnauthorizedHandler(() => {
    state.stopPolling();
    showAuthScreen('login');
    showAuthAlert('Your session has expired. Please sign in again.', 'error');
    showToast('Session expired. Please log in.', 'warning');
});

/**
 * Bind functions to Window for inline HTML onclick attributes & template strings
 */
Object.assign(window, {
    // Navigation & Auth
    navigateTo,
    logout,
    showAuthModal,
    showAuthScreen,
    setAuthMode,
    togglePasswordVisibility,
    closeModal,
    openModal,

    // Queue & Jobs
    retryJob,
    cancelJob,
    showJobDetails,
    clearCompleted,

    // Profiles
    deleteProfile,
    saveProfileFromModal,

    // Channels, Accounts & Templates
    connectGoogle,
    openConfigOAuthModal,
    saveOAuthCredentialsFromModal,
    openBrowserLoginModal,
    copyLoginCommand,
    copyRedirectUri,
    updateConnectionHubStatus,
    loadAccounts,
    deleteAccount,
    addAccount,
    openAddAccountModal,
    closeAddAccountModal,
    deleteChannel,
    saveChannelFromModal,
    deleteTemplate,
    saveTemplateFromModal,
    saveYouTubeApiKey,
    loadYouTubeChannels,
    searchYouTubeVideos,

    // Supabase
    syncToSupabase,
    loadSupabaseStats,
    requestSupabaseSync,
    uploadToSupabaseStorage
});

/**
 * Application Bootstrap
 */
document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Real-Time WebSockets
    initSocket();

    // 2. Initialize Navigation Router
    initNavigation(handlePageChange);

    // 3. Initialize Forms, Inputs & Filters
    initForms();
    initQueueFilters();
    initChannelTabs();
    initOAuth();
    initSupabase();
    initSupabasePanel();

    // 4. Initialize Auth Interactions
    initAuthHandlers(
        // On Login Success:
        () => {
            loadSupabaseProfile();
            loadDashboard();
            state.startPolling(refreshAll, 5000);
        },
        // On Logout:
        () => {
            state.stopPolling();
        }
    );

    // Refresh button global sync
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            refreshAll();
            showToast('Console data refreshed', 'info');
        });
    }

    // 5. Check Initial Authentication Session
    if (!state.authToken) {
        showAuthScreen(state.authMode);
    } else {
        checkAuthUser().then(isValid => {
            if (isValid) {
                hideAuthScreen();
                loadSupabaseProfile();
                loadDashboard();
                state.startPolling(refreshAll, 5000);
            } else {
                showAuthScreen('login');
            }
        });
    }
});
