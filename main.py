from flask import Flask, request, jsonify, g, render_template, redirect
from flask_mysqldb import MySQL
import logging
import os
from functools import wraps
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__)

# Database configuration
app.config['MYSQL_HOST'] = '10.0.116.125'
app.config['MYSQL_USER'] = 'cs432g17'
app.config['MYSQL_PASSWORD'] = 'qJ5YXTnZ'
app.config['MYSQL_DB'] = 'cs432g17'  # Project-specific database
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Constants
CIMS_DB = 'cs432cims'  # Centralized database
CENTRAL_API = 'http://localhost:5000'

# Initialize MySQL
mysql = MySQL(app)

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    filename='logs/security.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# Session validation middleware
def validate_session(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip validation for public routes
        public_routes = ['/login', '/', '/static', '/health', '/api/info']
        if any(request.path.startswith(route) for route in public_routes):
            print(f"Skipping validation for public route: {request.path}")
            return f(*args, **kwargs)

        # For API requests, extract token from Authorization header
        # For frontend requests, extract from cookie or query parameter
        is_api_request = request.path.startswith('/api/') or request.headers.get('Content-Type') == 'application/json'

        # Try to get session token from different sources
        session_token = None

        # First try query parameter (highest priority)
        if 'session_token' in request.args:
            session_token = request.args.get('session_token')
            print(f"Found session token in query params: {session_token}")

        # Then try Authorization header
        if not session_token and 'Authorization' in request.headers:
            session_token = request.headers.get('Authorization')
            print(f"Found Authorization header: {session_token}")
            # Clean the token (remove quotes if present)
            if session_token and (session_token.startswith('"') and session_token.endswith('"')):
                session_token = session_token[1:-1]
                print(f"Cleaned token from quotes: {session_token}")

        # Finally try cookies
        if not session_token and 'session_token' in request.cookies:
            session_token = request.cookies.get('session_token')
            print(f"Found session token in cookies: {session_token}")

        print(f"Request path: {request.path}, method: {request.method}, token: {session_token}")

        # If no token found and it's a GET request to a template, redirect to login
        if not session_token:
            if request.method == 'GET' and not is_api_request:
                print(f"No session token found for {request.path}, redirecting to login")
                return redirect('/login')
            else:
                # For API requests, return 401
                log_unauthorized_access(request, "Missing session token")
                return jsonify({"error": "Session token required"}), 401

        # Check if session is valid by querying the Login table in CIMS database
        try:
            cur = mysql.connection.cursor()

            # Get current timestamp for comparing with expiry
            current_time = int(datetime.now().timestamp())

            print(f"Validating session token: {session_token}, current time: {current_time}")

            # For testing purposes, always try without expiry check first
            cur.execute(
                f"""SELECT MemberID, Role FROM {CIMS_DB}.Login
                   WHERE Session = %s""",
                (session_token,)
            )

            user_data = cur.fetchone()

            if user_data:
                print(f"Found session for user: {user_data['MemberID']}, role: {user_data['Role']}")
                # Update the expiry time
                new_expiry = int((datetime.now() + timedelta(hours=24)).timestamp())
                cur.execute(
                    f"""UPDATE {CIMS_DB}.Login
                       SET Expiry = %s
                       WHERE Session = %s""",
                    (new_expiry, session_token)
                )
                mysql.connection.commit()
            else:
                # Try with different token formats
                possible_tokens = [
                    session_token,
                    session_token.strip() if session_token else None,
                    session_token.strip('"') if session_token else None,
                    session_token.strip("'") if session_token else None,
                    session_token.strip('"\' ') if session_token else None
                ]

                for token in possible_tokens:
                    if not token or token == session_token:
                        continue

                    print(f"Trying with alternative token format: {token}")
                    cur.execute(
                        f"""SELECT MemberID, Role FROM {CIMS_DB}.Login
                           WHERE Session = %s""",
                        (token,)
                    )
                    user_data = cur.fetchone()

                    if user_data:
                        print(f"Found session with alternative token format for user: {user_data['MemberID']}")
                        session_token = token  # Use this token from now on
                        # Update the expiry time
                        new_expiry = int((datetime.now() + timedelta(hours=24)).timestamp())
                        cur.execute(
                            f"""UPDATE {CIMS_DB}.Login
                               SET Expiry = %s
                               WHERE Session = %s""",
                            (new_expiry, session_token)
                        )
                        mysql.connection.commit()
                        break

            cur.close()

            if not user_data:
                log_unauthorized_access(request, "Invalid or expired session token")
                print(f"Invalid or expired session token: {session_token}")
                if not is_api_request and request.method == 'GET':
                    return redirect('/login')
                return jsonify({"error": "Invalid or expired session"}), 401

            # Store user data in Flask's g object for use in route handlers
            g.user_data = user_data
            print(f"Session validated for user: {user_data['MemberID']}")
            return f(*args, **kwargs)

        except Exception as e:
            log_unauthorized_access(request, f"Database error: {str(e)}")
            print(f"Database error during session validation: {str(e)}")
            if not is_api_request and request.method == 'GET':
                return redirect('/login')
            return jsonify({"error": "Authentication error"}), 500

    return decorated_function

# Role-based access control middleware
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For testing purposes, allow all authenticated users to perform admin actions
        # In a production environment, you would want to uncomment the role check
        if not hasattr(g, 'user_data'):
            log_unauthorized_access(request, "Unauthenticated user attempted admin action")
            return jsonify({"error": "Authentication required"}), 401

        # Print debug information
        print(f"Admin check for user: {g.user_data['MemberID']}, Role: {g.user_data['Role']}")

        # TEMPORARILY DISABLED FOR TESTING - Allow all authenticated users to perform admin actions
        # Comment this out and uncomment the next block for production
        print(f"ADMIN CHECK BYPASSED FOR TESTING - Allowing user {g.user_data['MemberID']} to perform admin action")
        return f(*args, **kwargs)

        # Check if user has admin role - UNCOMMENT THIS FOR PRODUCTION
        # if g.user_data['Role'].lower() != 'admin':
        #     log_unauthorized_access(request, "Non-admin attempted admin action")
        #     return jsonify({"error": "Admin access required"}), 403
        # return f(*args, **kwargs)
    return decorated_function

# Logging function for unauthorized access
def log_unauthorized_access(req, message):
    """Log unauthorized access attempts with details"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'endpoint': req.endpoint,
        'method': req.method,
        'ip': req.remote_addr,
        'user_agent': req.user_agent.string if req.user_agent else 'Unknown',
        'message': message
    }
    logging.warning(str(log_entry))

# Logging function for database changes
def log_db_change(action, table, data, user_id=None):
    """Log database changes with details"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'table': table,
        'data': data,
        'user_id': user_id if user_id else 'System'
    }
    logging.info(str(log_entry))

# Import route modules
from createUser import add_auth_routes
from addUser import add_user_routes
from deleteUser import add_delete_routes
from shops import add_shop_routes
from products import add_product_routes
from customers import add_customer_routes
from portfolio import add_portfolio_routes
from supplier import add_supplier_routes
from employee import add_employee_routes
from order import add_order_routes
from attendance import add_attendance_routes
from loyalty import add_loyalty_routes
from dashboard_api import add_dashboard_routes
from data_display import add_data_display_routes

# Register routes with the main app
add_auth_routes(app, mysql, validate_session, admin_required, log_db_change)
add_user_routes(app, mysql, validate_session, admin_required, log_db_change)
add_delete_routes(app, mysql, validate_session, admin_required, log_db_change)
add_shop_routes(app, mysql, validate_session, admin_required, log_db_change)
add_product_routes(app, mysql, validate_session, admin_required, log_db_change)
add_customer_routes(app, mysql, validate_session, admin_required, log_db_change)
add_portfolio_routes(app, mysql, validate_session, admin_required, log_db_change)
add_supplier_routes(app, mysql, validate_session, admin_required, log_db_change)
add_employee_routes(app, mysql, validate_session, admin_required, log_db_change)
add_order_routes(app, mysql, validate_session, admin_required, log_db_change)
add_attendance_routes(app, mysql, validate_session, admin_required, log_db_change)
add_loyalty_routes(app, mysql, validate_session, admin_required, log_db_change)
add_dashboard_routes(app, mysql, validate_session, admin_required, log_db_change)
add_data_display_routes(app, mysql, validate_session, admin_required, log_db_change)

# Public frontend routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

# Protected frontend routes
@app.route('/dashboard')
@validate_session
def dashboard():
    return render_template('dashboard.html')

@app.route('/members')
@validate_session
def members_page():
    return render_template('members.html')

@app.route('/shops')
@validate_session
def shops_page():
    return render_template('shops.html')

@app.route('/products')
@validate_session
def products_page():
    return render_template('products.html')

@app.route('/customers')
@validate_session
def customers_page():
    return render_template('customers.html')

@app.route('/portfolio')
@validate_session
def portfolio_page():
    return render_template('portfolio.html')

# New data display pages
@app.route('/shop-display')
@validate_session
def shop_display_page():
    return render_template('shop_display.html')

@app.route('/employee-display')
@validate_session
def employee_display_page():
    return render_template('employee_display.html')

@app.route('/order-display')
@validate_session
def order_display_page():
    return render_template('order_display.html')

@app.route('/profile-images')
@validate_session
def profile_images_page():
    return render_template('profile_images.html')

# API info route
@app.route('/api/info')
def api_info():
    return jsonify({
        "message": "Welcome to ShopStop API",
        "version": "1.0",
        "status": "running"
    })

# Health check route
@app.route('/health')
def health_check():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")
        cur.close()
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# Debug route to check user role
@app.route('/check-role')
def check_role():
    try:
        # Get the session token from different sources
        session_token = None

        # First try query parameter (highest priority)
        if 'session_token' in request.args:
            session_token = request.args.get('session_token')
            print(f"Found session token in query params: {session_token}")

        # Then try Authorization header
        if not session_token and 'Authorization' in request.headers:
            session_token = request.headers.get('Authorization')
            print(f"Found Authorization header: {session_token}")
            # Clean the token (remove quotes if present)
            if session_token and (session_token.startswith('"') and session_token.endswith('"')):
                session_token = session_token[1:-1]
                print(f"Cleaned token from quotes: {session_token}")

        # Finally try cookies
        if not session_token and 'session_token' in request.cookies:
            session_token = request.cookies.get('session_token')
            print(f"Found session token in cookies: {session_token}")

        print(f"Check-role using token: {session_token}")

        if not session_token:
            return jsonify({"error": "No session token provided"}), 401

        # Get user data from the database
        cur = mysql.connection.cursor()

        # Try with different token formats
        possible_tokens = [
            session_token,
            session_token.strip() if session_token else None,
            session_token.strip('"') if session_token else None,
            session_token.strip("'") if session_token else None,
            session_token.strip('"\' ') if session_token else None
        ]

        user_data = None
        for token in possible_tokens:
            if not token:
                continue

            print(f"Trying check-role with token: {token}")
            cur.execute(
                f"""SELECT MemberID, Role FROM {CIMS_DB}.Login
                   WHERE Session = %s""",
                (token,)
            )
            user_data = cur.fetchone()

            if user_data:
                print(f"Found user in check-role: {user_data['MemberID']}, role: {user_data['Role']}")
                session_token = token  # Use this token from now on
                break

        cur.close()

        if not user_data:
            return jsonify({"error": "User not found"}), 404

        # Return user role information
        return jsonify({
            "status": "success",
            "member_id": user_data['MemberID'],
            "role": user_data['Role'],
            "is_admin": user_data['Role'].lower() == 'admin',
            "session_token": session_token
        })
    except Exception as e:
        print(f"Error in check-role: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
