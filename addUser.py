from flask import Flask, request, jsonify, g
from flask_mysqldb import MySQL
import hashlib
import uuid
from datetime import datetime, timedelta
import os

def add_user_routes(app, mysql, validate_session, admin_required, log_db_change):
    @app.route('/shopstop/members/add', methods=['POST'])
    @validate_session
    @admin_required
    def add_user():
        # User data from request
        data = request.json

        # Validate required fields
        required_fields = ['userName', 'emailID', 'dob', 'role']
        if not data or not all(field in data for field in required_fields):
            return jsonify({
                "error": f"Missing required fields. Please provide: {', '.join(required_fields)}",
                "status": "failed",
                "code": 400
            }), 400

        # Extract user data
        user_name = data['userName']
        email_id = data['emailID']
        dob = data['dob']
        role = data['role']

        try:
            cur = mysql.connection.cursor()

            # Get MemberID of admin from g.user_data
            admin_member_id = g.user_data['MemberID']

            # Get GroupID associated with the admin's MemberID from CIMS database
            cur.execute(
                "SELECT GroupID FROM cs432cims.MemberGroupMapping WHERE MemberID = %s",
                (admin_member_id,)
            )
            group_data = cur.fetchone()

            if not group_data:
                return jsonify({
                    "error": f"No group found for admin MemberID: {admin_member_id}",
                    "status": "failed",
                    "code": 404
                }), 404

            group_id = group_data['GroupID']

            # Check if username already exists in CIMS database
            cur.execute("SELECT COUNT(*) as count FROM cs432cims.members WHERE UserName = %s", (user_name,))
            if cur.fetchone()['count'] > 0:
                return jsonify({
                    "error": "Username already exists",
                    "status": "failed",
                    "code": 409
                }), 409

            # Check if email already exists in CIMS database
            cur.execute("SELECT COUNT(*) as count FROM cs432cims.members WHERE emailID = %s", (email_id,))
            if cur.fetchone()['count'] > 0:
                return jsonify({
                    "error": "Email already exists",
                    "status": "failed",
                    "code": 409
                }), 409

            # Insert into members table in CIMS database
            cur.execute(
                "INSERT INTO cs432cims.members (UserName, emailID, DoB) VALUES (%s, %s, %s)",
                (user_name, email_id, dob)
            )

            # Get the auto-generated member ID
            member_id = cur.lastrowid

            # Insert into MemberGroupMapping table with admin's GroupID in CIMS database
            cur.execute(
                "INSERT INTO cs432cims.MemberGroupMapping (GroupID, MemberID) VALUES (%s, %s)",
                (group_id, member_id)
            )

            # Hash the password
            hashed_password = hashlib.sha256(f"{user_name}123".encode()).hexdigest()

            # Insert into Login table in CIMS database
            cur.execute(
                "INSERT INTO cs432cims.Login (MemberID, Password, Role) VALUES (%s, %s, %s)",
                (str(member_id), hashed_password, role)
            )

            # Commit all changes
            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="CREATE",
                table="members, MemberGroupMapping, Login",
                data={
                    "member_id": member_id,
                    "username": user_name,
                    "email": email_id,
                    "role": role,
                    "group_id": group_id
                },
                user_id=admin_member_id
            )

            # Return success response
            return jsonify({
                "message": "User created successfully",
                "status": "success",
                "member_id": member_id,
                "group_id": group_id,
                "user": {
                    "userName": user_name,
                    "emailID": email_id,
                    "role": role,
                    "groupID": group_id
                }
            }), 201

        except Exception as e:
            # Rollback on error
            mysql.connection.rollback()
            return jsonify({
                "error": str(e),
                "status": "failed",
                "code": 500
            }), 500
        finally:
            cur.close()


    # Return the app for chaining
    return app
