from flask import Flask, request, jsonify, g
from flask_mysqldb import MySQL
import hashlib
import uuid
from datetime import datetime, timedelta
import os

def add_delete_routes(app, mysql, validate_session, admin_required, log_db_change):
    @app.route('/shopstop/members/delete', methods=['POST'])
    @validate_session
<<<<<<< HEAD
    # Removed admin_required to allow all users to delete members
=======
    @admin_required
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
    def delete_member():
        """
        Delete a member based on specified criteria:
        1. If member has no other group associations, delete from members and login tables
        2. If member has other group associations, only remove the specific group mapping
        3. Restricted to admin users only
        """

        data = request.json

        # Validate required fields
        if not data or not all(k in data for k in ('memberID', 'groupID')):
            return jsonify({"error": "Missing required fields (memberID and groupID)"}), 400

        member_id = data['memberID']
        group_id = data['groupID']  # The specific group mapping to remove

        try:
            cur = mysql.connection.cursor()

            # Check if the specified group mapping exists in CIMS database
            cur.execute(
                "SELECT COUNT(*) as count FROM cs432cims.MemberGroupMapping WHERE MemberID = %s AND GroupID = %s",
                (member_id, group_id)
            )
            mapping_exists = cur.fetchone()['count'] > 0

            if not mapping_exists:
                return jsonify({"error": f"No mapping found for member {member_id} in group {group_id}"}), 404

            # Check if member is associated with any groups in CIMS database
            cur.execute(
                "SELECT GroupID FROM cs432cims.MemberGroupMapping WHERE MemberID = %s",
                (member_id,)
            )
            groups = cur.fetchall()

            # Determine deletion approach based on group associations
            if len(groups) == 1:
                # Member only belongs to the group being deleted - remove completely from CIMS database
                cur.execute("DELETE FROM cs432cims.MemberGroupMapping WHERE MemberID = %s", (member_id,))
                cur.execute("DELETE FROM cs432cims.Login WHERE MemberID = %s", (member_id,))
                cur.execute("DELETE FROM cs432cims.members WHERE ID = %s", (member_id,))
                message = "Member completely removed from system (only had one group association)"

                # Log complete member deletion
                log_db_change(
                    action="DELETE",
                    table="members, MemberGroupMapping, Login",
                    data={"member_id": member_id, "group_id": group_id, "type": "complete_removal"},
                    user_id=g.user_data['MemberID']
                )
            else:
                # Member belongs to multiple groups - remove only specific mapping from CIMS database
                cur.execute(
                    "DELETE FROM cs432cims.MemberGroupMapping WHERE MemberID = %s AND GroupID = %s",
                    (member_id, group_id)
                )
                message = "Member's association with specified group removed (member retained in system)"

                # Log group mapping removal
                log_db_change(
                    action="DELETE",
                    table="MemberGroupMapping",
                    data={"member_id": member_id, "group_id": group_id, "type": "mapping_removal"},
                    user_id=g.user_data['MemberID']
                )

            mysql.connection.commit()
            return jsonify({"message": message, "success": True}), 200

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            cur.close()

    # Return the app for chaining
    return app
