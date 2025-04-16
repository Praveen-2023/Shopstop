from flask import request, jsonify, g

def add_customer_routes(app, mysql, validate_session, admin_required, log_db_change):
    # Constants
    CIMS_DB = 'cs432cims'

    # Render customers page is defined in main.py

    # Get all customers
    @app.route('/api/customers', methods=['GET'])
    @validate_session
    def get_customers_api():
        """Get all customers from the G17_customer table in cs432cims database."""
        try:
            cur = mysql.connection.cursor()

            # Get all customers from G17_customer table
            cur.execute(f"""
                SELECT * FROM {CIMS_DB}.G17_customer
                ORDER BY customer_id
            """)

            customers = cur.fetchall()
            cur.close()

            # Format the response
            customer_list = []
            for customer in customers:
                customer_list.append({
                    "customer_id": customer['customer_id'],
                    "name": customer['name'],
                    "email": customer['email'],
                    "phone": customer['phone'],
                    "address": customer['address'],
                    "loyalty_points": customer['loyalty_points']
                })

            return jsonify({
                "status": "success",
                "count": len(customer_list),
                "data": customer_list
            })

        except Exception as e:
            print(f"Error getting customers: {str(e)}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    # Get customer by ID
    @app.route('/api/customers/<customer_id>', methods=['GET'])
    @validate_session
    def get_customer_api(customer_id):
        """Get a specific customer by ID."""
        try:
            cur = mysql.connection.cursor()

            # Get customer from G17_customer table
            cur.execute(f"""
                SELECT * FROM {CIMS_DB}.G17_customer
                WHERE customer_id = %s
            """, (customer_id,))

            customer = cur.fetchone()
            cur.close()

            if not customer:
                return jsonify({
                    "status": "error",
                    "error": "Customer not found"
                }), 404

            # Format the response
            customer_data = {
                "customer_id": customer['customer_id'],
                "name": customer['name'],
                "email": customer['email'],
                "phone": customer['phone'],
                "address": customer['address'],
                "loyalty_points": customer['loyalty_points']
            }

            return jsonify({
                "status": "success",
                "data": customer_data
            })

        except Exception as e:
            print(f"Error getting customer: {str(e)}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    # Create new customer
    @app.route('/api/customers', methods=['POST'])
    @validate_session
    @admin_required
    def create_customer_api():
        """Create a new customer."""
        try:
            data = request.json

            # Validate required fields
            required_fields = ['name', 'email', 'phone']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        "status": "error",
                        "error": f"Missing required field: {field}"
                    }), 400

            # Generate a unique customer ID (C + 4 digits)
            cur = mysql.connection.cursor()
            cur.execute(f"""
                SELECT MAX(CAST(SUBSTRING(customer_id, 2) AS UNSIGNED)) as max_id
                FROM {CIMS_DB}.G17_customer
                WHERE customer_id LIKE 'C%'
            """)

            result = cur.fetchone()
            max_id = result['max_id'] if result['max_id'] else 0
            new_id = f"C{(max_id + 1):04d}"

            # Insert new customer
            cur.execute(f"""
                INSERT INTO {CIMS_DB}.G17_customer
                (customer_id, name, email, phone, address, loyalty_points)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                new_id,
                data['name'],
                data['email'],
                data['phone'],
                data.get('address', ''),
                data.get('loyalty_points', 0)
            ))

            mysql.connection.commit()
            cur.close()

            # Log the action
            if hasattr(g, 'user_data'):
                log_db_change(
                    action="CREATE",
                    table=f"{CIMS_DB}.G17_customer",
                    data={"customer_id": new_id},
                    user_id=g.user_data['MemberID']
                )

            return jsonify({
                "status": "success",
                "message": "Customer created successfully",
                "customer_id": new_id
            })

        except Exception as e:
            mysql.connection.rollback()
            print(f"Error creating customer: {str(e)}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    # Update customer
    @app.route('/api/customers/<customer_id>', methods=['PUT'])
    @validate_session
    @admin_required
    def update_customer_api(customer_id):
        """Update an existing customer."""
        try:
            data = request.json

            # Check if customer exists
            cur = mysql.connection.cursor()
            cur.execute(f"""
                SELECT * FROM {CIMS_DB}.G17_customer
                WHERE customer_id = %s
            """, (customer_id,))

            if not cur.fetchone():
                cur.close()
                return jsonify({
                    "status": "error",
                    "error": "Customer not found"
                }), 404

            # Build update query
            update_fields = []
            update_values = []

            if 'name' in data:
                update_fields.append("name = %s")
                update_values.append(data['name'])

            if 'email' in data:
                update_fields.append("email = %s")
                update_values.append(data['email'])

            if 'phone' in data:
                update_fields.append("phone = %s")
                update_values.append(data['phone'])

            if 'address' in data:
                update_fields.append("address = %s")
                update_values.append(data['address'])

            if 'loyalty_points' in data:
                update_fields.append("loyalty_points = %s")
                update_values.append(data['loyalty_points'])

            if not update_fields:
                cur.close()
                return jsonify({
                    "status": "error",
                    "error": "No fields to update"
                }), 400

            # Add customer_id to values
            update_values.append(customer_id)

            # Execute update
            cur.execute(f"""
                UPDATE {CIMS_DB}.G17_customer
                SET {', '.join(update_fields)}
                WHERE customer_id = %s
            """, update_values)

            mysql.connection.commit()
            cur.close()

            # Log the action
            if hasattr(g, 'user_data'):
                log_db_change(
                    action="UPDATE",
                    table=f"{CIMS_DB}.G17_customer",
                    data={"customer_id": customer_id, "updated_fields": list(data.keys())},
                    user_id=g.user_data['MemberID']
                )

            return jsonify({
                "status": "success",
                "message": "Customer updated successfully"
            })

        except Exception as e:
            mysql.connection.rollback()
            print(f"Error updating customer: {str(e)}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    # Delete customer
    @app.route('/api/customers/<customer_id>', methods=['DELETE'])
    @validate_session
    @admin_required
    def delete_customer_api(customer_id):
        """Delete a customer."""
        try:
            # Check if customer exists
            cur = mysql.connection.cursor()
            cur.execute(f"""
                SELECT * FROM {CIMS_DB}.G17_customer
                WHERE customer_id = %s
            """, (customer_id,))

            if not cur.fetchone():
                cur.close()
                return jsonify({
                    "status": "error",
                    "error": "Customer not found"
                }), 404

            # Delete customer
            cur.execute(f"""
                DELETE FROM {CIMS_DB}.G17_customer
                WHERE customer_id = %s
            """, (customer_id,))

            mysql.connection.commit()
            cur.close()

            # Log the action
            if hasattr(g, 'user_data'):
                log_db_change(
                    action="DELETE",
                    table=f"{CIMS_DB}.G17_customer",
                    data={"customer_id": customer_id},
                    user_id=g.user_data['MemberID']
                )

            return jsonify({
                "status": "success",
                "message": "Customer deleted successfully"
            })

        except Exception as e:
            mysql.connection.rollback()
            print(f"Error deleting customer: {str(e)}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    # Return the app for chaining
    return app
