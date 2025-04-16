import mysql.connector
import json

def check_db_alignment():
    # Database connection parameters for cs432cims
    db_config_cims = {
        'host': '10.0.116.125',
        'user': 'cs432g17',
        'password': 'qJ5YXTnZ',
        'database': 'cs432cims'
    }
    
    try:
        # Connect to the cs432cims database
        print("\n=== Checking cs432cims database ===\n")
        conn_cims = mysql.connector.connect(**db_config_cims)
        cursor_cims = conn_cims.cursor(dictionary=True)
        
        # Get table schema for members table
        cursor_cims.execute("DESCRIBE members")
        columns = cursor_cims.fetchall()
        
        print("Members Table Schema:")
        for column in columns:
            print(f"Column: {column['Field']}, Type: {column['Type']}, Null: {column['Null']}, Key: {column['Key']}, Default: {column['Default']}")
        
        # Get sample data from members table
        cursor_cims.execute("SELECT * FROM members LIMIT 5")
        members_data = cursor_cims.fetchall()
        
        print("\nSample Members Data:")
        for member in members_data:
            print(json.dumps(member, default=str))
        
        # Get table schema for Login table
        cursor_cims.execute("DESCRIBE Login")
        columns = cursor_cims.fetchall()
        
        print("\nLogin Table Schema:")
        for column in columns:
            print(f"Column: {column['Field']}, Type: {column['Type']}, Null: {column['Null']}, Key: {column['Key']}, Default: {column['Default']}")
        
        # Get sample data from Login table
        cursor_cims.execute("SELECT * FROM Login LIMIT 5")
        login_data = cursor_cims.fetchall()
        
        print("\nSample Login Data:")
        for login in login_data:
            # Don't print the actual password
            if 'Password' in login:
                login['Password'] = '***HIDDEN***'
            print(json.dumps(login, default=str))
        
        # Get table schema for MemberGroupMapping table
        cursor_cims.execute("DESCRIBE MemberGroupMapping")
        columns = cursor_cims.fetchall()
        
        print("\nMemberGroupMapping Table Schema:")
        for column in columns:
            print(f"Column: {column['Field']}, Type: {column['Type']}, Null: {column['Null']}, Key: {column['Key']}, Default: {column['Default']}")
        
        # Get sample data from MemberGroupMapping table
        cursor_cims.execute("SELECT * FROM MemberGroupMapping LIMIT 5")
        mapping_data = cursor_cims.fetchall()
        
        print("\nSample MemberGroupMapping Data:")
        for mapping in mapping_data:
            print(json.dumps(mapping, default=str))
        
        # Check for data consistency between tables
        print("\n=== Checking Data Consistency ===\n")
        
        # Check if all members in Login table exist in members table
        cursor_cims.execute("""
            SELECT l.MemberID, m.ID, m.UserName
            FROM Login l
            LEFT JOIN members m ON l.MemberID = m.ID
            WHERE m.ID IS NULL
            LIMIT 10
        """)
        missing_members = cursor_cims.fetchall()
        
        if missing_members:
            print("Members in Login table that don't exist in members table:")
            for member in missing_members:
                print(json.dumps(member, default=str))
        else:
            print("All members in Login table exist in members table.")
        
        # Check if all members in MemberGroupMapping table exist in members table
        cursor_cims.execute("""
            SELECT mgm.MemberID, m.ID, m.UserName
            FROM MemberGroupMapping mgm
            LEFT JOIN members m ON mgm.MemberID = m.ID
            WHERE m.ID IS NULL
            LIMIT 10
        """)
        missing_members = cursor_cims.fetchall()
        
        if missing_members:
            print("\nMembers in MemberGroupMapping table that don't exist in members table:")
            for member in missing_members:
                print(json.dumps(member, default=str))
        else:
            print("\nAll members in MemberGroupMapping table exist in members table.")
        
        # Check data types
        print("\n=== Checking Data Types ===\n")
        
        # Check MemberID data type in Login table
        cursor_cims.execute("SELECT MemberID, typeof(MemberID) as type FROM Login LIMIT 5")
        try:
            member_id_types = cursor_cims.fetchall()
            print("MemberID data types in Login table:")
            for item in member_id_types:
                print(json.dumps(item, default=str))
        except Exception as e:
            print(f"Error checking MemberID data type in Login table: {str(e)}")
            # Alternative approach
            cursor_cims.execute("SELECT MemberID FROM Login LIMIT 5")
            member_ids = cursor_cims.fetchall()
            print("MemberID samples in Login table:")
            for item in member_ids:
                print(f"MemberID: {item['MemberID']}, Type: {type(item['MemberID'])}")
        
        # Close connection
        cursor_cims.close()
        conn_cims.close()
        print("\ncs432cims database connection closed")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")

if __name__ == "__main__":
    check_db_alignment()
