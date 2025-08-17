// static/js/submission_status.js - Real-time submission status updates
class SubmissionStatusChecker {
    constructor() {
        this.pendingSubmissions = new Set();
        this.checkInterval = 3000; // Check every 3 seconds
        this.maxChecks = 20; // Stop after 1 minute
        this.checkCounts = new Map();
        this.init();
    }
    
    init() {
        // Find all pending submissions on page load
        document.querySelectorAll('.submission-status[data-status="PE"]').forEach(element => {
            const submissionId = element.getAttribute('data-submission-id');
            if (submissionId) {
                this.startChecking(submissionId, element);
            }
        });
    }
    
    startChecking(submissionId, element) {
        if (this.pendingSubmissions.has(submissionId)) return;
        
        this.pendingSubmissions.add(submissionId);
        this.checkCounts.set(submissionId, 0);
        
        // Add loading indicator
        this.setLoadingState(element);
        
        // Start checking
        this.checkSubmissionStatus(submissionId, element);
    }
    
    async checkSubmissionStatus(submissionId, element) {
        try {
            const response = await fetch(`/submission/${submissionId}/status/`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            
            if (data.success) {
                if (!data.is_pending) {
                    // Submission completed
                    this.updateSubmissionDisplay(element, data.status, data.status_display);
                    this.pendingSubmissions.delete(submissionId);
                    this.checkCounts.delete(submissionId);
                    return;
                }
            }
            
            // Still pending, check again
            const checkCount = this.checkCounts.get(submissionId) + 1;
            this.checkCounts.set(submissionId, checkCount);
            
            if (checkCount < this.maxChecks) {
                setTimeout(() => {
                    this.checkSubmissionStatus(submissionId, element);
                }, this.checkInterval);
            } else {
                // Timeout reached
                this.setTimeoutState(element);
                this.pendingSubmissions.delete(submissionId);
                this.checkCounts.delete(submissionId);
            }
            
        } catch (error) {
            console.error('Error checking submission status:', error);
            this.setErrorState(element);
            this.pendingSubmissions.delete(submissionId);
            this.checkCounts.delete(submissionId);
        }
    }
    
    setLoadingState(element) {
        element.innerHTML = `
            <span class="badge badge-warning">
                ⏳ Evaluating...
            </span>
        `;
    }
    
    updateSubmissionDisplay(element, status, statusDisplay) {
        const badgeClass = this.getStatusBadgeClass(status);
        const icon = this.getStatusIcon(status);
        
        element.innerHTML = `
            <span class="badge ${badgeClass}">
                ${icon} ${statusDisplay}
            </span>
        `;
        element.setAttribute('data-status', status);
        
        // Show notification
        if (status === 'AC') {
            this.showNotification('Success! 🎉', 'Your solution was accepted!');
        } else if (status === 'WA') {
            this.showNotification('Wrong Answer ❌', 'Try again!');
        }
    }
    
    setTimeoutState(element) {
        element.innerHTML = `
            <span class="badge badge-secondary">
                ⏱️ Check manually
            </span>
        `;
    }
    
    setErrorState(element) {
        element.innerHTML = `
            <span class="badge badge-danger">
                ❌ Check failed
            </span>
        `;
    }
    
    getStatusBadgeClass(status) {
        const statusClasses = {
            'AC': 'badge-success',
            'WA': 'badge-danger', 
            'RE': 'badge-danger',
            'TLE': 'badge-warning',
            'CE': 'badge-warning',
            'PE': 'badge-info'
        };
        return statusClasses[status] || 'badge-secondary';
    }
    
    getStatusIcon(status) {
        const statusIcons = {
            'AC': '✅',
            'WA': '❌',
            'RE': '💥',
            'TLE': '⏰',
            'CE': '⚠️',
            'PE': '⏳'
        };
        return statusIcons[status] || '?';
    }
    
    showNotification(title, message) {
        // Simple notification - you can enhance this
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, { body: message });
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new SubmissionStatusChecker();
});