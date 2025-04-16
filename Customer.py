from flask import Flask, request, jsonify, g
from flask_mysqldb import MySQL
from datetime import datetime

def add_customer_routes(app, mysql, validate_session, admin_required, log_db_change):
    # Constants
    CIMS_DB = 'cs432cims'
<<<<<<< HEAD
    DB_NAME = 'cs432g17'
=======
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064

    # CREATE Customer
    @app.route('/customers/create', methods=['POST'])
    @validate_session
    def create_customer_record():
        try:
            data = request.json
            if not all(k in data for k in ['customer_id', 'name', 'contact', 'email']):
                return jsonify({"error": "Missing required fields"}), 400

            cur = mysql.connection.cursor()

            # Create customer in CIMS database
<<<<<<< HEAD
            cur.execute(f"""
                INSERT INTO {CIMS_DB}.G17_customer (customer_id, name, contact, email)
=======
            cur.execute("""
                INSERT INTO cs432cims.G17_customer (customer_id, name, contact, email)
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                VALUES (%s, %s, %s, %s)
            """, (data['customer_id'], data['name'], data['contact'], data['email']))

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="CREATE",
<<<<<<< HEAD
                table=f"{CIMS_DB}.G17_customer",
=======
                table="customer",
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                data={
                    "customer_id": data['customer_id'],
                    "name": data['name']
                },
                user_id=g.user_data['MemberID']
            )

            return jsonify({"status": "success", "customer_id": data['customer_id']}), 201

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400

    # READ Customer
    @app.route('/customers/get/<customer_id>', methods=['GET'])
    @validate_session
    def get_customer_record(customer_id):
        try:
            cur = mysql.connection.cursor()
<<<<<<< HEAD
            cur.execute(f"""
                SELECT * FROM {CIMS_DB}.G17_customer
=======
            cur.execute("""
                SELECT * FROM cs432cims.G17_customer
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
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
    @app.route('/customers/update/<customer_id>', methods=['PUT'])
    @validate_session
    def update_customer_record(customer_id):
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No update data provided"}), 400

            cur = mysql.connection.cursor()

            # Verify customer exists in CIMS database
<<<<<<< HEAD
            cur.execute(f"SELECT 1 FROM {CIMS_DB}.G17_customer WHERE customer_id = %s", (customer_id,))
=======
            cur.execute("SELECT 1 FROM cs432cims.G17_customer WHERE customer_id = %s", (customer_id,))
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
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
                return jsonify({"error": "No valid fields to update"}), 400

            # Add customer_id to values
            update_values.append(customer_id)

            # Execute update in CIMS database
            cur.execute(f"""
<<<<<<< HEAD
                UPDATE {CIMS_DB}.G17_customer
=======
                UPDATE cs432cims.G17_customer
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                SET {', '.join(update_fields)}
                WHERE customer_id = %s
            """, update_values)

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="UPDATE",
<<<<<<< HEAD
                table=f"{CIMS_DB}.G17_customer",
=======
                table="customer",
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                data={
                    "customer_id": customer_id,
                    "updated_fields": list(data.keys())
                },
                user_id=g.user_data['MemberID']
            )

            return jsonify({"status": "success"})

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400

    # DELETE Customer
    @app.route('/customers/delete/<customer_id>', methods=['DELETE'])
    @validate_session
    @admin_required  # Only admins can delete customers
    def delete_customer_record(customer_id):
        try:
            cur = mysql.connection.cursor()

            # Verify customer exists in CIMS database
<<<<<<< HEAD
            cur.execute(f"SELECT 1 FROM {CIMS_DB}.G17_customer WHERE customer_id = %s", (customer_id,))
=======
            cur.execute("SELECT 1 FROM cs432cims.G17_customer WHERE customer_id = %s", (customer_id,))
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
            if not cur.fetchone():
                return jsonify({"error": "Customer not found"}), 404

            # Delete customer from CIMS database
<<<<<<< HEAD
            cur.execute(f"DELETE FROM {CIMS_DB}.G17_customer WHERE customer_id = %s", (customer_id,))
=======
            cur.execute("DELETE FROM cs432cims.G17_customer WHERE customer_id = %s", (customer_id,))
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="DELETE",
<<<<<<< HEAD
                table=f"{CIMS_DB}.G17_customer",
=======
                table="customer",
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                data={"customer_id": customer_id},
                user_id=g.user_data['MemberID']
            )

            return jsonify({"status": "success"})

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400

    # Get Customer Loyalty Information
    @app.route('/customers/loyalty/<customer_id>', methods=['GET'])
    @validate_session
    def get_customer_loyalty(customer_id):
        try:
            cur = mysql.connection.cursor()

            # Verify customer exists in CIMS database
<<<<<<< HEAD
            cur.execute(f"SELECT 1 FROM {CIMS_DB}.G17_customer WHERE customer_id = %s", (customer_id,))
=======
            cur.execute("SELECT 1 FROM cs432cims.G17_customer WHERE customer_id = %s", (customer_id,))
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
            if not cur.fetchone():
                return jsonify({"error": "Customer not found"}), 404

            # Get customer loyalty information from cs432g17 database
<<<<<<< HEAD
            cur.execute(f"""
                SELECT l.*, s.name as shop_name
                FROM {DB_NAME}.loyalty l
                JOIN {DB_NAME}.shop s ON l.shop_id = s.shop_id
=======
            cur.execute("""
                SELECT l.*, s.name as shop_name
                FROM cs432g17.loyalty l
                JOIN cs432g17.shop s ON l.shop_id = s.shop_id
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                WHERE l.customer_id = %s
                ORDER BY l.purchase_date DESC
            """, (customer_id,))

            loyalty_points = cur.fetchall()

            # Format the dates and amounts
            formatted_loyalty = []
            for point in loyalty_points:
                formatted_point = {
                    'loyalty_id': point['loyalty_id'],
                    'customer_id': point['customer_id'],
                    'shop_id': point['shop_id'],
                    'shop_name': point['shop_name'],
                    'purchase_date': point['purchase_date'].strftime('%Y-%m-%d') if point['purchase_date'] else None,
                    'purchase_amount': float(point['purchase_amount']),
                    'loyalty_points': point['loyalty_points'],
                    'points_valid_till': point['points_valid_till'].strftime('%Y-%m-%d') if point['points_valid_till'] else None
                }
                formatted_loyalty.append(formatted_point)

            # Calculate total loyalty points
            total_points = sum(point['loyalty_points'] for point in loyalty_points)

            # Get customer order history
<<<<<<< HEAD
            cur.execute(f"""
                SELECT o.*, s.name as shop_name
                FROM {DB_NAME}.`order` o
                JOIN {DB_NAME}.shop s ON o.shop_id = s.shop_id
=======
            cur.execute("""
                SELECT o.*, s.name as shop_name
                FROM cs432g17.`order` o
                JOIN cs432g17.shop s ON o.shop_id = s.shop_id
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                WHERE o.customer_id = %s
                ORDER BY o.order_date DESC
            """, (customer_id,))

            orders = cur.fetchall()

            # Format the order dates and amounts
            formatted_orders = []
            for order in orders:
                formatted_order = {
                    'order_id': order['order_id'],
                    'customer_id': order['customer_id'],
                    'shop_id': order['shop_id'],
                    'shop_name': order['shop_name'],
                    'order_date': order['order_date'].strftime('%Y-%m-%d %H:%M:%S') if order['order_date'] else None,
                    'total_amount': float(order['total_amount']),
                    'status': order['status']
                }
                formatted_orders.append(formatted_order)

            return jsonify({
                "status": "success",
                "data": {
                    "loyalty_points": formatted_loyalty,
                    "total_points": total_points,
                    "orders": formatted_orders,
                    "total_orders": len(formatted_orders)
                }
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # Return the app for chaining
    return app
