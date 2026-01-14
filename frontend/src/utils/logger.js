/**
 * Frontend Logger for Transport Request Management System
 * Provides structured logging with localStorage backup for failed API calls
 */

class FrontendLogger {
    constructor() {
        this.logLevel = 'INFO'; // INFO, WARNING, ERROR
        this.maxStoredLogs = 100; // Maximum logs in localStorage
        this.storageKey = 'transport_app_logs';
        this.apiEndpoint = '/api/logs'; // Future endpoint for log collection
    }

    /**
     * Create structured log entry
     */
    createLogEntry(level, message, data = {}) {
        return {
            timestamp: new Date().toISOString(),
            level,
            message,
            url: window.location.href,
            userAgent: navigator.userAgent,
            sessionId: this.getSessionId(),
            data
        };
    }

    /**
     * Get or create session ID
     */
    getSessionId() {
        let sessionId = sessionStorage.getItem('transport_session_id');
        if (!sessionId) {
            sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('transport_session_id', sessionId);
        }
        return sessionId;
    }

    /**
     * Log form submission attempt
     */
    logFormSubmit(formData, status = 'ATTEMPT', errorMessage = null, requestId = null) {
        const logData = {
            event_type: 'FORM_SUBMIT',
            request_id: requestId,
            form_data: {
                delivery_note: formData.deliveryNoteNumber || '',
                truck_plates: formData.truckLicensePlates || '',
                trailer_plates: formData.trailerLicensePlates || '',
                carrier_country: formData.carrierCountry || '',
                carrier_name: formData.carrierFullName || '',
                border_crossing: formData.borderCrossing || '',
                crossing_date: formData.borderCrossingDate || ''
            },
            attachment: {
                has_attachment: formData.attachment ? true : false,
                filename: formData.attachment ? formData.attachment.name : null,
                size_bytes: formData.attachment ? formData.attachment.size : null
            },
            status,
            error_message: errorMessage,
            timestamp: new Date().toISOString()
        };

        const level = status === 'ERROR' ? 'ERROR' : 'INFO';
        const message = `Form submission ${status}${requestId ? `: ${requestId}` : ''}`;

        this.log(level, message, logData);

        // If it's an error or network failure, store for later retry
        if (status === 'ERROR' || status === 'NETWORK_ERROR') {
            this.storeFailedLog(logData);
        }
    }

    /**
     * Log API communication issues
     */
    logApiError(endpoint, error, requestData = null) {
        const logData = {
            event_type: 'API_ERROR',
            endpoint,
            error_type: error.name || 'Unknown',
            error_message: error.message || String(error),
            request_data: requestData,
            network_status: navigator.onLine ? 'online' : 'offline'
        };

        this.log('ERROR', `API Error: ${endpoint}`, logData);
        this.storeFailedLog(logData);
    }

    /**
     * Log general information
     */
    info(message, data = {}) {
        this.log('INFO', message, data);
    }

    /**
     * Log warnings
     */
    warning(message, data = {}) {
        this.log('WARNING', message, data);
    }

    /**
     * Log errors
     */
    error(message, data = {}) {
        this.log('ERROR', message, data);
    }

    /**
     * Core logging method
     */
    log(level, message, data = {}) {
        const logEntry = this.createLogEntry(level, message, data);
        
        // Console output for development
        const consoleMethod = level === 'ERROR' ? 'error' : 
                            level === 'WARNING' ? 'warn' : 'log';
        console[consoleMethod]('[Transport App]', message, data);

        // Store log entry
        this.storeLog(logEntry);

        // Try to send to backend (if available)
        this.sendLogToBackend(logEntry);
    }

    /**
     * Store log in localStorage
     */
    storeLog(logEntry) {
        try {
            const logs = this.getStoredLogs();
            logs.push(logEntry);

            // Keep only recent logs
            if (logs.length > this.maxStoredLogs) {
                logs.splice(0, logs.length - this.maxStoredLogs);
            }

            localStorage.setItem(this.storageKey, JSON.stringify(logs));
        } catch (error) {
            console.error('Failed to store log:', error);
        }
    }

    /**
     * Store failed logs for retry
     */
    storeFailedLog(logData) {
        try {
            const failedLogs = JSON.parse(localStorage.getItem('transport_failed_logs') || '[]');
            failedLogs.push({
                ...logData,
                retry_count: 0,
                stored_at: new Date().toISOString()
            });

            // Keep only recent failed logs
            if (failedLogs.length > 50) {
                failedLogs.splice(0, failedLogs.length - 50);
            }

            localStorage.setItem('transport_failed_logs', JSON.stringify(failedLogs));
        } catch (error) {
            console.error('Failed to store failed log:', error);
        }
    }

    /**
     * Get stored logs
     */
    getStoredLogs() {
        try {
            return JSON.parse(localStorage.getItem(this.storageKey) || '[]');
        } catch (error) {
            console.error('Failed to retrieve stored logs:', error);
            return [];
        }
    }

    /**
     * Send log to backend (future implementation)
     */
    async sendLogToBackend(logEntry) {
        // For now, just store. In future, could send to analytics endpoint
        // eslint-disable-next-line no-unused-vars
        const unused = logEntry; // Prevent ESLint warning
        return;
        
        /*
        try {
            await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(logEntry)
            });
        } catch (error) {
            // Silently fail - don't create infinite logging loop
        }
        */
    }

    /**
     * Export logs as CSV for manual analysis
     */
    exportLogsAsCSV() {
        const logs = this.getStoredLogs();
        if (logs.length === 0) {
            alert('No logs to export');
            return;
        }

        const headers = ['timestamp', 'level', 'message', 'event_type', 'session_id'];
        const csvRows = [headers.join(',')];

        logs.forEach(log => {
            const row = [
                log.timestamp,
                log.level,
                `"${log.message.replace(/"/g, '""')}"`, // Escape quotes
                log.data.event_type || '',
                log.sessionId || ''
            ];
            csvRows.push(row.join(','));
        });

        const csvContent = csvRows.join('\\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `transport_logs_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    /**
     * Clear all stored logs
     */
    clearLogs() {
        localStorage.removeItem(this.storageKey);
        localStorage.removeItem('transport_failed_logs');
        console.log('All logs cleared');
    }

    /**
     * Get log statistics
     */
    getLogStats() {
        const logs = this.getStoredLogs();
        const stats = {
            total: logs.length,
            levels: {},
            events: {},
            recent_errors: []
        };

        logs.forEach(log => {
            // Count by level
            stats.levels[log.level] = (stats.levels[log.level] || 0) + 1;
            
            // Count by event type
            const eventType = log.data.event_type || 'unknown';
            stats.events[eventType] = (stats.events[eventType] || 0) + 1;
            
            // Collect recent errors
            if (log.level === 'ERROR') {
                stats.recent_errors.push({
                    timestamp: log.timestamp,
                    message: log.message,
                    error: log.data.error_message
                });
            }
        });

        // Keep only last 10 errors
        stats.recent_errors = stats.recent_errors.slice(-10);

        return stats;
    }
}

// Create global logger instance
const frontendLogger = new FrontendLogger();

// Export for use in components
export default frontendLogger;