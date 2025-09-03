// Coffee Admin App JavaScript

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// SSE Connection for real-time updates
class SSEManager {
    constructor() {
        this.connections = {};
    }
    
    connect(channel, callback) {
        if (this.connections[channel]) {
            this.disconnect(channel);
        }
        
        const eventSource = new EventSource(`/sse/${channel}`);
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            callback(data);
        };
        
        eventSource.onerror = function(event) {
            console.error('SSE error:', event);
        };
        
        this.connections[channel] = eventSource;
    }
    
    disconnect(channel) {
        if (this.connections[channel]) {
            this.connections[channel].close();
            delete this.connections[channel];
        }
    }
    
    disconnectAll() {
        Object.keys(this.connections).forEach(channel => {
            this.disconnect(channel);
        });
    }
}

// Global SSE manager
window.sseManager = new SSEManager();

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    window.sseManager.disconnectAll();
});