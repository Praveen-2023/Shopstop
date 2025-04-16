import mysql.connector
import hashlib

def add_test_member():
    # Database connection parameters for cs432cims
    db_config_cims = {
        'host': '10.0.116.125',
        'user': 'cs432g17',
        'password': 'qJ5YXTnZ',
        'database': 'cs432cims'
    }
    
    try:
        # Connect to the cs432cims database
        print("\n=== Adding test member to cs432cims database ===\n")
        conn_cims = mysql.connector.connect(**db_config_cims)
        cursor_cims = conn_cims.cursor(dictionary=True)
        
        # Generate a unique ID for the new member
        cursor_cims.execute("SELECT MAX(ID) as max_id FROM members")
        result = cursor_cims.fetchone()
        max_id = result['max_id'] if result and result['max_id'] else 0
        member_id = max_id + 1
        print(f"Generated new member ID: {member_id}")
        
        # Member data
        user_name = f"test_user_{member_id}"
        email_id = f"test{member_id}@example.com"
        dob = "1990-01-01"
        role = "User"
        group_id = 17  # Our group ID
        
        # Insert into members table
        print(f"Inserting into members table with ID: {member_id}, UserName: {user_name}, emailID: {email_id}, DoB: {dob}")
        cursor_cims.execute(
            "INSERT INTO members (ID, UserName, emailID, DoB) VALUES (%s, %s, %s, %s)",
            (member_id, user_name, email_id, dob)
        )
        
        # Insert into MemberGroupMapping table
        print(f"Inserting into MemberGroupMapping table with GroupID: {group_id}, MemberID: {member_id}")
        cursor_cims.execute(
            "INSERT INTO MemberGroupMapping (GroupID, MemberID) VALUES (%s, %s)",
            (group_id, member_id)
        )
        
        # Hash the password
        password = f"{user_name}123"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Insert into Login table
        member_id_str = str(member_id)
        print(f"Inserting into Login table with MemberID: {member_id_str}, Role: {role}")
        cursor_cims.execute(
            "INSERT INTO Login (MemberID, Password, Role) VALUES (%s, %s, %s)",
            (member_id_str, hashed_password, role)
        )
        
        # Commit changes
        conn_cims.commit()
        print(f"\nMember added successfully with ID: {member_id}, Username: {user_name}")
        
        # Verify the member was added
        cursor_cims.execute("SELECT * FROM members WHERE ID = %s", (member_id,))
        member = cursor_cims.fetchone()
        print("\nMember data in members table:")
        print(member)
        
        cursor_cims.execute("SELECT * FROM Login WHERE MemberID = %s", (member_id_str,))
        login = cursor_cims.fetchone()
        print("\nMember data in Login table:")
        if login:
            login_copy = login.copy()
            login_copy['Password'] = '***HIDDEN***'
            print(login_copy)
        else:
            print("No login data found")
        
        cursor_cims.execute("SELECT * FROM MemberGroupMapping WHERE MemberID = %s", (member_id,))
        mapping = cursor_cims.fetchone()
        print("\nMember data in MemberGroupMapping table:")
        print(mapping)
        
        # Close connection
        cursor_cims.close()
        conn_cims.close()
        print("\ncs432cims database connection closed")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        if 'conn_cims' in locals() and conn_cims.is_connected():
            conn_cims.rollback()
            print("Transaction rolled back")

if __name__ == "__main__":
    add_test_member()
