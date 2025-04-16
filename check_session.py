import mysql.connector

def check_session():
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
        
        # Get login information
        cursor.execute("SELECT * FROM Login WHERE MemberID = %s", (member_id,))
        login_data = cursor.fetchone()
        
        if not login_data:
            print(f"No login data found for user '{username}'")
            return
            
        print("\nLogin Information:")
        print(f"Member ID: {login_data['MemberID']}")
        print(f"Role: {login_data['Role']}")
        print(f"Session Token: {login_data['Session']}")
        print(f"Expiry: {login_data['Expiry']}")
        
        # Check if session is valid
        import time
        current_time = int(time.time())
        if login_data['Expiry'] and login_data['Expiry'] > current_time:
            print(f"Session is valid until: {login_data['Expiry']} (current time: {current_time})")
        else:
            print(f"Session is expired or not set. Expiry: {login_data['Expiry']}, current time: {current_time}")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("\nDatabase connection closed")

if __name__ == "__main__":
    check_session()
