/**
 * Student Management System - Main JavaScript
 * 
 * Handles authentication, API calls, and UI interactions.
 */

// API Configuration
const API_BASE_URL = window.location.origin + '/api';

// Auth Token Management
const Auth = {
    getToken() {
        return localStorage.getItem('access_token');
    },
    
    getRefreshToken() {
        return localStorage.getItem('refresh_token');
    },
    
    setTokens(accessToken, refreshToken) {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
    },
    
    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    },
    
    getUser() {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    },
    
    setUser(user) {
        localStorage.setItem('user', JSON.stringify(user));
    },
    
    isAuthenticated() {
        return !!this.getToken();
    },
    
    logout() {
        this.clearTokens();
        window.location.href = '/login.html';
    }
};

// API Client
const API = {
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        // Add auth token if available
        const token = Auth.getToken();
        if (token) {
            defaultOptions.headers['Authorization'] = `Bearer ${token}`;
        }
        
        const config = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };
        
        try {
            const response = await fetch(url, config);
            
            // Handle 401 Unauthorized
            if (response.status === 401) {
                Auth.logout();
                return null;
            }
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || data.message || 'Request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            UI.showToast(error.message, 'error');
            throw error;
        }
    },
    
    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },
    
    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};

// UI Utilities
const UI = {
    showToast(message, type = 'success') {
        const container = document.querySelector('.toast-container') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    },
    
    createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
        return container;
    },
    
    showLoading(element) {
        element.classList.add('loading');
        element.disabled = true;
    },
    
    hideLoading(element) {
        element.classList.remove('loading');
        element.disabled = false;
    },
    
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-ZA', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },
    
    formatDateTime(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString('en-ZA', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    formatTime(timeString) {
        if (!timeString) return 'N/A';
        return timeString.substring(0, 5);
    },
    
    getInitials(name) {
        return name
            .split(' ')
            .map(n => n[0])
            .join('')
            .toUpperCase()
            .substring(0, 2);
    },
    
    getStatusBadge(status) {
        const statusClasses = {
            'active': 'badge-success',
            'present': 'badge-success',
            'enrolled': 'badge-success',
            'approved': 'badge-success',
            'completed': 'badge-success',
            'pending': 'badge-warning',
            'submitted': 'badge-warning',
            'in_progress': 'badge-warning',
            'late': 'badge-warning',
            'absent': 'badge-danger',
            'rejected': 'badge-danger',
            'failed': 'badge-danger',
            'open': 'badge-info',
            'draft': 'badge-info',
        };
        
        const className = statusClasses[status.toLowerCase()] || 'badge-primary';
        return `<span class="badge ${className}">${status.replace(/_/g, ' ').toUpperCase()}</span>`;
    }
};

// Navigation
const Navigation = {
    init() {
        this.highlightCurrentPage();
        this.initMobileMenu();
    },
    
    highlightCurrentPage() {
        const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';
        document.querySelectorAll('.nav-item').forEach(item => {
            const href = item.getAttribute('href');
            if (href && href.includes(currentPage)) {
                item.classList.add('active');
            }
        });
    },
    
    initMobileMenu() {
        const menuToggle = document.querySelector('.menu-toggle');
        const sidebar = document.querySelector('.sidebar');
        
        if (menuToggle && sidebar) {
            menuToggle.addEventListener('click', () => {
                sidebar.classList.toggle('open');
            });
        }
    }
};

// User Menu
const UserMenu = {
    init() {
        this.renderUserInfo();
        this.initDropdown();
    },
    
    renderUserInfo() {
        const user = Auth.getUser();
        if (!user) return;
        
        const userNameEl = document.querySelector('.user-name');
        const userRoleEl = document.querySelector('.user-role');
        const userAvatarEl = document.querySelector('.user-avatar');
        
        if (userNameEl) userNameEl.textContent = user.full_name || `${user.first_name} ${user.last_name}`;
        if (userRoleEl) userRoleEl.textContent = user.role;
        if (userAvatarEl) userAvatarEl.textContent = UI.getInitials(user.first_name + ' ' + user.last_name);
    },
    
    initDropdown() {
        const logoutBtn = document.querySelector('.logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                Auth.logout();
            });
        }
    }
};

// Geolocation Service
const GeoLocation = {
    async getCurrentPosition() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation is not supported by your browser'));
                return;
            }
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    });
                },
                (error) => {
                    reject(new Error(`Geolocation error: ${error.message}`));
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        });
    },
    
    async checkGeofence() {
        try {
            const position = await this.getCurrentPosition();
            const result = await API.get(`/attendance/geofence/status?lat=${position.lat}&lng=${position.lng}`);
            return result;
        } catch (error) {
            console.error('Geofence check failed:', error);
            throw error;
        }
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication for protected pages
    const publicPages = ['login.html', 'register.html', 'index.html', 'apply.html'];
    const currentPage = window.location.pathname.split('/').pop();
    
    if (!publicPages.includes(currentPage) && !Auth.isAuthenticated()) {
        window.location.href = '/login.html';
        return;
    }
    
    // Initialize UI components
    Navigation.init();
    UserMenu.init();
});

// Export for use in other scripts
window.Auth = Auth;
window.API = API;
window.UI = UI;
window.GeoLocation = GeoLocation;
