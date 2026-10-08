/**
 * Phase 3 Dashboard WebSocket Integration
 * Real-time metrics streaming and updates
 * Fecha: Oct 8, 2026
 */

class Phase3DashboardWebSocket {
    constructor(config = {}) {
        this.wsUrl = config.wsUrl || 'ws://localhost:8000/ws/phase3-monitoring';
        this.reconnectInterval = config.reconnectInterval || 3000;
        this.maxReconnectAttempts = config.maxReconnectAttempts || 5;
        this.reconnectAttempts = 0;
        this.ws = null;
        this.isConnected = false;
        this.metrics = this.initializeMetrics();
        this.eventHandlers = {};
        this.init();
    }

    init() {
        console.log('[Phase 3 Dashboard] Initializing WebSocket connection...');
        this.connect();
        this.setupEventListeners();
        this.startMetricsUpdateLoop();
    }

    connect() {
        try {
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = () => this.handleOpen();
            this.ws.onmessage = (event) => this.handleMessage(event);
            this.ws.onerror = (event) => this.handleError(event);
            this.ws.onclose = () => this.handleClose();
        } catch (error) {
            console.error('[WebSocket] Connection error:', error);
            this.scheduleReconnect();
        }
    }

    handleOpen() {
        console.log('[WebSocket] ✓ Connected to Phase 3 monitoring server');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.updateWSStatus(true);
        this.emit('connected');
        
        // Subscribe to metric streams
        this.sendMessage({
            type: 'SUBSCRIBE',
            channels: [
                'metrics:ml_accuracy',
                'metrics:error_rate',
                'metrics:throughput',
                'metrics:conversion',
                'metrics:personalization',
                'metrics:ab_tests',
                'events:checkpoint',
                'events:error',
                'alerts:critical'
            ]
        });
    }

    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.processMessage(data);
        } catch (error) {
            console.error('[WebSocket] Message parse error:', error);
        }
    }

    processMessage(data) {
        const { type, channel, payload, timestamp } = data;
        
        switch (type) {
            case 'METRIC_UPDATE':
                this.handleMetricUpdate(channel, payload, timestamp);
                break;
            case 'CHECKPOINT_EVENT':
                this.handleCheckpointEvent(payload, timestamp);
                break;
            case 'ERROR_EVENT':
                this.handleErrorEvent(payload, timestamp);
                break;
            case 'ALERT':
                this.handleAlert(payload, timestamp);
                break;
            default:
                console.log('[WebSocket] Unhandled message type:', type);
        }
    }

    handleMetricUpdate(channel, payload, timestamp) {
        const metricName = channel.split(':')[1];
        
        if (this.metrics.hasOwnProperty(metricName)) {
            const oldValue = this.metrics[metricName].value;
            this.metrics[metricName].value = payload.value;
            this.metrics[metricName].timestamp = timestamp;
            this.metrics[metricName].change = payload.value - oldValue;
            this.metrics[metricName].target = payload.target || this.metrics[metricName].target;
            
            console.log(`[Metric Update] ${metricName}: ${oldValue} → ${payload.value}`);
            this.updateMetricDisplay(metricName);
            this.emit('metric_updated', { metric: metricName, ...payload });
        }
    }

    handleCheckpointEvent(payload, timestamp) {
        const { checkpoint_id, status, metrics } = payload;
        
        console.log(`[Checkpoint] ${checkpoint_id}: ${status}`, metrics);
        
        // Update checkpoint UI
        this.updateCheckpointUI(checkpoint_id, status);
        
        // Add event to stream
        this.addEventToStream({
            type: status === 'completed' ? 'completed' : 'started',
            message: `Checkpoint ${checkpoint_id} ${status}`,
            timestamp,
            metrics
        });
        
        this.emit('checkpoint_event', { checkpoint_id, status, metrics });
    }

    handleErrorEvent(payload, timestamp) {
        const { error_type, severity, message, context } = payload;
        
        console.error(`[Error Event] ${severity}: ${message}`, context);
        
        // Add alert
        this.addAlert({
            type: severity,
            title: `${error_type} Error`,
            message,
            timestamp
        });
        
        this.addEventToStream({
            type: 'error',
            message,
            timestamp
        });
        
        this.emit('error_event', payload);
    }

    handleAlert(payload, timestamp) {
        const { level, title, message } = payload;
        
        console.log(`[Alert] ${level}: ${title}`);
        
        this.addAlert({
            type: level,
            title,
            message,
            timestamp
        });
        
        this.emit('alert', payload);
    }

    handleError(event) {
        console.error('[WebSocket] Connection error:', event);
        this.isConnected = false;
        this.updateWSStatus(false);
    }

    handleClose() {
        console.log('[WebSocket] Connection closed');
        this.isConnected = false;
        this.updateWSStatus(false);
        this.scheduleReconnect();
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectInterval * this.reconnectAttempts;
            console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => this.connect(), delay);
        } else {
            console.error('[WebSocket] Max reconnection attempts exceeded');
            this.emit('connection_failed');
        }
    }

    sendMessage(msg) {
        if (this.isConnected && this.ws) {
            this.ws.send(JSON.stringify(msg));
        } else {
            console.warn('[WebSocket] Not connected, message queued:', msg);
        }
    }

    // UI Update Methods
    updateMetricDisplay(metricName) {
        const metric = this.metrics[metricName];
        const element = document.querySelector(`[data-metric="${metricName}"]`);
        
        if (element) {
            // Update value
            const valueEl = element.querySelector('.metric-value');
            if (valueEl) {
                valueEl.textContent = metric.value.toFixed(metric.decimals);
            }
            
            // Update progress bar
            const progressEl = element.querySelector('.progress-fill');
            if (progressEl) {
                const percentage = Math.min((metric.value / metric.max) * 100, 100);
                progressEl.style.width = percentage + '%';
            }
            
            // Update status indicator
            const statusEl = element.querySelector('.metric-status');
            if (statusEl) {
                statusEl.classList.remove('warning', 'danger');
                if (metric.value < metric.warning_threshold) {
                    statusEl.classList.add('warning');
                }
                if (metric.value < metric.danger_threshold) {
                    statusEl.classList.add('danger');
                }
            }
        }
    }

    updateCheckpointUI(checkpointId, status) {
        const cpElement = document.querySelector(`[data-checkpoint="${checkpointId}"]`);
        
        if (cpElement) {
            const marker = cpElement.querySelector('.checkpoint-marker');
            
            marker.classList.remove('pending', 'active', 'completed');
            
            if (status === 'completed') {
                marker.classList.add('completed');
                marker.textContent = '✓';
            } else if (status === 'in_progress') {
                marker.classList.add('active');
                marker.textContent = '◐';
            }
        }
    }

    addEventToStream(event) {
        const eventStream = document.getElementById('eventStream');
        
        if (eventStream) {
            const eventEl = document.createElement('div');
            eventEl.className = `event-item ${event.type}`;
            
            const icons = {
                created: '●',
                started: '▶',
                completed: '✓',
                error: '✕'
            };
            
            const time = new Date(event.timestamp).toLocaleTimeString();
            
            eventEl.innerHTML = `
                <div class="event-icon">${icons[event.type] || '○'}</div>
                <div>
                    <div>${event.message}</div>
                    <div class="event-time">${time}</div>
                </div>
            `;
            
            eventStream.insertBefore(eventEl, eventStream.firstChild);
            
            // Keep only last 10 events
            while (eventStream.children.length > 10) {
                eventStream.removeChild(eventStream.lastChild);
            }
        }
    }

    addAlert(alert) {
        const alertsPanel = document.querySelector('[data-alerts-panel]');
        
        if (alertsPanel) {
            const alertEl = document.createElement('div');
            alertEl.className = `alert-item ${alert.type}`;
            
            const icons = {
                critical: '🚨',
                warning: '⚠',
                info: 'ℹ'
            };
            
            alertEl.innerHTML = `
                <div class="alert-icon">${icons[alert.type] || 'ℹ'}</div>
                <div>
                    <div class="alert-title">${alert.title}</div>
                    <div class="alert-message">${alert.message}</div>
                </div>
            `;
            
            alertsPanel.insertBefore(alertEl, alertsPanel.firstChild);
            
            // Keep only last 5 alerts
            while (alertsPanel.children.length > 5) {
                alertsPanel.removeChild(alertsPanel.lastChild);
            }
        }
    }

    updateWSStatus(connected) {
        const statusEl = document.getElementById('wsStatus');
        
        if (statusEl) {
            if (connected) {
                statusEl.textContent = '✓ LIVE';
                statusEl.style.color = 'var(--success)';
            } else {
                statusEl.textContent = '✕ DISCONNECTED';
                statusEl.style.color = 'var(--danger)';
            }
        }
    }

    // Event Emitter
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }

    emit(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => handler(data));
        }
    }

    // Metrics Initialization
    initializeMetrics() {
        return {
            ml_accuracy: {
                value: 77.1,
                target: 78,
                max: 100,
                decimals: 1,
                warning_threshold: 76,
                danger_threshold: 75,
                timestamp: new Date().toISOString(),
                change: 0
            },
            error_rate: {
                value: 0.065,
                target: 0.08,
                max: 0.2,
                decimals: 3,
                warning_threshold: 0.09,
                danger_threshold: 0.12,
                timestamp: new Date().toISOString(),
                change: 0
            },
            throughput: {
                value: 38.2,
                target: 42,
                max: 50,
                decimals: 1,
                warning_threshold: 30,
                danger_threshold: 20,
                timestamp: new Date().toISOString(),
                change: 0
            },
            conversion: {
                value: 4.02,
                target: 4.2,
                max: 6,
                decimals: 2,
                warning_threshold: 3.8,
                danger_threshold: 3.5,
                timestamp: new Date().toISOString(),
                change: 0
            },
            personalization: {
                value: 125,
                target: 140,
                max: 200,
                decimals: 0,
                warning_threshold: 110,
                danger_threshold: 90,
                timestamp: new Date().toISOString(),
                change: 0
            },
            ab_tests: {
                value: 7,
                target: 8,
                max: 12,
                decimals: 0,
                warning_threshold: 5,
                danger_threshold: 3,
                timestamp: new Date().toISOString(),
                change: 0
            }
        };
    }

    // Metrics Update Loop (simulated for demo)
    startMetricsUpdateLoop() {
        // In production, this would be driven by WebSocket messages
        // For demo, simulate updates every 30 seconds
        setInterval(() => {
            if (Math.random() > 0.7) { // 30% chance of update per interval
                const metrics = ['ml_accuracy', 'throughput', 'conversion'];
                const metric = metrics[Math.floor(Math.random() * metrics.length)];
                
                const variance = (Math.random() - 0.5) * 0.2;
                this.metrics[metric].value = Math.max(
                    0,
                    this.metrics[metric].value + variance
                );
                
                this.updateMetricDisplay(metric);
            }
        }, 30000);
    }

    setupEventListeners() {
        // Listen for keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'p') {
                e.preventDefault();
                document.getElementById('pauseBtn')?.click();
            }
            if (e.ctrlKey && e.key === 'e') {
                e.preventDefault();
                document.getElementById('exportBtn')?.click();
            }
        });
    }

    // Utilities
    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }

    getMetrics() {
        return this.metrics;
    }

    getStatus() {
        return {
            connected: this.isConnected,
            metrics: this.metrics,
            timestamp: new Date().toISOString()
        };
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Create global dashboard instance
    window.phase3Dashboard = new Phase3DashboardWebSocket({
        wsUrl: 'ws://localhost:8000/ws/phase3-monitoring',
        reconnectInterval: 3000,
        maxReconnectAttempts: 5
    });

    // Listen for events
    window.phase3Dashboard.on('connected', () => {
        console.log('Dashboard connected to Phase 3 monitoring');
    });

    window.phase3Dashboard.on('metric_updated', (data) => {
        console.log('Metric updated:', data);
    });

    window.phase3Dashboard.on('checkpoint_event', (data) => {
        console.log('Checkpoint event:', data);
    });

    window.phase3Dashboard.on('error_event', (data) => {
        console.error('Error event:', data);
    });

    window.phase3Dashboard.on('alert', (data) => {
        console.warn('Alert:', data);
    });

    window.phase3Dashboard.on('connection_failed', () => {
        console.error('Failed to maintain WebSocket connection');
    });
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Phase3DashboardWebSocket;
}
