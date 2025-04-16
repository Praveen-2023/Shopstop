/**
 * Authentication related functions for ShopStop application
 */

// Check if user is authenticated
function checkAuth() {
    const sessionToken = localStorage.getItem('sessionToken');
    const expiry = localStorage.getItem('expiry');
    const username = localStorage.getItem('username');
    const userRole = localStorage.getItem('userRole');
    const memberId = localStorage.getItem('memberId');

    console.log('Checking authentication...');
    console.log('Session token:', sessionToken ? 'Available' : 'Not available');
    console.log('Expiry:', expiry ? new Date(parseInt(expiry) * 1000).toLocaleString() : 'Not available');
    console.log('Current time:', new Date().toLocaleString());

    // Check for session token in URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const urlSessionToken = urlParams.get('session_token');

    if (urlSessionToken && !sessionToken) {
        console.log('Found session token in URL but not in localStorage, storing it');
        localStorage.setItem('sessionToken', urlSessionToken);

        // Set a default expiry time (24 hours from now) if not available
        if (!expiry) {
            const newExpiry = Math.floor(Date.now() / 1000) + (24 * 60 * 60);
            localStorage.setItem('expiry', newExpiry);
            console.log('Set default expiry time:', new Date(newExpiry * 1000).toLocaleString());
        }

        // Remove the session token from the URL to avoid sharing it
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
        console.log('Removed session token from URL');

        // Refresh the page to ensure proper authentication
        window.location.reload();
        return true;
    }

    // If no session token or expired, redirect to login
    if (!sessionToken || !expiry || (parseInt(expiry) < Date.now() / 1000)) {
        console.log('No valid session found, clearing auth data');
        clearAuthData();

        // Only redirect if not already on login page or home page
        const currentPath = window.location.pathname;
        if (currentPath !== '/login' && currentPath !== '/') {
            console.log('Redirecting to login page');
            window.location.href = '/login';
        }
        return false;
    }

    console.log('Authentication successful');

    // Update user info in the UI
    updateUserInfo(username, userRole);

    // Setup logout button
    setupLogout();

    // Set session token as a cookie as well (for backend validation)
    document.cookie = `session_token=${sessionToken}; path=/; max-age=${60*60*24}`;

    // Add a global fetch interceptor to add the session token to all requests
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        // Create a new options object to avoid modifying the original
        const newOptions = {...options};
        newOptions.headers = {...(options.headers || {})};

        // Always add the session token to the Authorization header
        newOptions.headers.Authorization = sessionToken;

        // Add session token as a query parameter for GET requests
        if (!url.includes('?')) {
            url = `${url}?session_token=${sessionToken}`;
        } else {
            url = `${url}&session_token=${sessionToken}`;
        }

        // Log the request for debugging
        console.log(`Sending request to ${url} with session token in headers and query params`);

        return originalFetch(url, newOptions);
    };

    return true;
}

// Clear all authentication data
function clearAuthData() {
    localStorage.removeItem('sessionToken');
    localStorage.removeItem('expiry');
    localStorage.removeItem('username');
    localStorage.removeItem('userRole');
    localStorage.removeItem('memberId');
}

// Update user info in the UI
function updateUserInfo(username, role) {
    const userNameElement = document.getElementById('user-name');
    const userRoleElement = document.getElementById('user-role');

    if (userNameElement) {
        userNameElement.textContent = username || 'Unknown User';
    }

    if (userRoleElement) {
        userRoleElement.textContent = role || 'User';
        userRoleElement.className = role && role.toLowerCase() === 'admin' ? 'badge bg-danger ms-2' : 'badge bg-primary ms-2';
    }
}

// Setup logout button
function setupLogout() {
    const logoutBtn = document.getElementById('logout-btn');

    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            // Clear authentication data
            clearAuthData();

            // Redirect to login page
            window.location.href = '/login';
        });
    }
}

// Check if user has admin role
function isAdmin() {
    const userRole = localStorage.getItem('userRole');
    return userRole && userRole.toLowerCase() === 'admin';
}

// Get current user ID
function getCurrentUserId() {
    return localStorage.getItem('memberId');
}
