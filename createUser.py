from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
import hashlib  # For password hashing
import uuid     # For generating unique session tokens
from datetime import datetime, timedelta

def add_auth_routes(app, mysql, validate_session, admin_required, log_db_change):
    # Route to fetch members (GET request)
    @app.route('/get-info', methods=['GET'])
    @validate_session
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
    @app.route('/shopstop/members/create', methods=['POST'])
    @validate_session
    @admin_required
    def create_member():
        data = request.json  # Access JSON data from the request

        # Validate input
        required_fields = ['UserName', 'emailID', 'DoB']
        if not data or not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        group_id = data.get('GroupID', 17)
        username = data['UserName']
        email_id = data['emailID']
        dob = data['DoB']

        try:
            cur = mysql.connection.cursor()

            # Insert into members table in CIMS database
            cur.execute(
                "INSERT INTO cs432cims.members (UserName, emailID, DoB) VALUES (%s, %s, %s)",
                (username, email_id, dob)
            )

            # Get the newly created member ID
            member_id = cur.lastrowid

            # Insert into MemberGroupMapping table in CIMS database
            cur.execute(
                "INSERT INTO cs432cims.MemberGroupMapping (GroupID, MemberID) VALUES (%s, %s)",
                (group_id, member_id)
            )

            # Create default password (hashed for security)
            default_password = hashlib.sha256(f"{username}123".encode()).hexdigest()

            # Set default role
            default_role = "User"  # Default role is User, not Admin

            # Insert into Login table in CIMS database
            cur.execute(
                "INSERT INTO cs432cims.Login (MemberID, Password, Role, Session, Expiry) VALUES (%s, %s, %s, %s, %s)",
                (str(member_id), default_password, default_role, None, None)
            )

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="CREATE",
                table="members, MemberGroupMapping, Login",
                data={
                    "member_id": member_id,
                    "username": username,
                    "email": email_id,
                    "group_id": group_id
                },
                user_id=getattr(request, 'user_data', {}).get('MemberID', 'Unknown')
            )

            return jsonify({
                "message": "Member created successfully",
                "member_id": member_id,
                "user": {
                    "UserName": username,
                    "emailID": email_id,
                    "DoB": dob
                }
            }), 201

        except Exception as e:
            # Rollback on error
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            cur.close()

    @app.route('/shopstop/authUser', methods=['POST'])
    def auth_user():
        data = request.json
        print(f"Received login request: {data}")

        # Validate input
        if not data or not all(k in data for k in ('username', 'password')):
            print("Missing credentials in login request")
            return jsonify({"error": "Missing credentials"}), 400

        username = data['username']
        password = data['password']

        try:
            cur = mysql.connection.cursor()

            # Find member by username from CIMS database
            print(f"Looking up username: {username}")
            cur.execute("SELECT ID FROM cs432cims.members WHERE UserName = %s", (username,))
            member = cur.fetchone()

            if not member:
                print(f"Username not found: {username}")
                return jsonify({"error": "Invalid username"}), 401

            member_id = member['ID']
            print(f"Found member ID: {member_id}")

            # For testing purposes, allow direct password comparison for specific test accounts
            # In production, you would always use hashed passwords
            if username == 'admin' and password == 'admin123':
                # Special case for admin user
                cur.execute("SELECT * FROM cs432cims.Login WHERE MemberID = %s", (member_id,))
                login_data = cur.fetchone()
                if not login_data:
                    print(f"No login data found for admin user")
                    return jsonify({"error": "Login data not found"}), 401
            else:
                # Hash the provided password for normal users
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                print(f"Checking credentials for member ID: {member_id}")

                # Check login credentials in CIMS database
                cur.execute(
                    "SELECT * FROM cs432cims.Login WHERE MemberID = %s AND Password = %s",
                    (member_id, hashed_password)
                )
                login_data = cur.fetchone()

                if not login_data:
                    print(f"Invalid password for username: {username}")
                    return jsonify({"error": "Invalid password"}), 401

            # Generate new session token
            session_token = str(uuid.uuid4())
            expiry_time = int((datetime.now() + timedelta(hours=24)).timestamp())  # Convert to epoch time
            print(f"Generated session token: {session_token}, expiry: {expiry_time}")

            # Update session in CIMS database
            cur.execute(
                "UPDATE cs432cims.Login SET Session = %s, Expiry = %s WHERE MemberId = %s",
                (session_token, expiry_time, member_id)
            )

            mysql.connection.commit()
            print(f"Updated session in database for member ID: {member_id}")

            # Log successful login
            log_db_change(
                action="LOGIN",
                table="Login",
                data={"member_id": member_id, "username": username},
                user_id=member_id
            )

            # Verify the session was updated correctly
            cur.execute(
                "SELECT Session, Expiry FROM cs432cims.Login WHERE MemberId = %s",
                (member_id,)
            )
            session_check = cur.fetchone()
            print(f"Session verification: {session_check}")

            response_data = {
                "message": "Authentication successful",
                "session_token": session_token,
                "expiry": expiry_time,
                "role": login_data['Role'],
                "member_id": member_id
            }
            print(f"Sending response: {response_data}")
            return jsonify(response_data), 200

        except Exception as e:
            print(f"Login error: {str(e)}")
            return jsonify({"error": str(e)}), 500
        finally:
            cur.close()

    # Return the app for chaining
    return app



'''
@app.route('/api/auth/login', methods=['POST'])
def auth_user():
    data = request.json

    # Validate input
    if not data or not all(k in data for k in ('username', 'password')):
        return jsonify({"error": "Missing credentials"}), 400

    username = data['username']
    password = data['password']

    try:
        cur = mysql.connection.cursor(dictionary=True)

        # Find member by username
        cur.execute(
            "SELECT ID FROM members WHERE UserName = %s",
            (username,)
        )
        member = cur.fetchone()

        if not member:
            return jsonify({"error": "Invalid username"}), 401

        member_id = member['ID']

        # Hash the provided password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Check login credentials
        cur.execute(
            """SELECT * FROM Login
               WHERE member_id = %s AND password = %s""",
            (member_id, hashed_password)
        )
        login_data = cur.fetchone()

        if not login_data:
            return jsonify({"error": "Invalid password"}), 401

        # Generate new session token
        session_token = str(uuid.uuid4())
        expiry_time = datetime.now() + timedelta(hours=24)

        # Update session in database
        cur.execute(
            """UPDATE Login
               SET session = %s, expiry = %s
               WHERE member_id = %s""",
            (session_token, expiry_time, member_id)
        )

        mysql.connection.commit()

        return jsonify({
            "message": "Authentication successful",
            "session_token": session_token,
            "expiry": expiry_time.isoformat(),
            "role": login_data['role']
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()

'''


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