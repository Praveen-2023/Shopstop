from flask import Flask, request, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)

# Configure MySQL connection
app.config['MYSQL_HOST'] = '10.0.116.125'  # Replace with your host
app.config['MYSQL_USER'] = 'cs432g17'      # Replace with your username
app.config['MYSQL_PASSWORD'] = 'qJ5YXTnZ' # Replace with your password
app.config['MYSQL_DB'] = 'cs432cims'      # Replace with your database name

mysql = MySQL(app)

# Route to fetch members (GET request)
@app.route('/get-info', methods=['GET'])
def get_members():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM members LIMIT 5;")
        rows = cur.fetchall()
        return jsonify({"status": "success", "data": rows})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()

# Route to create a new member (POST request)
@app.route('/api/members/create', methods=['POST'])
def create_member():
    data = request.json  # Access JSON data from the request
    
    # Validate input
    required_fields = ['UserName', 'emailID', 'DoB']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    username = data['UserName']
    email_id = data['emailID']
    dob = data['DoB']
    
    try:
        cur = mysql.connection.cursor()
        
        # Insert into members table
        cur.execute(
            "INSERT INTO members (UserName, emailID, DoB) VALUES (%s, %s, %s)",
            (username, email_id, dob)
        )
        
        mysql.connection.commit()
        
        return jsonify({
            "message": "Member created successfully",
            "member_id": cur.lastrowid,
            "user": {
                "UserName": username,
                "emailID": email_id,
                "DoB": dob
            }
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


'''
from flask import Flask, request, jsonify  # Ensure 'request' is properly imported
import mysql.connector
import hashlib  # For password hashing
import uuid     # For generating unique session tokens
from datetime import datetime, timedelta

app = Flask(_name_)

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='10.0.116.125',
            user='cs432g17',
            password='qJ5YXTnZ',
            database='cs432cims',
            connect_timeout=5
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/api/members/create', methods=['POST'])
def create_member():
    data = request.json  # Access JSON data from the request
    
    # Validate input
    if not data or not all(k in data for k in ('UserName', 'emailID', 'DoB')):
        return jsonify({"error": "Missing required fields"}), 400
    
    username = data['UserName']
    email_id = data['emailID']
    dob = data['DoB']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert into members table
        cursor.execute(
            "INSERT INTO members (UserName, emailID, DoB) VALUES (%s, %s, %s)",
            (username, email_id, dob)
        )
        
        # Get the newly created member ID
        member_id = cursor.lastrowid
        
        # Create default password (hashed for security)
        default_password = hashlib.sha256(f"{username}123".encode()).hexdigest()
        
        # Set default role
        default_role = "user"
        
        # Insert into login table with default credentials
        # Note: MemberID is VARCHAR in the login table but might be INT in members table
        cursor.execute(
            "INSERT INTO Login (MemberID, Password, Role, Session, Expiry) VALUES (%s, %s, %s, %s, %s)",
            (str(member_id), default_password, default_role, None, None)
        )
        
        conn.commit()
        
        return jsonify({
            "message": "Member created successfully with default login credentials",
            "member_id": member_id,
            "username": username
        }), 201
    
    except mysql.connector.Error as err:
        # If an error occurs, rollback changes
        if 'conn' in locals() and conn.is_connected():
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/auth/login', methods=['POST'])
def auth_user():
    data = request.json
    
    # Validate input
    if not data or not all(k in data for k in ('username', 'password')):
        return jsonify({"error": "Missing credentials"}), 400
    
    username = data['username']
    password = data['password']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Find member ID by username
        cursor.execute(
            "SELECT ID FROM members WHERE UserName = %s",
            (username,)
        )
        member = cursor.fetchone()
        
        if not member:
            return jsonify({"error": "Invalid username"}), 401
        
        member_id = member['ID']
        
        # Hash the provided password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Check credentials
        cursor.execute(
            "SELECT * FROM Login WHERE MemberID = %s AND Password = %s",
            (str(member_id), hashed_password)
        )
        login_data = cursor.fetchone()
        
        if not login_data:
            return jsonify({"error": "Invalid password"}), 401
        
        # Generate session token
        session_token = str(uuid.uuid4())
        expiry_time = datetime.now() + timedelta(hours=24)  # Set expiry for 24 hours
        
        # Update session token and expiry
        cursor.execute(
            "UPDATE Login SET Session = %s, Expiry = %s WHERE MemberID = %s",
            (session_token, expiry_time, str(member_id))
        )
        
        conn.commit()
        
        return jsonify({
            "message": "Login successful",
            "session_token": session_token,
            "expiry": expiry_time.isoformat(),
            "role": login_data['Role']
        }), 200
    
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if _name_ == '_main_':
    app.run(host='0.0.0.0', port=5000, debug=True)
'''