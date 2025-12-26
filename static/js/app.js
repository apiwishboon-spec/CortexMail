/**
 * AI Email Auto-Reply - Frontend Application
 * Handles login, dashboard, and API communication
 */

// ============================================
// Utility Functions
// ============================================

const API_BASE = '';

async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            credentials: 'include'
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Request failed');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function formatDate(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// ============================================
// Login Page Logic
// ============================================

if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
    const loginForm = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const loginButton = document.getElementById('loginButton');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');

    // Email validation
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    // Show error
    function showError(message) {
        errorMessage.textContent = message;
        errorAlert.classList.add('active');

        setTimeout(() => {
            errorAlert.classList.remove('active');
        }, 5000);
    }

    // Hide error
    function hideError() {
        errorAlert.classList.remove('active');
    }

    // Form submission
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError();

        const email = emailInput.value.trim();
        const password = passwordInput.value;

        // Validate
        if (!validateEmail(email)) {
            showError('Please enter a valid email address');
            return;
        }

        if (!password) {
            showError('Please enter your app password');
            return;
        }

        // Show loading
        loadingOverlay.classList.add('active');
        loginButton.disabled = true;

        try {
            const response = await apiCall('/api/login', {
                method: 'POST',
                body: JSON.stringify({ email, password })
            });

            if (response.success) {
                // Redirect to dashboard
                window.location.href = '/dashboard';
            } else {
                showError(response.message || 'Login failed');
            }
        } catch (error) {
            showError(error.message || 'Connection failed. Please check your credentials.');
        } finally {
            loadingOverlay.classList.remove('active');
            loginButton.disabled = false;
        }
    });

    // Input validation feedback
    emailInput.addEventListener('blur', () => {
        const email = emailInput.value.trim();
        if (email && !validateEmail(email)) {
            emailInput.style.borderColor = 'var(--error-color)';
        } else {
            emailInput.style.borderColor = '';
        }
    });
}

// ============================================
// Dashboard Page Logic
// ============================================

if (window.location.pathname === '/dashboard' || window.location.pathname === '/dashboard.html') {
    const userEmail = document.getElementById('userEmail');
    const connectionStatus = document.getElementById('connectionStatus');
    const processedCount = document.getElementById('processedCount');
    const autoreplyToggle = document.getElementById('autoreplyToggle');
    const autoreplyLabel = document.getElementById('autoreplyLabel');
    const refreshButton = document.getElementById('refreshButton');
    const checkNowButton = document.getElementById('checkNowButton');
    const logoutButton = document.getElementById('logoutButton');
    const emailsTableBody = document.getElementById('emailsTableBody');
    const emailCount = document.getElementById('emailCount');

    let statusInterval;

    // Load initial status
    async function loadStatus() {
        try {
            const data = await apiCall('/api/status');

            // Update UI
            userEmail.textContent = data.email || 'Unknown';
            processedCount.textContent = data.processed_count || 0;

            // Connection status
            if (data.connected) {
                connectionStatus.innerHTML = `
                    <span class="status-dot status-dot-connected"></span>
                    Connected
                `;
            } else if (data.message && data.message.includes('re-authentication')) {
                connectionStatus.innerHTML = `
                    <span class="status-dot status-dot-warning" title="${data.message}"></span>
                    Re-authentication Required
                `;
            } else {
                connectionStatus.innerHTML = `
                    <span class="status-dot status-dot-disconnected"></span>
                    Disconnected
                `;
            }

            // Auto-reply status
            autoreplyToggle.checked = data.autoreply_enabled || false;
            autoreplyLabel.textContent = data.autoreply_enabled ? 'Enabled' : 'Disabled';
            autoreplyLabel.style.color = data.autoreply_enabled ? 'var(--success-color)' : 'var(--text-secondary)';

        } catch (error) {
            console.error('Failed to load status:', error);
            // Redirect to login ONLY if we are truly not logged in
            if (error.message && error.message.includes('Not logged in')) {
                window.location.href = '/';
            } else {
                connectionStatus.innerHTML = `
                    <span class="status-dot status-dot-disconnected"></span>
                    Disconnected
                `;
            }
        }
    }

    // Load recent emails
    async function loadRecentEmails() {
        try {
            const data = await apiCall('/api/recent-emails?limit=20');

            if (data.success && data.emails.length > 0) {
                emailCount.textContent = `${data.emails.length} emails`;

                emailsTableBody.innerHTML = data.emails.map(email => `
                    <tr>
                        <td>
                            <div style="font-weight: 600; color: var(--text-primary);">${escapeHtml(email.sender)}</div>
                        </td>
                        <td>
                            <div style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                ${escapeHtml(email.subject)}
                            </div>
                        </td>
                        <td>
                            <span style="
                                display: inline-block;
                                padding: 0.25rem 0.625rem;
                                background-color: var(--bg-secondary);
                                color: var(--text-secondary);
                                border-radius: var(--radius-full);
                                font-size: 0.75rem;
                                font-weight: 600;
                            ">
                                ${capitalizeFirst(email.intent)}
                            </span>
                        </td>
                        <td>
                            <span style="
                                display: inline-block;
                                padding: 0.25rem 0.625rem;
                                background-color: ${getToneColor(email.tone)};
                                color: ${getToneTextColor(email.tone)};
                                border-radius: var(--radius-full);
                                font-size: 0.75rem;
                                font-weight: 600;
                            ">
                                ${capitalizeFirst(email.tone)}
                            </span>
                        </td>
                        <td style="color: var(--text-secondary);">
                            ${formatDate(email.timestamp)}
                        </td>
                    </tr>
                `).join('');
            } else {
                emailCount.textContent = '0 emails';
                emailsTableBody.innerHTML = `
                    <tr class="empty-state">
                        <td colspan="5">
                            <div class="empty-state-content">
                                <svg class="empty-state-icon" viewBox="0 0 20 20" fill="currentColor">
                                    <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
                                    <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
                                </svg>
                                <p class="empty-state-text">No emails processed yet</p>
                                <p class="empty-state-subtext">Enable auto-reply to start processing incoming emails</p>
                            </div>
                        </td>
                    </tr>
                `;
            }
        } catch (error) {
            console.error('Failed to load emails:', error);
        }
    }

    // Helper functions
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function getToneColor(tone) {
        const colors = {
            'formal': '#ede9fe',
            'friendly': '#dbeafe',
            'professional': '#f3f4f6',
            'casual': '#fef3c7'
        };
        return colors[tone] || colors['professional'];
    }

    function getToneTextColor(tone) {
        const colors = {
            'formal': '#5b21b6',
            'friendly': '#1e40af',
            'professional': '#374151',
            'casual': '#92400e'
        };
        return colors[tone] || colors['professional'];
    }

    // Toggle auto-reply
    autoreplyToggle.addEventListener('change', async () => {
        const enabled = autoreplyToggle.checked;

        try {
            const data = await apiCall('/api/toggle-autoreply', {
                method: 'POST',
                body: JSON.stringify({ enabled })
            });

            if (data.success) {
                autoreplyLabel.textContent = enabled ? 'Enabled' : 'Disabled';
                autoreplyLabel.style.color = enabled ? 'var(--success-color)' : 'var(--text-secondary)';
                showToast(`Auto-reply ${enabled ? 'enabled' : 'disabled'}`, 'success');
            }
        } catch (error) {
            showToast('Failed to toggle auto-reply', 'error');
            autoreplyToggle.checked = !enabled; // Revert
        }
    });

    // Refresh status
    refreshButton.addEventListener('click', async () => {
        refreshButton.disabled = true;
        refreshButton.innerHTML = `
            <div class="spinner" style="width: 18px; height: 18px; border-width: 2px;"></div>
            Refreshing...
        `;

        await loadStatus();
        await loadRecentEmails();

        refreshButton.disabled = false;
        refreshButton.innerHTML = `
            <svg class="btn-icon-left" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
            </svg>
            Refresh Status
        `;

        showToast('Status refreshed', 'success');
    });

    // Check emails now
    checkNowButton.addEventListener('click', async () => {
        checkNowButton.disabled = true;
        checkNowButton.innerHTML = `
            <div class="spinner" style="width: 18px; height: 18px; border-width: 2px;"></div>
            Checking...
        `;

        try {
            const data = await apiCall('/api/check-now', {
                method: 'POST'
            });

            if (data.success) {
                showToast(`Found ${data.new_emails} new emails`, 'success');
                await loadRecentEmails();
            }
        } catch (error) {
            showToast('Failed to check emails', 'error');
        } finally {
            checkNowButton.disabled = false;
            checkNowButton.innerHTML = `
                <svg class="btn-icon-left" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
                    <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
                </svg>
                Check Emails Now
            `;
        }
    });

    // Logout
    logoutButton.addEventListener('click', async () => {
        try {
            await apiCall('/api/logout', {
                method: 'POST'
            });
            window.location.href = '/';
        } catch (error) {
            console.error('Logout failed:', error);
            window.location.href = '/';
        }
    });

    // Initial load
    loadStatus();
    loadRecentEmails();

    // Auto-refresh every 10 seconds
    statusInterval = setInterval(() => {
        loadStatus();
        loadRecentEmails();
    }, 10000);

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (statusInterval) {
            clearInterval(statusInterval);
        }
    });
}
