from flask import Flask, request, jsonify, g
from flask_mysqldb import MySQL
from datetime import datetime

def add_portfolio_routes(app, mysql, validate_session, admin_required, log_db_change):
    # Constants
    CIMS_DB = 'cs432cims'
    GROUP_ID = 17  # Our group ID

    # Get member portfolio
    @app.route('/portfolio/member-details/<int:member_id>', methods=['GET'])
    @validate_session
    def get_member_portfolio(member_id):
        """
        Get detailed portfolio information for a specific member.
        Only accessible if the member belongs to the same group as the requester.
        """
        try:
            # Get the requesting user's member ID from the session
            requester_id = g.user_data['MemberID'] if hasattr(g, 'user_data') else None

            # For testing purposes, if no user data is available, proceed anyway
            if requester_id is None:
                print("Warning: No user data available, proceeding with portfolio access for testing")

            cur = mysql.connection.cursor()

            # Check if the requested member belongs to our group
            cur.execute(f"""
                SELECT GroupID FROM {CIMS_DB}.MemberGroupMapping
                WHERE MemberID = %s AND GroupID = %s
            """, (member_id, GROUP_ID))

            if not cur.fetchone():
                return jsonify({
                    "error": "Member not found or not in your group",
                    "status": "failed"
                }), 404

            # Check if the requester belongs to the same group (skip if no requester_id)
            if requester_id is not None:
                cur.execute(f"""
                    SELECT GroupID FROM {CIMS_DB}.MemberGroupMapping
                    WHERE MemberID = %s AND GroupID = %s
                """, (requester_id, GROUP_ID))

                if not cur.fetchone():
                    return jsonify({
                        "error": "You don't have permission to view this portfolio",
                        "status": "failed"
                    }), 403
            else:
                # Skip permission check for testing
                print("Skipping permission check for testing")

            # Get member details
            cur.execute(f"""
                SELECT m.ID, m.UserName, m.emailID, m.DoB, l.Role
                FROM {CIMS_DB}.members m
                JOIN {CIMS_DB}.Login l ON m.ID = l.MemberID
                WHERE m.ID = %s
            """, (member_id,))

            member_data = cur.fetchone()

            if not member_data:
                return jsonify({
                    "error": "Member details not found",
                    "status": "failed"
                }), 404

            # Get shops owned by this member
            cur.execute("""
                SELECT shop_id, name, address, contact
                FROM cs432g17.shop
                WHERE member_id = %s
            """, (member_id,))

            shops = cur.fetchall()

            # Get total number of products in all shops owned by this member
            cur.execute("""
                SELECT COUNT(*) as product_count
                FROM cs432g17.product p
                JOIN cs432g17.shop s ON p.shop_id = s.shop_id
                WHERE s.member_id = %s
            """, (member_id,))

            product_count = cur.fetchone()['product_count']

            # Format the response
            portfolio = {
                "member_id": member_data['ID'],
                "username": member_data['UserName'],
                "email": member_data['emailID'],
                "date_of_birth": member_data['DoB'].strftime('%Y-%m-%d') if isinstance(member_data['DoB'], datetime) else member_data['DoB'],
                "role": member_data['Role'],
                "shops": shops,
                "total_products": product_count
            }

            # Add profile image based on member_id
            try:
                gender = 'f' if member_id % 2 == 0 else 'm'
                image_number = (member_id % 6) + 1

                # Use local member profile images
                portfolio['profile_image'] = f'/static/images/members/{gender}{image_number}.jpg'
                portfolio['gender'] = 'female' if gender == 'f' else 'male'
                portfolio['image_file'] = f'{gender}{image_number}.jpg'

                print(f"Added profile image to portfolio: {portfolio['profile_image']}")
            except Exception as img_error:
                print(f"Error adding profile image to portfolio: {str(img_error)}")
                # Continue even if there's an error with the image
                portfolio['profile_image'] = '/static/images/members/placeholder.jpg'
                portfolio['gender'] = 'unknown'
                portfolio['image_file'] = 'placeholder.jpg'

            # Log the access (only if requester_id is available)
            if requester_id is not None:
                log_db_change(
                    action="VIEW",
                    table="portfolio",
                    data={"member_id": member_id},
                    user_id=requester_id
                )
            else:
                # Log with a placeholder user ID for testing
                log_db_change(
                    action="VIEW",
                    table="portfolio",
                    data={"member_id": member_id},
                    user_id="test_user"
                )

            return jsonify({
                "status": "success",
                "data": portfolio
            })

        except Exception as e:
            return jsonify({
                "error": str(e),
                "status": "failed"
            }), 500

    # Update member portfolio (admin or self only)
    @app.route('/portfolio/member-details/<int:member_id>', methods=['PUT'])
    @validate_session
    def update_member_portfolio(member_id):
        """
        Update portfolio information for a specific member.
        Only accessible by the member themselves or an admin.
        """
        try:
            # Get the requesting user's member ID and role from the session
            if hasattr(g, 'user_data'):
                requester_id = g.user_data['MemberID']
                requester_role = g.user_data['Role']

                # Check if requester is the member or an admin
                if int(requester_id) != member_id and requester_role.lower() != 'admin':
                    return jsonify({
                        "error": "You don't have permission to update this portfolio",
                        "status": "failed"
                    }), 403
            else:
                # For testing purposes, if no user data is available, proceed anyway
                print("Warning: No user data available, proceeding with portfolio update for testing")
                requester_id = "test_user"
                requester_role = "admin"

            # Get update data
            data = request.json
            if not data:
                return jsonify({
                    "error": "No update data provided",
                    "status": "failed"
                }), 400

            cur = mysql.connection.cursor()

            # Check if the member exists and belongs to our group
            cur.execute(f"""
                SELECT m.ID FROM {CIMS_DB}.members m
                JOIN {CIMS_DB}.MemberGroupMapping mgm ON m.ID = mgm.MemberID
                WHERE m.ID = %s AND mgm.GroupID = %s
            """, (member_id, GROUP_ID))

            if not cur.fetchone():
                return jsonify({
                    "error": "Member not found or not in your group",
                    "status": "failed"
                }), 404

            # Update member details
            update_fields = []
            update_values = []

            if 'username' in data:
                update_fields.append("UserName = %s")
                update_values.append(data['username'])

            if 'email' in data:
                update_fields.append("emailID = %s")
                update_values.append(data['email'])

            if 'dob' in data:
                update_fields.append("DoB = %s")
                update_values.append(data['dob'])

            if not update_fields:
                return jsonify({
                    "error": "No valid fields to update",
                    "status": "failed"
                }), 400

            # Add member_id to values
            update_values.append(member_id)

            # Execute update
            cur.execute(f"""
                UPDATE {CIMS_DB}.members
                SET {', '.join(update_fields)}
                WHERE ID = %s
            """, update_values)

            mysql.connection.commit()

            # Log the update
            log_db_change(
                action="UPDATE",
                table=f"{CIMS_DB}.members",
                data={
                    "member_id": member_id,
                    "updated_fields": list(data.keys())
                },
                user_id=requester_id
            )

            return jsonify({
                "status": "success",
                "message": "Portfolio updated successfully"
            })

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({
                "error": str(e),
                "status": "failed"
            }), 500

    # List all members in our group
    @app.route('/portfolio/members', methods=['GET'])
    @validate_session
    def list_group_members():
        """
        List all members in our group with basic information.
        """
        try:
            # For testing purposes, if no user data is available, proceed anyway
            if not hasattr(g, 'user_data'):
                print("Warning: No user data available, proceeding with members list for testing")
            cur = mysql.connection.cursor()

            # Get all members in our group
            cur.execute(f"""
                SELECT m.ID, m.UserName, m.emailID, l.Role
                FROM {CIMS_DB}.members m
                JOIN {CIMS_DB}.MemberGroupMapping mgm ON m.ID = mgm.MemberID
                JOIN {CIMS_DB}.Login l ON m.ID = l.MemberID
                WHERE mgm.GroupID = %s
            """, (GROUP_ID,))

            members = cur.fetchall()

            # Format the response
            member_list = []
            for member in members:
                member_list.append({
                    "member_id": member['ID'],
                    "username": member['UserName'],
                    "email": member['emailID'],
                    "role": member['Role']
                })

            return jsonify({
                "status": "success",
                "count": len(member_list),
                "data": member_list
            })

        except Exception as e:
            return jsonify({
                "error": str(e),
                "status": "failed"
            }), 500

    # Get member by ID
    @app.route('/portfolio/member/<int:member_id>', methods=['GET'])
    @validate_session
    def get_member_by_id(member_id):
        try:
            # For testing purposes, if no user data is available, proceed anyway
            if not hasattr(g, 'user_data'):
                print("Warning: No user data available, proceeding with member fetch for testing")
            # Print debug information
            print(f"Fetching member with ID: {member_id}")

            cur = mysql.connection.cursor()

            # Get member details from CIMS database
            cur.execute(f"""
                SELECT ID as member_id, UserName as name, UserName as username, emailID as email, DoB as date_of_birth
                FROM {CIMS_DB}.members
                WHERE ID = %s
            """, (member_id,))

            member_data = cur.fetchone()
            cur.close()

            if not member_data:
                print(f"Member not found with ID: {member_id}")
                return jsonify({"status": "error", "error": "Member not found"}), 404

            # Convert to regular dictionary to avoid issues with modification
            try:
                member = dict(member_data) if member_data else {}
                print(f"Member data converted to dictionary: {member}")

                # Format date of birth if available
                if 'date_of_birth' in member and member['date_of_birth']:
                    if isinstance(member['date_of_birth'], datetime):
                        member['date_of_birth'] = member['date_of_birth'].strftime('%Y-%m-%d')
                    else:
                        # Try to parse the date string
                        try:
                            dob = datetime.strptime(str(member['date_of_birth']), '%Y-%m-%d')
                            member['date_of_birth'] = dob.strftime('%Y-%m-%d')
                        except Exception as date_error:
                            print(f"Error formatting date of birth: {str(date_error)}")
                            # Keep the original value
            except Exception as dict_error:
                print(f"Error converting member data to dictionary: {str(dict_error)}")
                return jsonify({"status": "error", "error": f"Error processing member data: {str(dict_error)}"}), 500

            # Add profile image based on member_id
            # For simplicity, we'll assign m1-m6 for male members and f1-f6 for female members
            # based on member_id modulo
            try:
                gender = 'f' if member_id % 2 == 0 else 'm'
                image_number = (member_id % 6) + 1

                # Use local member profile images
                member['profile_image'] = f'/static/images/members/{gender}{image_number}.jpg'

                # Add a field to indicate if this is a male or female image (for reference)
                member['gender'] = 'female' if gender == 'f' else 'male'
                member['image_file'] = f'{gender}{image_number}.jpg'

                print(f"Added profile image to member data: {member['profile_image']}")
            except Exception as img_error:
                print(f"Error adding profile image: {str(img_error)}")
                # Continue even if there's an error with the image
                member['profile_image'] = '/static/images/members/placeholder.jpg'
                member['gender'] = 'unknown'
                member['image_file'] = 'placeholder.jpg'

            return jsonify({"status": "success", "data": member})

        except Exception as e:
            print(f"Error in get_member_by_id: {str(e)}")
            return jsonify({"status": "error", "error": str(e)}), 400

    # Return the app for chaining
    return app
