from flask import Flask, request, jsonify, g
from flask_mysqldb import MySQL
import logging
from functools import wraps
from datetime import datetime
import os
<<<<<<< HEAD
import re

def add_shop_routes(app, mysql, validate_session, admin_required, log_db_change):
    # Constants
    DB_NAME = 'cs432g17'
=======

def add_shop_routes(app, mysql, validate_session, admin_required, log_db_change):
    # Constants
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
    CIMS_DB = 'cs432cims'

    # CREATE Customer
    @app.route('/customers', methods=['POST'])
    @validate_session
    def create_customer():
        try:
            data = request.json
            if not all(k in data for k in ['name', 'contact', 'email']):
                return jsonify({"error": "Missing required fields"}), 400

<<<<<<< HEAD
            # Validate email format
            if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
                return jsonify({"error": "Invalid email format"}), 400

            # Validate contact number (basic validation)
            if not re.match(r"^\+?[\d\s-]{10,}$", data['contact']):
                return jsonify({"error": "Invalid contact number format"}), 400

            cur = mysql.connection.cursor()
            
            try:
                # Start transaction
                mysql.connection.begin()

                # Get max customer ID with row lock to prevent race conditions
                cur.execute(f"""
                    SELECT MAX(customer_id) as max_id 
                    FROM {CIMS_DB}.G17_customer 
                    FOR UPDATE
                """)
                result = cur.fetchone()

                # Generate new customer ID
                if result['max_id'] is None or result['max_id'] == '':
                    customer_id = "CS0001"
                else:
                    last_id = result['max_id']
                    if last_id.startswith('CS'):
                        num_part = int(last_id[2:]) + 1
                        customer_id = f"CS{num_part:04d}"
                    else:
                        customer_id = f"CS{int(datetime.now().timestamp())}"

=======
            cur = mysql.connection.cursor()
            mysql.connection.begin()

            cur.execute(f"SELECT MAX(customer_id) as max_id FROM {CIMS_DB}.G17_customer")
            result = cur.fetchone()

            # Generate new customer ID
            if result['max_id'] is None or result['max_id'] == '':
                # If no customers exist, start with CS0001
                customer_id = "CS0001"
            else:
                # Extract numeric part, increment, and format
                last_id = result['max_id']
                if last_id.startswith('CS'):
                    num_part = int(last_id[2:]) + 1
                    customer_id = f"CS{num_part:04d}"
                else:
                    # Fallback if format is unexpected
                    customer_id = f"CS{int(datetime.now().timestamp())}"

            try:
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                # Create entry in G17_customer table
                cur.execute(f"""
                    INSERT INTO {CIMS_DB}.G17_customer (customer_id, name, contact, email)
                    VALUES (%s, %s, %s, %s)
                """, (customer_id, data['name'], data['contact'], data['email']))

<<<<<<< HEAD
                # Commit transaction
=======
                # Commit all changes
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                mysql.connection.commit()

                # Log the database change
                log_db_change(
                    action="CREATE",
                    table=f"{CIMS_DB}.G17_customer",
                    data={
                        "customer_id": customer_id,
                        "name": data['name'],
                        "contact": data['contact'],
                        "email": data['email']
                    },
                    user_id=g.user_data['MemberID']
                )

                return jsonify({
                    "status": "success",
                    "message": "Customer created successfully",
                    "customer_id": customer_id
                }), 201

            except Exception as e:
<<<<<<< HEAD
                # Rollback transaction on any error
=======
                # Rollback in case of error
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                mysql.connection.rollback()
                raise e

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # READ Customer
    @app.route('/customers/<customer_id>', methods=['GET'])
    @validate_session
    def get_customer(customer_id):
        try:
            cur = mysql.connection.cursor()
            cur.execute(f"""
                SELECT * FROM {CIMS_DB}.G17_customer
                WHERE customer_id = %s
            """, (customer_id,))

            customer = cur.fetchone()
            if not customer:
                return jsonify({"error": "Customer not found"}), 404

            return jsonify({
                "status": "success",
                "data": {
                    "customer_id": customer['customer_id'],
                    "name": customer['name'],
                    "contact": customer['contact'],
                    "email": customer['email']
                }
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # UPDATE Customer
    @app.route('/customers/<customer_id>', methods=['PUT'])
    @validate_session
    @admin_required
    def update_customer(customer_id):
        try:
            data = request.json
            cur = mysql.connection.cursor()

            # Verify customer exists
            cur.execute(f"SELECT 1 FROM {CIMS_DB}.G17_customer WHERE customer_id = %s", (customer_id,))
            if not cur.fetchone():
                return jsonify({"error": "Customer not found"}), 404

            # Update customer
            update_fields = []
            update_values = []
            if 'name' in data:
                update_fields.append("name = %s")
                update_values.append(data['name'])
            if 'contact' in data:
                update_fields.append("contact = %s")
                update_values.append(data['contact'])
            if 'email' in data:
                update_fields.append("email = %s")
                update_values.append(data['email'])
            if not update_fields:
                return jsonify({"error": "No fields to update"}), 400

            update_values.append(customer_id)
            cur.execute(f"""
                UPDATE {CIMS_DB}.G17_customer
                SET {', '.join(update_fields)}
                WHERE customer_id = %s
            """, update_values)

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="UPDATE",
                table=f"{CIMS_DB}.G17_customer",
                data={
                    "customer_id": customer_id,
                    "updated_fields": list(data.keys())
                },
                user_id=g.user_data['MemberID']
            )

            return jsonify({"status": "success"})

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # DELETE Customer
    @app.route('/customers/<customer_id>', methods=['DELETE'])
    @validate_session
    @admin_required  # Only admins can delete customers
    def delete_customer(customer_id):
        try:
            cur = mysql.connection.cursor()

            # Verify customer exists
            cur.execute(f"SELECT 1 FROM {CIMS_DB}.G17_customer WHERE customer_id = %s", (customer_id,))
            if not cur.fetchone():
                return jsonify({"error": "Customer not found"}), 404

            # Delete customer
            cur.execute(f"DELETE FROM {CIMS_DB}.G17_customer WHERE customer_id = %s", (customer_id,))

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="DELETE",
                table=f"{CIMS_DB}.G17_customer",
                data={"customer_id": customer_id},
                user_id=g.user_data['MemberID']
            )

            return jsonify({"status": "success"})

        except Exception as e:
            return jsonify({"error": str(e)}), 400


    # SHOP CRUD OPERATIONS

<<<<<<< HEAD
    # CREATE Shop (Any authenticated user)
    @app.route('/shops', methods=['POST'])
    @validate_session
=======
    # CREATE Shop (Admin only)
    @app.route('/api/shops', methods=['POST'])
    @validate_session
    @admin_required
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
    def create_shop():
        try:
            data = request.json
            if not all(k in data for k in ['shop_id', 'name', 'address', 'contact', 'member_id']):
                return jsonify({"error": "Missing required fields"}), 400

<<<<<<< HEAD
            # Validate shop_id length (max 5 characters)
            if len(data['shop_id']) > 5:
                return jsonify({"error": "Shop ID must be 5 characters or less"}), 400

=======
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
            member_id = data['member_id']

            cur = mysql.connection.cursor()

            # Verify member exists in CIMS database
<<<<<<< HEAD
            cur.execute(f"SELECT 1 FROM {DB_NAME}.members WHERE ID = %s",
=======
            cur.execute(f"SELECT 1 FROM {CIMS_DB}.members WHERE ID = %s",
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                       (member_id,))
            if not cur.fetchone():
                return jsonify({"error": "Member not found in CIMS database"}), 400

            # Create shop in cs432g17 database
            cur.execute("""
                INSERT INTO cs432g17.shop (shop_id, name, address, contact, member_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (data['shop_id'], data['name'], data['address'],
                 data['contact'], data['member_id']))

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="CREATE",
                table="cs432g17.shop",
                data={
                    "shop_id": data['shop_id'],
                    "name": data['name'],
                    "member_id": data['member_id']
                },
                user_id=g.user_data['MemberID']
            )

            return jsonify({
                "status": "success",
                "message": "Shop created successfully",
                "shop_id": data['shop_id']
            }), 201

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # READ Shop
<<<<<<< HEAD
    @app.route('/shops/<shop_id>', methods=['GET'])
=======
    @app.route('/api/shops/<shop_id>', methods=['GET'])
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
    @validate_session
    def get_shop(shop_id):
        try:
            cur = mysql.connection.cursor()
            # Get shop without joining to members table
            cur.execute("""
                SELECT * FROM cs432g17.shop
                WHERE shop_id = %s
            """, (shop_id,))

            shop = cur.fetchone()
            if not shop:
                return jsonify({"error": "Shop not found"}), 404

            return jsonify({"status": "success", "data": shop})

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # UPDATE Shop
<<<<<<< HEAD
    @app.route('/shops/<shop_id>', methods=['PUT'])
    @validate_session
=======
    @app.route('/api/shops/<shop_id>', methods=['PUT'])
    @validate_session
    @admin_required
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
    def update_shop(shop_id):
        try:
            data = request.json
            cur = mysql.connection.cursor()

            # Verify shop exists
            cur.execute("SELECT 1 FROM cs432g17.shop WHERE shop_id = %s", (shop_id,))
            if not cur.fetchone():
                return jsonify({"error": "Shop not found"}), 404

            # Update shop
            update_fields = []
            update_values = []

            if 'name' in data:
                update_fields.append("name = %s")
                update_values.append(data['name'])

            if 'address' in data:
                update_fields.append("address = %s")
                update_values.append(data['address'])

            if 'contact' in data:
                update_fields.append("contact = %s")
                update_values.append(data['contact'])

            if not update_fields:
                return jsonify({"error": "No fields to update"}), 400

            query = f"UPDATE cs432g17.shop SET {', '.join(update_fields)} WHERE shop_id = %s"
            update_values.append(shop_id)

            cur.execute(query, update_values)
            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="UPDATE",
                table="cs432g17.shop",
                data={
                    "shop_id": shop_id,
                    "updated_fields": list(data.keys())
                },
                user_id=g.user_data['MemberID']
            )

            return jsonify({"status": "success", "message": "Shop updated successfully"})

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # DELETE Shop
<<<<<<< HEAD
    @app.route('/shops/<shop_id>', methods=['DELETE'])
    @validate_session
=======
    @app.route('/api/shops/<shop_id>', methods=['DELETE'])
    @validate_session
    @admin_required
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
    def delete_shop(shop_id):
        try:
            cur = mysql.connection.cursor()

            # Verify shop exists
            cur.execute("SELECT 1 FROM cs432g17.shop WHERE shop_id = %s", (shop_id,))
            if not cur.fetchone():
                return jsonify({"error": "Shop not found"}), 404

            # Delete shop
            cur.execute("DELETE FROM cs432g17.shop WHERE shop_id = %s", (shop_id,))
            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="DELETE",
                table="cs432g17.shop",
                data={"shop_id": shop_id},
                user_id=g.user_data['MemberID']
            )

            return jsonify({"status": "success", "message": "Shop deleted successfully"})

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400

    # List all shops
<<<<<<< HEAD
    @app.route('/shops', methods=['GET'])
=======
    @app.route('/api/shops', methods=['GET'])
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
    @validate_session
    def list_shops():
        try:
            cur = mysql.connection.cursor()
            # Get all shops without joining to members table
            cur.execute("""
                SELECT * FROM cs432g17.shop
                ORDER BY shop_id
            """)

            shops = cur.fetchall()

            # Convert price values from $ to ₹ (if any price fields exist)
            for shop in shops:
                if 'price' in shop:
                    shop['price'] = float(shop['price'])

            return jsonify({"status": "success", "data": shops})

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # Return the app for chaining
    return app
