import mysql.connector
import requests
import json

def test_admin_access():
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
        
        # Test admin access with the session token
        session_token = login_data['Session']
        
        # Test the /api/check-role endpoint
        try:
            response = requests.get(
                'http://localhost:5000/api/check-role',
                headers={'Authorization': session_token}
            )
            
            print("\nAPI Check Role Response:")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error testing API: {str(e)}")
        
        # Test an admin-required endpoint
        try:
            test_data = {
                "shop_id": f"TEST{int(member_id) % 1000}",
                "name": "Test Shop",
                "address": "Test Address",
                "contact": "1234567890",
                "member_id": member_id
            }
            
            response = requests.post(
                'http://localhost:5000/shops',
                headers={
                    'Authorization': session_token,
                    'Content-Type': 'application/json'
                },
                json=test_data
            )
            
            print("\nAdmin Endpoint Test Response:")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error testing admin endpoint: {str(e)}")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("\nDatabase connection closed")

if __name__ == "__main__":
    test_admin_access()
