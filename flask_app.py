from flask import Flask, request, jsonify  # Import 'request' here
# import mysql.connector
# from datetime import date
from flask_mysqldb import MySQL

app = Flask(__name__)

# Configure MySQL connection
app.config['MYSQL_HOST'] = '10.0.116.125'  # Replace with your host
app.config['MYSQL_USER'] = 'cs432g17'      # Replace with your username
app.config['MYSQL_PASSWORD'] = 'qJ5YXTnZ' # Replace with your password
app.config['MYSQL_DB'] = 'cs432cims'      # Replace with your database name

mysql = MySQL(app)

@app.route('/get-info', methods=['GET'])
def test_db():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM members LIMIT 5;")
        rows = cur.fetchall()
        return jsonify({"status": "success", "data": rows})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

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
        conn = mysql.connection()
        cursor = conn.cursor()
        
        # Insert into members table
        cursor.execute(
            "INSERT INTO members (UserName, emailID, DoB) VALUES (%s, %s, %s)",
            (username, email_id, dob)
        )
        
        conn.commit()
        
        return jsonify({"message": "Member created successfully", "member_id": cursor.lastrowid}), 201
    
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    # finally:
    #     if 'conn' in locals() and conn.is_connected():
    #         cursor.close()
    #         conn.close()


if __name__== '_main_':
    app.run(host='0.0.0.0', port=5000, debug=True)