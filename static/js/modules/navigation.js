/**
 * YouTube Uploader Pro - Single Page Application Navigation
 * Handles route switching, sidebar responsiveness, mobile drawer, and active view state.
 */

import { PAGE_TITLES, PAGE_DOM_MAP } from './constants.js';
import { state } from './state.js';

let pageChangeHandler = null;

export function setPageChangeHandler(handler) {
    pageChangeHandler = handler;
}

export function navigateTo(page) {
    if (!PAGE_DOM_MAP[page]) return;

    state.currentPage = page;

    // Update Navigation links
    document.querySelectorAll('.nav-item').forEach(item => {
        const isActive = item.dataset.page === page;
        item.classList.toggle('active', isActive);
        item.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    // Hide all sections and show active section
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.add('hidden');
    });

    // Reset channel sub-tabs active state if navigating away
    if (page !== 'channels') {
        document.querySelectorAll('#channelTabs .tab').forEach(t => t.classList.remove('active'));
    }

    const targetId = PAGE_DOM_MAP[page];
    const targetSection = document.getElementById(targetId);
    if (targetSection) {
        targetSection.classList.remove('hidden');
    }

    // Update Topbar Page Title
    const titleEl = document.getElementById('pageTitle');
    if (titleEl) {
        titleEl.textContent = PAGE_TITLES[page] || page;
    }

    // Close Mobile Navigation Drawer
    closeMobileNav();

    // Trigger page-specific data fetchers
    if (typeof pageChangeHandler === 'function') {
        pageChangeHandler(page);
    }
}

export function closeMobileNav() {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    if (sidebar) sidebar.classList.remove('open');
    if (backdrop) backdrop.classList.remove('active');
}

export function toggleMobileNav() {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    if (!sidebar) return;

    const isOpen = sidebar.classList.toggle('open');
    if (backdrop) {
        backdrop.classList.toggle('active', isOpen);
    }
}

export function initNavigation(onPageChange) {
    if (onPageChange) {
        setPageChangeHandler(onPageChange);
    }

    // Nav Item Click Handlers
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const page = item.dataset.page;
            if (page) navigateTo(page);
        });
    });

    // Sidebar Toggles
    const sidebarToggle = document.getElementById('sidebarToggle');
    const topbarToggle = document.getElementById('topbarToggle');
    const backdrop = document.getElementById('sidebarBackdrop');

    if (sidebarToggle) sidebarToggle.addEventListener('click', toggleMobileNav);
    if (topbarToggle) topbarToggle.addEventListener('click', toggleMobileNav);
    if (backdrop) backdrop.addEventListener('click', closeMobileNav);

    // Quick New Upload header button
    const newUploadBtn = document.getElementById('newUploadBtn');
    if (newUploadBtn) {
        newUploadBtn.addEventListener('click', () => navigateTo('upload'));
    }
}
