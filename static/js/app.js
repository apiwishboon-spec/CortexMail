/**
 * CortexMail - Frontend Application
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
    toast.className = `toast show align-items-center text-dark border-4 border-dark rounded-0 mb-3 brutal-card`;

    // Set background color based on type
    if (type === 'success') toast.classList.add('bg-primary');
    else if (type === 'error') toast.classList.add('bg-danger');
    else toast.classList.add('bg-warning');

    toast.role = 'alert';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body fw-bold text-uppercase">
                ${message}
            </div>
            <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 500);
    }, 4000);
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
        errorAlert.classList.remove('d-none');

        setTimeout(() => {
            errorAlert.classList.add('d-none');
        }, 5000);
    }

    // Hide error
    function hideError() {
        errorAlert.classList.add('d-none');
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
        loadingOverlay.classList.remove('d-none');
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
            loadingOverlay.classList.add('d-none');
            loginButton.disabled = false;
        }
    });

    // Input validation feedback
    emailInput.addEventListener('blur', () => {
        const email = emailInput.value.trim();
        if (email && !validateEmail(email)) {
            emailInput.classList.add('is-invalid');
        } else {
            emailInput.classList.remove('is-invalid');
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
                    <i class="bi bi-patch-check-fill text-dark me-2"></i>
                    Connected
                `;
                connectionStatus.parentElement.parentElement.parentElement.querySelector('.bg-primary').classList.replace('bg-primary', 'bg-primary');
            } else if (data.message && data.message.includes('re-authentication')) {
                connectionStatus.innerHTML = `
                    <i class="bi bi-exclamation-octagon-fill text-dark me-2"></i>
                    Auth Needed
                `;
                connectionStatus.classList.add('text-danger');
            } else {
                connectionStatus.innerHTML = `
                    <i class="bi bi-x-circle-fill text-dark me-2"></i>
                    Disconnected
                `;
            }

            // Auto-reply status
            autoreplyToggle.checked = data.autoreply_enabled || false;
            autoreplyLabel.textContent = data.autoreply_enabled ? 'ON' : 'OFF';
            autoreplyLabel.classList.toggle('text-primary', data.autoreply_enabled);

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
                        <td class="ps-4">
                            <div class="fw-bold text-dark">${escapeHtml(email.sender)}</div>
                        </td>
                        <td>
                            <div class="text-truncate" style="max-width: 250px;">
                                ${escapeHtml(email.subject)}
                            </div>
                        </td>
                        <td>
                            <span class="badge border border-dark border-2 text-dark bg-info text-uppercase">
                                ${email.intent}
                            </span>
                        </td>
                        <td>
                            <span class="badge border border-dark border-2 text-dark text-uppercase" style="background-color: ${getToneColor(email.tone)}">
                                ${email.tone}
                            </span>
                        </td>
                        <td class="pe-4 fw-bold">
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
            'formal': '#daff00',
            'friendly': '#0047ff',
            'professional': '#ff6b00',
            'casual': '#ffffff'
        };
        return colors[tone] || '#ffffff';
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
                autoreplyLabel.textContent = enabled ? 'ON' : 'OFF';
                autoreplyLabel.classList.toggle('text-primary', enabled);
                showToast(`Auto-Monitoring ${enabled ? 'Started' : 'Stopped'}`, 'success');
            }
        } catch (error) {
            showToast('Toggle Failed', 'error');
            autoreplyToggle.checked = !enabled; // Revert
        }
    });

    // Refresh status
    refreshButton.addEventListener('click', async () => {
        refreshButton.disabled = true;
        refreshButton.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Syncing...
        `;

        await loadStatus();
        await loadRecentEmails();

        refreshButton.disabled = false;
        refreshButton.innerHTML = `
            <i class="bi bi-arrow-clockwise me-2"></i> Refresh dashboard
        `;

        showToast('Dashboard Synced', 'success');
    });

    // Check emails now
    checkNowButton.addEventListener('click', async () => {
        checkNowButton.disabled = true;
        checkNowButton.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Checking...
        `;

        try {
            const data = await apiCall('/api/check-now', {
                method: 'POST'
            });

            if (data.success) {
                showToast(`Action: ${data.new_emails} emails processed`, 'success');
                await loadRecentEmails();
            }
        } catch (error) {
            showToast('Search Failed', 'error');
        } finally {
            checkNowButton.disabled = false;
            checkNowButton.innerHTML = `
                <i class="bi bi-search me-2"></i> Check now
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
