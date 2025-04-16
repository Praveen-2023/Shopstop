/**
 * Login functionality for ShopStop application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if login form exists
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Check for login error message in URL
    const urlParams = new URLSearchParams(window.location.search);
    const errorMsg = urlParams.get('error');
    if (errorMsg) {
        showLoginError(decodeURIComponent(errorMsg));
    }
});

/**
 * Handle login form submission
 */
function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        showLoginError('Please enter both username and password');
        return;
    }
    
    // Show loading indicator
    const loginBtn = document.querySelector('#login-form button[type="submit"]');
    const originalBtnText = loginBtn.innerHTML;
    loginBtn.disabled = true;
    loginBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Logging in...';
    
    // Clear previous error
    hideLoginError();
    
    // Send login request
    fetch('/shopstop/authUser', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Store authentication data in localStorage
        localStorage.setItem('sessionToken', data.session_token);
        localStorage.setItem('expiry', data.expiry);
        localStorage.setItem('username', username);
        localStorage.setItem('userRole', data.role);
        localStorage.setItem('memberId', data.member_id);
        
        console.log('Login successful');
        console.log('User role:', data.role);
        
        // Redirect to dashboard
        window.location.href = '/dashboard';
    })
    .catch(error => {
        console.error('Login error:', error);
        showLoginError(error.message || 'Login failed. Please try again.');
        
        // Reset button
        loginBtn.disabled = false;
        loginBtn.innerHTML = originalBtnText;
    });
}

/**
 * Show login error message
 */
function showLoginError(message) {
    const errorAlert = document.getElementById('login-error');
    if (errorAlert) {
        errorAlert.textContent = message;
        errorAlert.classList.remove('d-none');
    }
}

/**
 * Hide login error message
 */
function hideLoginError() {
    const errorAlert = document.getElementById('login-error');
    if (errorAlert) {
        errorAlert.classList.add('d-none');
    }
}
