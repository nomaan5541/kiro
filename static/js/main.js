// Main JavaScript for School Management System

// Theme toggle functionality
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        const currentTheme = localStorage.getItem('theme') || 'dark';
        applyTheme(currentTheme);
        
        themeToggle.addEventListener('click', () => {
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            localStorage.setItem('theme', newTheme);
            applyTheme(newTheme);
        });
    }
}

function applyTheme(theme) {
    const root = document.documentElement;
    
    if (theme === 'light') {
        root.style.setProperty('--color-background', '#f6f7fb');
        root.style.setProperty('--color-surface', '#ffffff');
        root.style.setProperty('--color-text', '#0b0b0b');
        root.style.setProperty('--color-muted', '#666666');
    } else {
        root.style.setProperty('--color-background', '#101010');
        root.style.setProperty('--color-surface', '#1E1E1E');
        root.style.setProperty('--color-text', '#E0E0E0');
        root.style.setProperty('--color-muted', '#505050');
    }
}

// Form validation helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^\d{10}$/;
    return re.test(phone.replace(/\D/g, ''));
}

// Auto-dismiss alerts
function initAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    });
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initAlerts();
});

// Utility functions
const Utils = {
    formatCurrency: (amount) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR'
        }).format(amount);
    },
    
    formatDate: (date) => {
        return new Date(date).toLocaleDateString('en-IN');
    },
    
    showLoading: (element) => {
        element.innerHTML = '<span>Loading...</span>';
        element.disabled = true;
    },
    
    hideLoading: (element, originalText) => {
        element.innerHTML = originalText;
        element.disabled = false;
    }
};