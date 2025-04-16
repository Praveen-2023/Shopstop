import mysql.connector
import hashlib
import uuid
from datetime import datetime, timedelta

def add_admin_user():
    # Database connection parameters
    db_config = {
        'host': '10.0.116.125',
        'user': 'cs432g17',
        'password': 'qJ5YXTnZ',
        'database': 'cs432cims'
    }
    
    # User details
    username = "Praveen Rathod"
    password = "Praveen Rathod123"
    email = "praveen.rathod@example.com"
    dob = "2000-01-01"  # Format: YYYY-MM-DD
    
    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Check if user already exists
        cursor.execute("SELECT ID FROM members WHERE UserName = %s", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            member_id = existing_user['ID']
            print(f"User '{username}' already exists with ID: {member_id}")
            
            # Update the role to Admin
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            # Check if login entry exists
            cursor.execute("SELECT 1 FROM Login WHERE MemberID = %s", (member_id,))
            login_exists = cursor.fetchone()
            
            if login_exists:
                # Update existing login entry
                cursor.execute(
                    "UPDATE Login SET Role = 'Admin', Password = %s WHERE MemberID = %s",
                    (hashed_password, member_id)
                )
                print(f"Updated user '{username}' to Admin role")
            else:
                # Create new login entry
                session_token = str(uuid.uuid4())
                expiry_time = int((datetime.now() + timedelta(hours=24)).timestamp())
                
                cursor.execute(
                    "INSERT INTO Login (MemberID, Password, Role, Session, Expiry) VALUES (%s, %s, %s, %s, %s)",
                    (member_id, hashed_password, "Admin", session_token, expiry_time)
                )
                print(f"Created login entry for user '{username}' with Admin role")
        else:
            # Create new user
            cursor.execute(
                "INSERT INTO members (UserName, emailID, DoB) VALUES (%s, %s, %s)",
                (username, email, dob)
            )
            
            # Get the newly created member ID
            member_id = cursor.lastrowid
            print(f"Created new user '{username}' with ID: {member_id}")
            
            # Create login entry with Admin role
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            session_token = str(uuid.uuid4())
            expiry_time = int((datetime.now() + timedelta(hours=24)).timestamp())
            
            cursor.execute(
                "INSERT INTO Login (MemberID, Password, Role, Session, Expiry) VALUES (%s, %s, %s, %s, %s)",
                (member_id, hashed_password, "Admin", session_token, expiry_time)
            )
            print(f"Created login entry for user '{username}' with Admin role")
        
        # Commit changes
        conn.commit()
        print("Changes committed to database")
        
        # Print login information
        print("\nAdmin User Created/Updated:")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"Role: Admin")
        print(f"Member ID: {member_id}")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed")

if __name__ == "__main__":
    add_admin_user()
