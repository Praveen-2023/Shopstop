import mysql.connector
import uuid
from datetime import datetime, timedelta

def update_session():
    # Database connection parameters
    db_config = {
        'host': '10.0.116.125',
        'user': 'cs432g17',
        'password': 'qJ5YXTnZ',
        'database': 'cs432cims'
    }
    
    # User details
    username = "Praveen Rathod"
    
    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Get member ID from username
        cursor.execute("SELECT ID FROM members WHERE UserName = %s", (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"User '{username}' not found")
            return
            
        member_id = user['ID']
        print(f"User '{username}' found with ID: {member_id}")
        
        # Generate new session token and expiry
        session_token = str(uuid.uuid4())
        expiry_time = int((datetime.now() + timedelta(hours=24)).timestamp())
        
        # Update session token in database
        cursor.execute(
            "UPDATE Login SET Session = %s, Expiry = %s, Role = 'Admin' WHERE MemberID = %s",
            (session_token, expiry_time, member_id)
        )
        
        conn.commit()
        
        print(f"\nSession token updated for user '{username}'")
        print(f"New Session Token: {session_token}")
        print(f"New Expiry: {expiry_time}")
        print(f"Role: Admin")
        
        # Verify the update
        cursor.execute("SELECT * FROM Login WHERE MemberID = %s", (member_id,))
        login_data = cursor.fetchone()
        
        print("\nVerified Login Information:")
        print(f"Member ID: {login_data['MemberID']}")
        print(f"Role: {login_data['Role']}")
        print(f"Session Token: {login_data['Session']}")
        print(f"Expiry: {login_data['Expiry']}")
        
        # Print instructions for using the new session token
        print("\nTo use this session token:")
        print("1. Open your browser's developer tools (F12)")
        print("2. Go to the Application tab")
        print("3. Select 'Local Storage' on the left")
        print("4. Find and update the 'sessionToken' value with the new token above")
        print("5. Refresh the page")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("\nDatabase connection closed")

if __name__ == "__main__":
    update_session()
