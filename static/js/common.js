/**
 * Common utility functions for ShopStop application
 */

// Show message in modal
function showMessage(title, message) {
    const messageModal = new bootstrap.Modal(document.getElementById('messageModal'));
    document.getElementById('messageModalLabel').textContent = title;
    document.getElementById('messageModalBody').textContent = message;
    messageModal.show();
}

// Format date to YYYY-MM-DD
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toISOString().split('T')[0];
}

// Format currency
function formatCurrency(amount) {
    return '$' + parseFloat(amount).toFixed(2);
}

// Generate random ID with prefix
function generateId(prefix, length = 4) {
    return prefix + Math.floor(Math.random() * Math.pow(10, length)).toString().padStart(length, '0');
}

// Validate email format
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Validate phone number format
function isValidPhone(phone) {
    const re = /^\d{3}-\d{3}-\d{4}$/;
    return re.test(phone);
}

// Truncate text with ellipsis
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Get URL parameter by name
function getUrlParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// Set active nav item based on current page
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('#sidebar .nav-link');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Make authenticated API request
async function apiRequest(url, method = 'GET', data = null) {
    const sessionToken = localStorage.getItem('sessionToken');

    console.log('Making API request to:', url);
    console.log('Session token:', sessionToken ? 'Available' : 'Not available');

    // Add session token to URL for GET requests
    if (method === 'GET' && sessionToken && !url.includes('?')) {
        url = `${url}?session_token=${sessionToken}`;
        console.log('Added session token to URL:', url);
    } else if (method === 'GET' && sessionToken && url.includes('?')) {
        url = `${url}&session_token=${sessionToken}`;
        console.log('Added session token to URL with existing params:', url);
    }

    if (!sessionToken) {
        console.error('No session token available');
        // Clear any existing auth data
        if (typeof clearAuthData === 'function') {
            clearAuthData();
        } else {
            localStorage.removeItem('sessionToken');
            localStorage.removeItem('expiry');
            localStorage.removeItem('username');
            localStorage.removeItem('userRole');
            localStorage.removeItem('memberId');
        }
        // Redirect to login if no session token
        window.location.href = '/login';
        throw new Error('No session token available');
    }

    const options = {
        method: method,
        headers: {
            'Authorization': sessionToken,
            'Content-Type': 'application/json'
        },
        credentials: 'include' // Include cookies in the request
    };

    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }

    try {
        console.log('Sending request with options:', JSON.stringify(options));
        const response = await fetch(url, options);
        console.log('Response status:', response.status);

        // If unauthorized, redirect to login
        if (response.status === 401) {
            console.error('Unauthorized response (401)');
            // Clear auth data using the function from auth.js
            if (typeof clearAuthData === 'function') {
                clearAuthData();
            } else {
                localStorage.removeItem('sessionToken');
                localStorage.removeItem('expiry');
                localStorage.removeItem('username');
                localStorage.removeItem('userRole');
                localStorage.removeItem('memberId');
            }
            window.location.href = '/login';
            throw new Error('Session expired or invalid');
        }

        const responseData = await response.json();
        console.log('Response data:', responseData);
        return responseData;
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Set active nav item
    setActiveNavItem();

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Check authentication for protected pages
    const currentPath = window.location.pathname;
    // Skip auth check for login and home page
    if (currentPath !== '/login' && currentPath !== '/') {
        // Only check auth if the function exists (it's loaded from auth.js)
        if (typeof checkAuth === 'function') {
            checkAuth();
        }
    }
});
