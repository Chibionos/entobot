// Entobot Enterprise Dashboard - JavaScript

class EntobotDashboard {
    constructor() {
        this.ws = null;
        this.wsReconnectDelay = 1000;
        this.maxReconnectDelay = 30000;
        this.refreshInterval = 5000; // 5 seconds
        this.refreshTimer = null;
        this.demoMode = true;

        this.init();
    }

    init() {
        console.log('Initializing Entobot Dashboard...');

        // Setup event listeners
        this.setupEventListeners();

        // Connect WebSocket
        this.connectWebSocket();

        // Start auto-refresh
        this.startAutoRefresh();

        // Initial data load
        this.refreshAll();

        console.log('Dashboard initialized');
    }

    setupEventListeners() {
        // Generate QR button
        document.getElementById('generateQR').addEventListener('click', () => {
            this.generateQRCode();
        });

        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshAll();
        });

        // Demo mode toggle
        document.getElementById('demoToggle').addEventListener('click', () => {
            this.toggleDemoMode();
        });

        // Help button
        document.getElementById('helpBtn').addEventListener('click', () => {
            this.showHelp();
        });

        // Modal close buttons
        document.getElementById('closeQR').addEventListener('click', () => {
            this.closeQRModal();
        });

        document.getElementById('closeHelp').addEventListener('click', () => {
            this.closeHelpModal();
        });

        // Close modals on background click
        document.getElementById('qrModal').addEventListener('click', (e) => {
            if (e.target.id === 'qrModal') {
                this.closeQRModal();
            }
        });

        document.getElementById('helpModal').addEventListener('click', (e) => {
            if (e.target.id === 'helpModal') {
                this.closeHelpModal();
            }
        });

        // Export audit log
        document.getElementById('exportAuditBtn').addEventListener('click', () => {
            this.exportAuditLog();
        });

        // ESC key closes modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeQRModal();
                this.closeHelpModal();
            }
        });
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;

        console.log('Connecting to WebSocket:', wsUrl);
        this.updateConnectionStatus('connecting');

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus('connected');
                this.wsReconnectDelay = 1000; // Reset reconnect delay
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (e) {
                    console.error('Error parsing WebSocket message:', e);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('error');
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus('disconnected');
                this.scheduleReconnect();
            };
        } catch (e) {
            console.error('Error creating WebSocket:', e);
            this.updateConnectionStatus('error');
            this.scheduleReconnect();
        }
    }

    scheduleReconnect() {
        console.log(`Reconnecting in ${this.wsReconnectDelay}ms...`);
        setTimeout(() => {
            this.connectWebSocket();
            // Exponential backoff
            this.wsReconnectDelay = Math.min(this.wsReconnectDelay * 2, this.maxReconnectDelay);
        }, this.wsReconnectDelay);
    }

    handleWebSocketMessage(data) {
        console.log('WebSocket message:', data);

        switch (data.type) {
            case 'connected':
                console.log('Dashboard WebSocket connected');
                break;

            case 'activity_update':
                if (data.activity) {
                    this.addActivityItem(data.activity);
                }
                break;

            case 'qr_generated':
                this.showNotification('QR Code generated', 'success');
                break;

            case 'device_connected':
                this.showNotification(`Device connected: ${data.device_name}`, 'success');
                this.refreshAll();
                break;

            case 'device_disconnected':
                this.showNotification(`Device disconnected: ${data.device_name}`, 'info');
                this.refreshAll();
                break;

            case 'pong':
                // Heartbeat response
                break;

            default:
                console.log('Unknown message type:', data.type);
        }
    }

    updateConnectionStatus(status) {
        const indicator = document.querySelector('.connection-indicator');
        const text = document.getElementById('connectionText');

        indicator.className = 'connection-indicator';

        switch (status) {
            case 'connected':
                indicator.classList.add('connected');
                text.textContent = 'Connected';
                break;
            case 'connecting':
                text.textContent = 'Connecting...';
                break;
            case 'disconnected':
                indicator.classList.add('disconnected');
                text.textContent = 'Disconnected';
                break;
            case 'error':
                indicator.classList.add('disconnected');
                text.textContent = 'Connection Error';
                break;
        }
    }

    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        this.refreshTimer = setInterval(() => {
            this.refreshAll();
        }, this.refreshInterval);
    }

    async refreshAll() {
        console.log('Refreshing dashboard data...');
        await Promise.all([
            this.updateStatus(),
            this.updateDevices(),
            this.updateActivity(),
            this.updateAuditLog()
        ]);
    }

    async updateStatus() {
        try {
            const response = await fetch('/api/dashboard/status');
            const data = await response.json();

            // Update status cards
            document.getElementById('systemStatus').textContent =
                data.status.charAt(0).toUpperCase() + data.status.slice(1);
            document.getElementById('deviceCount').textContent = data.devices;
            document.getElementById('sessionCount').textContent = data.sessions;
            document.getElementById('messageCount').textContent = data.messages;

            const uptime = data.uptime;
            document.getElementById('uptime').textContent =
                `${uptime.hours}h ${uptime.minutes}m`;

            this.demoMode = data.demo_mode;
        } catch (e) {
            console.error('Error updating status:', e);
        }
    }

    async updateDevices() {
        try {
            const response = await fetch('/api/dashboard/devices');
            const devices = await response.json();

            const deviceList = document.getElementById('deviceList');
            const deviceBadge = document.getElementById('deviceBadge');

            deviceBadge.textContent = devices.length;

            if (devices.length === 0) {
                deviceList.innerHTML = '<div class="loading">No devices connected</div>';
                return;
            }

            deviceList.innerHTML = devices.map(device => `
                <div class="device-item">
                    <div class="device-icon">📱</div>
                    <div class="device-info">
                        <div class="device-name">${this.escapeHtml(device.name)}</div>
                        <div class="device-platform">${this.escapeHtml(device.platform || 'Unknown')}</div>
                    </div>
                    <div class="device-status">
                        <span class="status-dot"></span>
                        <span style="font-size: 12px; color: var(--text-secondary);">Active</span>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            console.error('Error updating devices:', e);
            document.getElementById('deviceList').innerHTML =
                '<div class="loading">Error loading devices</div>';
        }
    }

    async updateActivity() {
        try {
            const response = await fetch('/api/dashboard/activity');
            const activities = await response.json();

            const activityFeed = document.getElementById('activityFeed');

            if (activities.length === 0) {
                activityFeed.innerHTML = '<div class="loading">No recent activity</div>';
                return;
            }

            activityFeed.innerHTML = activities.slice(0, 20).map(activity =>
                this.createActivityItemHTML(activity)
            ).join('');
        } catch (e) {
            console.error('Error updating activity:', e);
            document.getElementById('activityFeed').innerHTML =
                '<div class="loading">Error loading activity</div>';
        }
    }

    addActivityItem(activity) {
        const activityFeed = document.getElementById('activityFeed');

        // Remove "no activity" message if present
        const loading = activityFeed.querySelector('.loading');
        if (loading) {
            loading.remove();
        }

        // Add new activity at the top
        const itemHTML = this.createActivityItemHTML(activity);
        activityFeed.insertAdjacentHTML('afterbegin', itemHTML);

        // Keep only latest 20
        const items = activityFeed.querySelectorAll('.activity-item');
        if (items.length > 20) {
            items[items.length - 1].remove();
        }
    }

    createActivityItemHTML(activity) {
        const time = this.formatTime(activity.timestamp);
        return `
            <div class="activity-item ${activity.type}">
                <div class="activity-header">
                    <span class="activity-type">${activity.type.replace(/_/g, ' ')}</span>
                    <span class="activity-time">${time}</span>
                </div>
                <div class="activity-message">${this.escapeHtml(activity.message)}</div>
            </div>
        `;
    }

    async updateAuditLog() {
        try {
            const response = await fetch('/api/dashboard/audit');
            const events = await response.json();

            const auditLog = document.getElementById('auditLog');

            if (events.length === 0) {
                auditLog.innerHTML = '<div class="loading">No audit events</div>';
                return;
            }

            auditLog.innerHTML = events.slice(0, 30).map(event => `
                <div class="audit-item severity-${event.severity}">
                    <span class="audit-timestamp">${this.formatTime(event.timestamp)}</span>
                    <span class="audit-type">${event.type}</span>
                    <span class="audit-message">${this.escapeHtml(event.message)}</span>
                </div>
            `).join('');
        } catch (e) {
            console.error('Error updating audit log:', e);
            document.getElementById('auditLog').innerHTML =
                '<div class="loading">Error loading audit log</div>';
        }
    }

    async generateQRCode() {
        const modal = document.getElementById('qrModal');
        const loading = document.getElementById('qrLoading');
        const content = document.getElementById('qrContent');

        // Show modal
        modal.classList.add('active');
        loading.style.display = 'block';
        content.style.display = 'none';

        try {
            const response = await fetch('/api/dashboard/generate-qr', {
                method: 'POST'
            });
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Update QR code display
            document.getElementById('qrImage').src = data.qr_code;
            document.getElementById('qrSessionId').textContent = data.session_id;
            document.getElementById('qrWebsocketUrl').textContent = data.websocket_url;
            document.getElementById('qrExpiry').textContent = `${data.expires_in_minutes} minutes`;
            document.getElementById('qrValidUntil').textContent =
                this.formatDateTime(data.valid_until);

            // Show content
            loading.style.display = 'none';
            content.style.display = 'block';

            this.showNotification('QR Code generated successfully', 'success');
        } catch (e) {
            console.error('Error generating QR code:', e);
            loading.textContent = `Error: ${e.message}`;
            this.showNotification('Failed to generate QR code', 'error');
        }
    }

    closeQRModal() {
        document.getElementById('qrModal').classList.remove('active');
    }

    showHelp() {
        document.getElementById('helpModal').classList.add('active');
    }

    closeHelpModal() {
        document.getElementById('helpModal').classList.remove('active');
    }

    async toggleDemoMode() {
        this.demoMode = !this.demoMode;

        try {
            await fetch('/api/dashboard/demo-mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ enabled: this.demoMode })
            });

            document.getElementById('demoText').textContent =
                `Demo: ${this.demoMode ? 'ON' : 'OFF'}`;

            this.showNotification(
                `Demo mode ${this.demoMode ? 'enabled' : 'disabled'}`,
                'info'
            );

            // Refresh data
            this.refreshAll();
        } catch (e) {
            console.error('Error toggling demo mode:', e);
        }
    }

    exportAuditLog() {
        fetch('/api/dashboard/audit')
            .then(response => response.json())
            .then(events => {
                const text = events.map(e =>
                    `[${e.timestamp}] ${e.type} - ${e.message}`
                ).join('\n');

                const blob = new Blob([text], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `audit-log-${Date.now()}.txt`;
                a.click();
                URL.revokeObjectURL(url);

                this.showNotification('Audit log exported', 'success');
            })
            .catch(e => {
                console.error('Error exporting audit log:', e);
                this.showNotification('Failed to export audit log', 'error');
            });
    }

    showNotification(message, type = 'info') {
        // Simple notification (could be enhanced with a library)
        console.log(`[${type.toUpperCase()}] ${message}`);

        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 80px;
            right: 24px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: var(--shadow-lg);
            z-index: 1001;
            animation: slideIn 0.3s ease;
            max-width: 300px;
        `;

        // Add color based on type
        const colors = {
            success: 'var(--success)',
            error: 'var(--danger)',
            warning: 'var(--warning)',
            info: 'var(--info)'
        };
        toast.style.borderLeft = `4px solid ${colors[type] || colors.info}`;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    formatTime(timestamp) {
        if (!timestamp) return '';

        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        // Less than 1 minute
        if (diff < 60000) {
            return 'Just now';
        }

        // Less than 1 hour
        if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `${minutes}m ago`;
        }

        // Less than 24 hours
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours}h ago`;
        }

        // Show time
        return date.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatDateTime(timestamp) {
        if (!timestamp) return '-';
        const date = new Date(timestamp);
        return date.toLocaleString([], {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new EntobotDashboard();
});
