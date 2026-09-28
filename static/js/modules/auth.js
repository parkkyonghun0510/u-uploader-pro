/**
 * YouTube Uploader Pro - Authentication Controller
 * Manages Supabase Auth, JWT storage, Login/Signup/Forgot modal flows, and session validation.
 */

import { API_BASE } from './constants.js';
import { state } from './state.js';
import { _origFetch } from './api.js';
import { showToast } from './ui.js';

export function updateUserBadge(data) {
    const badge = document.getElementById('userBadge');
    const nameEl = document.getElementById('userName');
    if (!badge || !nameEl) return;

    if (data) {
        const name = (data.profile && data.profile.display_name) ||
                     data.display_name ||
                     (data.user && data.user.email) ||
                     data.email || 'Studio Operator';
        nameEl.textContent = name;
        badge.style.display = 'inline-flex';
        state.currentUser = data;
    } else {
        badge.style.display = 'none';
        nameEl.textContent = '';
        state.currentUser = null;
    }
}

export async function checkAuthUser() {
    if (!state.authToken) {
        updateUserBadge(null);
        return false;
    }
    try {
        const r = await _origFetch(`${API_BASE}/api/auth/me`, {
            headers: { Authorization: `Bearer ${state.authToken}` }
        });
        if (r.ok) {
            const data = await r.json();
            updateUserBadge(data);
            return true;
        } else if (r.status === 401) {
            state.authToken = null;
            updateUserBadge(null);
            showAuthScreen('login');
            return false;
        }
    } catch (e) {
        console.error('Failed to verify authentication session:', e);
    }
    return false;
}

export function showAuthScreen(mode = 'login') {
    state.stopPolling();
    const authScreen = document.getElementById('authScreen');
    const appEl = document.getElementById('app');
    if (authScreen) authScreen.style.display = 'flex';
    if (appEl) appEl.style.display = 'none';
    setAuthMode(mode);
}

export function hideAuthScreen() {
    const authScreen = document.getElementById('authScreen');
    const appEl = document.getElementById('app');
    if (authScreen) authScreen.style.display = 'none';
    if (appEl) appEl.style.display = 'flex';
}

export function setAuthMode(mode, preserveAlert = false) {
    state.authMode = mode;
    if (!preserveAlert) hideAuthAlert();

    const tabSignIn = document.getElementById('tabSignIn');
    const tabSignUp = document.getElementById('tabSignUp');
    const nameGroup = document.getElementById('authDisplayNameGroup');
    const pwdGroup = document.getElementById('authPasswordGroup');
    const pwdHint = document.getElementById('passwordHint');
    const forgotLink = document.getElementById('authForgotLink');
    const submitText = document.getElementById('authSubmitText');
    const submitIcon = document.getElementById('authSubmitIcon');
    const promptText = document.getElementById('authPromptText');
    const switchBtn = document.getElementById('authSwitchBtn');

    if (mode === 'signup') {
        if (tabSignIn) {
            tabSignIn.classList.remove('active');
            tabSignIn.setAttribute('aria-selected', 'false');
        }
        if (tabSignUp) {
            tabSignUp.classList.add('active');
            tabSignUp.setAttribute('aria-selected', 'true');
        }
        if (nameGroup) nameGroup.style.display = 'block';
        if (pwdGroup) pwdGroup.style.display = 'block';
        if (pwdHint) pwdHint.style.display = 'inline';
        if (forgotLink) forgotLink.style.display = 'none';
        if (submitText) submitText.textContent = 'Create Account';
        if (submitIcon) submitIcon.className = 'fas fa-user-plus';
        if (promptText) promptText.textContent = 'Already have an account?';
        if (switchBtn) switchBtn.textContent = 'Sign in here';
    } else if (mode === 'forgot') {
        if (tabSignIn) {
            tabSignIn.classList.remove('active');
            tabSignIn.setAttribute('aria-selected', 'false');
        }
        if (tabSignUp) {
            tabSignUp.classList.remove('active');
            tabSignUp.setAttribute('aria-selected', 'false');
        }
        if (nameGroup) nameGroup.style.display = 'none';
        if (pwdGroup) pwdGroup.style.display = 'none';
        if (pwdHint) pwdHint.style.display = 'none';
        if (forgotLink) forgotLink.style.display = 'none';
        if (submitText) submitText.textContent = 'Send Reset Instructions';
        if (submitIcon) submitIcon.className = 'fas fa-paper-plane';
        if (promptText) promptText.textContent = 'Remembered your password?';
        if (switchBtn) switchBtn.textContent = 'Back to Sign In';
    } else {
        if (tabSignIn) {
            tabSignIn.classList.add('active');
            tabSignIn.setAttribute('aria-selected', 'true');
        }
        if (tabSignUp) {
            tabSignUp.classList.remove('active');
            tabSignUp.setAttribute('aria-selected', 'false');
        }
        if (nameGroup) nameGroup.style.display = 'none';
        if (pwdGroup) pwdGroup.style.display = 'block';
        if (pwdHint) pwdHint.style.display = 'none';
        if (forgotLink) forgotLink.style.display = 'inline';
        if (submitText) submitText.textContent = 'Sign In';
        if (submitIcon) submitIcon.className = 'fas fa-arrow-right';
        if (promptText) promptText.textContent = "Don't have an account yet?";
        if (switchBtn) switchBtn.textContent = 'Create an account';
    }
}

export function showAuthAlert(message, type = 'error') {
    const alertEl = document.getElementById('authAlert');
    const msgEl = document.getElementById('authAlertMessage');
    const iconEl = document.getElementById('authAlertIcon');
    const cardEl = document.getElementById('authCard');
    if (!alertEl || !msgEl) return;

    alertEl.className = 'auth-alert ' + type;
    msgEl.textContent = message;
    if (iconEl) {
        iconEl.className = type === 'success'
            ? 'auth-alert-icon fas fa-check-circle'
            : 'auth-alert-icon fas fa-exclamation-circle';
    }
    alertEl.style.display = 'flex';

    if (type === 'error' && cardEl) {
        cardEl.classList.remove('shake');
        void cardEl.offsetWidth; // Trigger reflow for CSS keyframe animation
        cardEl.classList.add('shake');
    }
}

export function hideAuthAlert() {
    const alertEl = document.getElementById('authAlert');
    if (alertEl) alertEl.style.display = 'none';
}

export function togglePasswordVisibility() {
    const pwdInput = document.getElementById('authPassword');
    const icon = document.getElementById('togglePasswordIcon');
    if (!pwdInput || !icon) return;

    if (pwdInput.type === 'password') {
        pwdInput.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        pwdInput.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

export async function authRequest(mode, onSuccessCallback) {
    const emailInput = document.getElementById('authEmail');
    const pwdInput = document.getElementById('authPassword');
    const nameInput = document.getElementById('authDisplayName');
    const submitBtn = document.getElementById('authSubmitBtn');
    const submitText = document.getElementById('authSubmitText');
    const submitIcon = document.getElementById('authSubmitIcon');

    const email = emailInput ? emailInput.value.trim() : '';
    const password = pwdInput ? pwdInput.value : '';
    const displayName = nameInput ? nameInput.value.trim() : '';

    hideAuthAlert();

    if (!email) {
        showAuthAlert('Please enter your email address.', 'error');
        if (emailInput) emailInput.focus();
        return;
    }
    if (!email.includes('@') || !email.includes('.')) {
        showAuthAlert('Please enter a valid email address.', 'error');
        if (emailInput) emailInput.focus();
        return;
    }

    if (mode === 'forgot') {
        if (submitBtn) submitBtn.disabled = true;
        if (submitText) submitText.textContent = 'Sending...';
        if (submitIcon) submitIcon.className = 'fas fa-circle-notch fa-spin';

        try {
            const res = await _origFetch(`${API_BASE}/api/auth/forgot-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await res.json();
            if (!res.ok) {
                showAuthAlert(data.error || 'Failed to send reset email.', 'error');
                return;
            }
            setAuthMode('login', true);
            showAuthAlert(data.message || 'Check your inbox! Password reset instructions sent.', 'success');
        } catch (err) {
            showAuthAlert('Network error: ' + err.message, 'error');
        } finally {
            if (submitBtn) submitBtn.disabled = false;
            if (submitText) submitText.textContent = 'Send Reset Instructions';
            if (submitIcon) submitIcon.className = 'fas fa-paper-plane';
        }
        return;
    }

    if (!password) {
        showAuthAlert('Please enter your password.', 'error');
        if (pwdInput) pwdInput.focus();
        return;
    }
    if (password.length < 8) {
        showAuthAlert('Password must be at least 8 characters long.', 'error');
        if (pwdInput) pwdInput.focus();
        return;
    }

    if (submitBtn) submitBtn.disabled = true;
    if (submitText) submitText.textContent = mode === 'signup' ? 'Creating Account...' : 'Signing In...';
    if (submitIcon) submitIcon.className = 'fas fa-circle-notch fa-spin';

    try {
        const payload = { email, password };
        if (mode === 'signup' && displayName) {
            payload.display_name = displayName;
        }

        const endpoint = mode === 'signup' ? '/api/auth/signup' : '/api/auth/login';
        const res = await _origFetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            showAuthAlert(data.error || 'Authentication failed. Please verify your credentials.', 'error');
            return;
        }

        if (data.needs_email_confirm) {
            setAuthMode('login', true);
            showAuthAlert('Account created successfully! Please check your email to confirm your account, then sign in.', 'success');
            return;
        }

        if (data.access_token) {
            state.authToken = data.access_token;
            hideAuthScreen();
            showToast('Welcome to YouTube Uploader Pro!', 'success');
            await checkAuthUser();
            if (typeof onSuccessCallback === 'function') {
                onSuccessCallback();
            }
        } else {
            showAuthAlert('Unexpected authentication response. Please try again.', 'error');
        }
    } catch (err) {
        showAuthAlert('Connection error: ' + err.message, 'error');
    } finally {
        if (submitBtn) submitBtn.disabled = false;
        if (submitText) submitText.textContent = mode === 'signup' ? 'Create Account' : 'Sign In';
        if (submitIcon) submitIcon.className = mode === 'signup' ? 'fas fa-user-plus' : 'fas fa-arrow-right';
    }
}

export function showAuthModal() {
    showAuthScreen('login');
}

export function logout(onLogoutCallback) {
    state.authToken = null;
    updateUserBadge(null);
    state.stopPolling();
    _origFetch(`${API_BASE}/api/auth/logout`, { method: 'POST' }).catch(() => {});
    showToast('Signed out successfully', 'info');
    showAuthScreen('login');
    if (typeof onLogoutCallback === 'function') {
        onLogoutCallback();
    }
}

export function initAuthHandlers(onLoginSuccess, onLogout) {
    const tabSignIn = document.getElementById('tabSignIn');
    const tabSignUp = document.getElementById('tabSignUp');
    const authSwitchBtn = document.getElementById('authSwitchBtn');
    const authForgotLink = document.getElementById('authForgotLink');
    const authForm = document.getElementById('authForm');
    const btnTogglePassword = document.getElementById('btnTogglePassword');
    const logoutBtn = document.getElementById('logoutBtn');

    if (tabSignIn) tabSignIn.addEventListener('click', () => setAuthMode('login'));
    if (tabSignUp) tabSignUp.addEventListener('click', () => setAuthMode('signup'));

    if (authForgotLink) {
        authForgotLink.addEventListener('click', (e) => {
            e.preventDefault();
            setAuthMode('forgot');
        });
    }

    if (authSwitchBtn) {
        authSwitchBtn.addEventListener('click', () => {
            if (state.authMode === 'forgot') {
                setAuthMode('login');
            } else {
                setAuthMode(state.authMode === 'login' ? 'signup' : 'login');
            }
        });
    }

    if (btnTogglePassword) {
        btnTogglePassword.addEventListener('click', togglePasswordVisibility);
    }

    if (authForm) {
        authForm.addEventListener('submit', (e) => {
            e.preventDefault();
            authRequest(state.authMode, onLoginSuccess);
        });
    }

    if (logoutBtn) {
        logoutBtn.onclick = () => logout(onLogout);
    }
}
