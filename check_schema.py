import mysql.connector

def check_schema():
    # Database connection parameters for cs432g17
    db_config_g17 = {
        'host': '10.0.116.125',
        'user': 'cs432g17',
        'password': 'qJ5YXTnZ',
        'database': 'cs432g17'
    }

    # Database connection parameters for cs432cims
    db_config_cims = {
        'host': '10.0.116.125',
        'user': 'cs432g17',
        'password': 'qJ5YXTnZ',
        'database': 'cs432cims'
    }

    try:
        # Connect to the cs432g17 database
        print("\n=== Checking cs432g17 database ===\n")
        conn_g17 = mysql.connector.connect(**db_config_g17)
        cursor_g17 = conn_g17.cursor(dictionary=True)

        # Get table schema for shop table
        cursor_g17.execute("DESCRIBE shop")
        columns = cursor_g17.fetchall()

        print("Shop Table Schema:")
        for column in columns:
            print(f"Column: {column['Field']}, Type: {column['Type']}, Null: {column['Null']}, Key: {column['Key']}, Default: {column['Default']}")

        # Close cs432g17 connection
        cursor_g17.close()
        conn_g17.close()
        print("\ncs432g17 database connection closed")

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

        # Get table schema for Login table
        cursor_cims.execute("DESCRIBE Login")
        columns = cursor_cims.fetchall()

        print("\nLogin Table Schema:")
        for column in columns:
            print(f"Column: {column['Field']}, Type: {column['Type']}, Null: {column['Null']}, Key: {column['Key']}, Default: {column['Default']}")

        # Get table schema for MemberGroupMapping table
        cursor_cims.execute("DESCRIBE MemberGroupMapping")
        columns = cursor_cims.fetchall()

        print("\nMemberGroupMapping Table Schema:")
        for column in columns:
            print(f"Column: {column['Field']}, Type: {column['Type']}, Null: {column['Null']}, Key: {column['Key']}, Default: {column['Default']}")

        # Close cs432cims connection
        cursor_cims.close()
        conn_cims.close()
        print("\ncs432cims database connection closed")

    except mysql.connector.Error as err:
        print(f"Database error: {err}")

if __name__ == "__main__":
    check_schema()
