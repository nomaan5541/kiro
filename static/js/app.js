// School Management System - Main JavaScript

// Global app object
const SchoolApp = {
    // Initialize the application
    init() {
        this.setupEventListeners();
        this.initializeComponents();
        this.setupFormValidation();
    },

    // Setup global event listeners
    setupEventListeners() {
        // Mobile sidebar toggle
        const sidebarToggle = document.querySelector('[data-sidebar-toggle]');
        const sidebar = document.querySelector('.sidebar');
        
        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('open');
            });
        }

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) {
                const sidebar = document.querySelector('.sidebar');
                const sidebarToggle = document.querySelector('[data-sidebar-toggle]');
                
                if (sidebar && !sidebar.contains(e.target) && !sidebarToggle?.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            }
        });

        // Auto-hide flash messages
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(message => {
            setTimeout(() => {
                message.style.opacity = '0';
                setTimeout(() => message.remove(), 300);
            }, 5000);
        });
    },

    // Initialize components
    initializeComponents() {
        this.initializeModals();
        this.initializeTooltips();
        this.initializeProgressBars();
        this.initializeDatePickers();
    },

    // Initialize modals
    initializeModals() {
        const modalTriggers = document.querySelectorAll('[data-modal-target]');
        const modalCloses = document.querySelectorAll('[data-modal-close]');
        
        modalTriggers.forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = trigger.getAttribute('data-modal-target');
                const modal = document.getElementById(targetId);
                if (modal) {
                    this.showModal(modal);
                }
            });
        });

        modalCloses.forEach(close => {
            close.addEventListener('click', (e) => {
                e.preventDefault();
                const modal = close.closest('.modal');
                if (modal) {
                    this.hideModal(modal);
                }
            });
        });

        // Close modal when clicking backdrop
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-backdrop')) {
                const modal = e.target.closest('.modal');
                if (modal) {
                    this.hideModal(modal);
                }
            }
        });
    },

    // Show modal
    showModal(modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        document.body.style.overflow = 'hidden';
        
        // Focus first input
        const firstInput = modal.querySelector('input, select, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    },

    // Hide modal
    hideModal(modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        document.body.style.overflow = '';
    },

    // Initialize tooltips
    initializeTooltips() {
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                const text = element.getAttribute('data-tooltip');
                this.showTooltip(e.target, text);
            });

            element.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    },

    // Show tooltip
    showTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = text;
        tooltip.style.cssText = `
            position: absolute;
            background: var(--bg-tertiary);
            color: var(--text-primary);
            padding: 0.5rem 0.75rem;
            border-radius: var(--radius-md);
            font-size: 0.75rem;
            z-index: 9999;
            pointer-events: none;
            box-shadow: var(--shadow-lg);
            border: 1px solid var(--border-color);
        `;
        
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
        
        this.currentTooltip = tooltip;
    },

    // Hide tooltip
    hideTooltip() {
        if (this.currentTooltip) {
            this.currentTooltip.remove();
            this.currentTooltip = null;
        }
    },

    // Initialize progress bars
    initializeProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar[data-progress]');
        
        progressBars.forEach(bar => {
            const progress = parseFloat(bar.getAttribute('data-progress'));
            setTimeout(() => {
                bar.style.width = progress + '%';
            }, 100);
        });
    },

    // Initialize date pickers
    initializeDatePickers() {
        const dateInputs = document.querySelectorAll('input[type="date"]');
        
        dateInputs.forEach(input => {
            // Set max date to today for birth dates
            if (input.name.includes('birth') || input.name.includes('dob')) {
                input.max = new Date().toISOString().split('T')[0];
            }
            
            // Set min date to today for future dates
            if (input.name.includes('due') || input.name.includes('expiry')) {
                input.min = new Date().toISOString().split('T')[0];
            }
        });
    },

    // Setup form validation
    setupFormValidation() {
        const forms = document.querySelectorAll('form[data-validate]');
        
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            });

            // Real-time validation
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('blur', () => {
                    this.validateField(input);
                });
            });
        });
    },

    // Validate form
    validateForm(form) {
        let isValid = true;
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        
        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });

        return isValid;
    },

    // Validate individual field
    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let errorMessage = '';

        // Required validation
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        }

        // Email validation
        if (field.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address';
            }
        }

        // Phone validation
        if (field.name === 'phone' && value) {
            const phoneRegex = /^[6-9]\d{9}$/;
            if (!phoneRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid 10-digit phone number';
            }
        }

        // Password validation
        if (field.type === 'password' && value) {
            if (value.length < 6) {
                isValid = false;
                errorMessage = 'Password must be at least 6 characters long';
            }
        }

        // Number validation
        if (field.type === 'number' && value) {
            const min = parseFloat(field.min);
            const max = parseFloat(field.max);
            const numValue = parseFloat(value);

            if (!isNaN(min) && numValue < min) {
                isValid = false;
                errorMessage = `Value must be at least ${min}`;
            }

            if (!isNaN(max) && numValue > max) {
                isValid = false;
                errorMessage = `Value must be at most ${max}`;
            }
        }

        // Update field appearance
        this.updateFieldValidation(field, isValid, errorMessage);
        
        return isValid;
    },

    // Update field validation appearance
    updateFieldValidation(field, isValid, errorMessage) {
        const fieldGroup = field.closest('.form-group') || field.parentElement;
        let errorElement = fieldGroup.querySelector('.field-error');

        // Remove existing error styling
        field.classList.remove('field-invalid', 'field-valid');

        if (!isValid) {
            field.classList.add('field-invalid');
            
            if (!errorElement) {
                errorElement = document.createElement('div');
                errorElement.className = 'field-error';
                errorElement.style.cssText = `
                    color: var(--error);
                    font-size: 0.75rem;
                    margin-top: 0.25rem;
                `;
                fieldGroup.appendChild(errorElement);
            }
            
            errorElement.textContent = errorMessage;
        } else {
            field.classList.add('field-valid');
            
            if (errorElement) {
                errorElement.remove();
            }
        }
    },

    // Utility functions
    utils: {
        // Format currency
        formatCurrency(amount) {
            return new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR'
            }).format(amount);
        },

        // Format date
        formatDate(date, options = {}) {
            const defaultOptions = {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            };
            
            return new Intl.DateTimeFormat('en-IN', { ...defaultOptions, ...options }).format(new Date(date));
        },

        // Debounce function
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Show notification
        showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.style.cssText = `
                position: fixed;
                top: 1rem;
                right: 1rem;
                background: var(--bg-secondary);
                color: var(--text-primary);
                padding: 1rem 1.5rem;
                border-radius: var(--radius-lg);
                box-shadow: var(--shadow-xl);
                border-left: 4px solid var(--accent-orange);
                z-index: 9999;
                max-width: 400px;
                animation: slideIn 0.3s ease-out;
            `;

            if (type === 'success') {
                notification.style.borderLeftColor = 'var(--success)';
            } else if (type === 'error') {
                notification.style.borderLeftColor = 'var(--error)';
            } else if (type === 'warning') {
                notification.style.borderLeftColor = 'var(--warning)';
            }

            notification.textContent = message;
            document.body.appendChild(notification);

            setTimeout(() => {
                notification.style.opacity = '0';
                setTimeout(() => notification.remove(), 300);
            }, 5000);
        },

        // Copy to clipboard
        async copyToClipboard(text) {
            try {
                await navigator.clipboard.writeText(text);
                this.showNotification('Copied to clipboard!', 'success');
            } catch (err) {
                console.error('Failed to copy: ', err);
                this.showNotification('Failed to copy to clipboard', 'error');
            }
        }
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    SchoolApp.init();
});

// Export for use in other scripts
window.SchoolApp = SchoolApp;
    // E
nhanced Theme Functions
    setupThemeEnhancements() {
        this.setupAnimations();
        this.setupAccessibility();
        this.setupPerformanceOptimizations();
    },

    // Setup animations
    setupAnimations() {
        // Intersection Observer for fade-in animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        }, observerOptions);

        // Observe all cards and major elements
        document.querySelectorAll('.dashboard-card, .kpi-card').forEach(el => {
            observer.observe(el);
        });
    },

    // Setup accessibility features
    setupAccessibility() {
        // Keyboard navigation for dropdowns
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                // Close all open dropdowns and modals
                document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                    menu.classList.remove('show');
                });
                
                const openModals = document.querySelectorAll('.modal:not(.hidden)');
                openModals.forEach(modal => this.hideModal(modal));
            }
        });

        // Focus management for modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const openModal = document.querySelector('.modal:not(.hidden)');
                if (openModal) {
                    this.trapFocus(e, openModal);
                }
            }
        });
    },

    // Trap focus within modal
    trapFocus(e, modal) {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
        }
    },

    // Setup performance optimizations
    setupPerformanceOptimizations() {
        // Lazy load images
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));

        // Debounce search inputs
        const searchInputs = document.querySelectorAll('input[type="search"], input[data-search]');
        searchInputs.forEach(input => {
            let timeout;
            input.addEventListener('input', (e) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    // Trigger search function
                    if (typeof window.performSearch === 'function') {
                        window.performSearch(e.target.value);
                    }
                }, 300);
            });
        });
    },

    // Enhanced notification system
    showNotification(message, type = 'info', duration = 4000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} fade-in`;
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button class="btn-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: var(--spacing-lg);
            right: var(--spacing-lg);
            z-index: 1000;
            max-width: 350px;
            animation: slideInRight 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after duration
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, duration);
        
        return notification;
    },

    // Get notification icon based on type
    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'times-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    },

    // Enhanced form validation
    validateForm(form) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        const errors = [];

        requiredFields.forEach(field => {
            const value = field.value.trim();
            const fieldName = field.getAttribute('name') || field.getAttribute('id') || 'Field';
            
            if (!value) {
                field.classList.add('error');
                errors.push(`${fieldName} is required`);
                isValid = false;
            } else {
                field.classList.remove('error');
                
                // Specific validation based on field type
                if (field.type === 'email' && !this.isValidEmail(value)) {
                    field.classList.add('error');
                    errors.push(`${fieldName} must be a valid email address`);
                    isValid = false;
                }
                
                if (field.type === 'tel' && !this.isValidPhone(value)) {
                    field.classList.add('error');
                    errors.push(`${fieldName} must be a valid phone number`);
                    isValid = false;
                }
            }
        });

        // Show validation errors
        if (!isValid) {
            this.showNotification(errors[0], 'error');
        }

        return isValid;
    },

    // Email validation
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    // Phone validation
    isValidPhone(phone) {
        const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
        return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
    },

    // Utility functions
    utils: {
        // Format currency
        formatCurrency(amount, currency = 'INR') {
            return new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: currency
            }).format(amount);
        },

        // Format date
        formatDate(date, options = {}) {
            const defaultOptions = {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            };
            return new Intl.DateTimeFormat('en-IN', { ...defaultOptions, ...options }).format(new Date(date));
        },

        // Debounce function
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Throttle function
        throttle(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        }
    }
};

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    SchoolApp.init();
    SchoolApp.setupThemeEnhancements();
});

// Export for global access
window.SchoolApp = SchoolApp;