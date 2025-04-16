from flask import Flask, request, jsonify, g
from flask_mysqldb import MySQL
from datetime import datetime

def add_order_routes(app, mysql, validate_session, admin_required, log_db_change):
    # Constants
<<<<<<< HEAD
    DB_NAME = 'cs432g17'
=======
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
    CIMS_DB = 'cs432cims'

    # CREATE Order with Order Details
    @app.route('/orders', methods=['POST'])
    @validate_session
    def create_order():
        try:
            data = request.json
<<<<<<< HEAD
            if not all(k in data for k in ['customer_id', 'items']):
                return jsonify({"error": "Missing required fields"}), 400

            # Validate items
            if not data['items'] or not isinstance(data['items'], list):
                return jsonify({"error": "Invalid items format"}), 400

            for item in data['items']:
                if not all(k in item for k in ['product_id', 'quantity']):
                    return jsonify({"error": "Each item must have product_id and quantity"}), 400
                if item['quantity'] <= 0:
                    return jsonify({"error": "Quantity must be positive"}), 400

            cur = mysql.connection.cursor()
            
            try:
                # Start transaction
                mysql.connection.begin()

                # Verify customer exists with row lock
                cur.execute(f"""
                    SELECT customer_id 
                    FROM {CIMS_DB}.G17_customer 
                    WHERE customer_id = %s 
                    FOR UPDATE
                """, (data['customer_id'],))
                
                if not cur.fetchone():
                    mysql.connection.rollback()
                    return jsonify({"error": "Customer not found"}), 404

                # Generate order ID
                cur.execute(f"""
                    SELECT MAX(order_id) as max_id 
                    FROM {DB_NAME}.order 
                    FOR UPDATE
                """)
                result = cur.fetchone()
                
                if result['max_id'] is None:
                    order_id = "ORD0001"
                else:
                    last_id = result['max_id']
                    if last_id.startswith('ORD'):
                        num_part = int(last_id[3:]) + 1
                        order_id = f"ORD{num_part:04d}"
                    else:
                        order_id = f"ORD{int(datetime.now().timestamp())}"

                # Create order
                cur.execute(f"""
                    INSERT INTO {DB_NAME}.order (order_id, customer_id, order_date, status)
                    VALUES (%s, %s, NOW(), 'pending')
                """, (order_id, data['customer_id']))

                total_amount = 0
                # Process each item
                for item in data['items']:
                    # Check stock with row lock
                    cur.execute(f"""
                        SELECT price, stock_quantity 
                        FROM {DB_NAME}.product 
                        WHERE product_id = %s 
                        FOR UPDATE
                    """, (item['product_id'],))
                    
                    product = cur.fetchone()
                    if not product:
                        mysql.connection.rollback()
                        return jsonify({"error": f"Product {item['product_id']} not found"}), 404
                    
                    if product['stock_quantity'] < item['quantity']:
                        mysql.connection.rollback()
                        return jsonify({
                            "error": f"Insufficient stock for product {item['product_id']}. Available: {product['stock_quantity']}"
                        }), 400

                    # Update stock
                    cur.execute(f"""
                        UPDATE {DB_NAME}.product 
                        SET stock_quantity = stock_quantity - %s 
                        WHERE product_id = %s
                    """, (item['quantity'], item['product_id']))

                    # Add order detail
                    item_total = product['price'] * item['quantity']
                    total_amount += item_total
                    
                    cur.execute(f"""
                        INSERT INTO {DB_NAME}.order_details 
                        (order_id, product_id, quantity, unit_price)
                        VALUES (%s, %s, %s, %s)
                    """, (order_id, item['product_id'], item['quantity'], product['price']))

                # Update order total
                cur.execute(f"""
                    UPDATE {DB_NAME}.order 
                    SET total_amount = %s 
                    WHERE order_id = %s
                """, (total_amount, order_id))

                # Commit transaction
                mysql.connection.commit()

                # Log the database change
                log_db_change(
                    action="CREATE",
                    table=f"{DB_NAME}.order",
                    data={
                        "order_id": order_id,
                        "customer_id": data['customer_id'],
                        "total_amount": total_amount,
                        "items": data['items']
                    },
                    user_id=g.user_data['MemberID']
                )

                return jsonify({
                    "status": "success",
                    "message": "Order created successfully",
                    "order_id": order_id,
                    "total_amount": total_amount
                }), 201

            except Exception as e:
                # Rollback transaction on any error
                mysql.connection.rollback()
                raise e

        except Exception as e:
=======
            if not all(k in data for k in ['customer_id', 'shop_id', 'total_amount', 'status', 'items']):
                return jsonify({"error": "Missing required fields"}), 400

            # Validate items array
            if not isinstance(data['items'], list) or len(data['items']) == 0:
                return jsonify({"error": "Items must be a non-empty array"}), 400

            for item in data['items']:
                if not all(k in item for k in ['product_id', 'quantity', 'price']):
                    return jsonify({"error": "Each item must have product_id, quantity, and price"}), 400

            cur = mysql.connection.cursor()

            # Verify customer exists if provided
            if data['customer_id']:
                cur.execute("SELECT 1 FROM cs432cims.G17_customer WHERE customer_id = %s", (data['customer_id'],))
                if not cur.fetchone():
                    return jsonify({"error": "Customer not found"}), 404

            # Verify shop exists
            cur.execute("SELECT 1 FROM shop WHERE shop_id = %s", (data['shop_id'],))
            if not cur.fetchone():
                return jsonify({"error": "Shop not found"}), 404

            # Verify products exist and have sufficient stock
            for item in data['items']:
                cur.execute("""
                    SELECT stock_quantity FROM product
                    WHERE product_id = %s
                """, (item['product_id'],))

                product = cur.fetchone()
                if not product:
                    return jsonify({"error": f"Product with ID {item['product_id']} not found"}), 404

                if product['stock_quantity'] < item['quantity']:
                    return jsonify({
                        "error": f"Insufficient stock for product ID {item['product_id']}. Available: {product['stock_quantity']}"
                    }), 400

            # Validate status
            if data['status'] not in ['Pending', 'Completed', 'Cancelled']:
                return jsonify({"error": "Invalid status. Must be 'Pending', 'Completed', or 'Cancelled'"}), 400

            # Create order
            cur.execute("""
                INSERT INTO `order` (customer_id, shop_id, total_amount, status)
                VALUES (%s, %s, %s, %s)
            """, (data['customer_id'], data['shop_id'], data['total_amount'], data['status']))

            # Get the auto-generated order ID
            order_id = cur.lastrowid

            # Create order details
            for item in data['items']:
                cur.execute("""
                    INSERT INTO order_details (order_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, item['product_id'], item['quantity'], item['price']))

                # Update product stock
                if data['status'] == 'Completed':
                    cur.execute("""
                        UPDATE product
                        SET stock_quantity = stock_quantity - %s
                        WHERE product_id = %s
                    """, (item['quantity'], item['product_id']))

            # Create loyalty points if customer exists and order is completed
            if data['customer_id'] and data['status'] == 'Completed':
                # Calculate loyalty points (1 point per $10 spent)
                loyalty_points = int(float(data['total_amount']) / 10)

                if loyalty_points > 0:
                    cur.execute("""
                        INSERT INTO loyalty (customer_id, shop_id, purchase_amount, loyalty_points, purchase_date)
                        VALUES (%s, %s, %s, %s, CURDATE())
                    """, (data['customer_id'], data['shop_id'], data['total_amount'], loyalty_points))

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="CREATE",
                table="order, order_details",
                data={
                    "order_id": order_id,
                    "customer_id": data['customer_id'],
                    "shop_id": data['shop_id'],
                    "total_amount": data['total_amount'],
                    "items_count": len(data['items'])
                },
                user_id=g.user_data['MemberID']
            )

            return jsonify({
                "status": "success",
                "message": "Order created successfully",
                "order_id": order_id
            }), 201

        except Exception as e:
            mysql.connection.rollback()
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
            return jsonify({"error": str(e)}), 400

    # READ Order with Order Details
    @app.route('/orders/<int:order_id>', methods=['GET'])
    @validate_session
    def get_order(order_id):
        try:
            cur = mysql.connection.cursor()

            # Get order
<<<<<<< HEAD
            cur.execute(f"""
                SELECT o.*, c.name as customer_name, s.name as shop_name
                FROM {DB_NAME}.`order` o
                LEFT JOIN {CIMS_DB}.G17_customer c ON o.customer_id = c.customer_id
                LEFT JOIN {DB_NAME}.shop s ON o.shop_id = s.shop_id
=======
            cur.execute("""
                SELECT o.*, c.name as customer_name, s.name as shop_name
                FROM `order` o
                LEFT JOIN cs432cims.G17_customer c ON o.customer_id = c.customer_id
                LEFT JOIN shop s ON o.shop_id = s.shop_id
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                WHERE o.order_id = %s
            """, (order_id,))

            order = cur.fetchone()
            if not order:
                return jsonify({"error": "Order not found"}), 404

            # Get order details
<<<<<<< HEAD
            cur.execute(f"""
                SELECT od.*, p.name as product_name
                FROM {DB_NAME}.order_details od
                JOIN {DB_NAME}.product p ON od.product_id = p.product_id
=======
            cur.execute("""
                SELECT od.*, p.name as product_name
                FROM order_details od
                JOIN product p ON od.product_id = p.product_id
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                WHERE od.order_id = %s
            """, (order_id,))

            order_details = cur.fetchall()

            # Format response
            response = {
                "order_id": order['order_id'],
                "customer_id": order['customer_id'],
                "customer_name": order['customer_name'],
                "shop_id": order['shop_id'],
                "shop_name": order['shop_name'],
                "order_date": order['order_date'].strftime('%Y-%m-%d %H:%M:%S') if order['order_date'] else None,
                "total_amount": float(order['total_amount']),
                "status": order['status'],
                "items": []
            }

            for item in order_details:
                response["items"].append({
                    "order_details_id": item['order_details_id'],
                    "product_id": item['product_id'],
                    "product_name": item['product_name'],
                    "quantity": item['quantity'],
                    "price": float(item['price']),
                    "subtotal": float(item['price']) * item['quantity']
                })

            return jsonify({
                "status": "success",
                "data": response
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # READ All Orders
    @app.route('/orders', methods=['GET'])
    @validate_session
    def get_all_orders():
        try:
            cur = mysql.connection.cursor()

            # Get query parameters
            customer_id = request.args.get('customer_id')
            shop_id = request.args.get('shop_id')
            status = request.args.get('status')

            # Base query
<<<<<<< HEAD
            query = f"""
                SELECT o.*, c.name as customer_name, s.name as shop_name
                FROM {DB_NAME}.`order` o
                LEFT JOIN {CIMS_DB}.G17_customer c ON o.customer_id = c.customer_id
                LEFT JOIN {DB_NAME}.shop s ON o.shop_id = s.shop_id
=======
            query = """
                SELECT o.*, c.name as customer_name, s.name as shop_name
                FROM `order` o
                LEFT JOIN cs432cims.G17_customer c ON o.customer_id = c.customer_id
                LEFT JOIN shop s ON o.shop_id = s.shop_id
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
            """

            params = []
            where_clauses = []

            # Add filters if provided
            if customer_id:
                where_clauses.append("o.customer_id = %s")
                params.append(customer_id)

            if shop_id:
                where_clauses.append("o.shop_id = %s")
                params.append(shop_id)

            if status:
                where_clauses.append("o.status = %s")
                params.append(status)

            # Add WHERE clause if filters exist
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            # Add ORDER BY
            query += " ORDER BY o.order_date DESC"

            # Execute query
            cur.execute(query, params)

            orders = cur.fetchall()

            # Format response
            formatted_orders = []
            for order in orders:
                formatted_orders.append({
                    "order_id": order['order_id'],
                    "customer_id": order['customer_id'],
                    "customer_name": order['customer_name'],
                    "shop_id": order['shop_id'],
                    "shop_name": order['shop_name'],
                    "order_date": order['order_date'].strftime('%Y-%m-%d %H:%M:%S') if order['order_date'] else None,
                    "total_amount": float(order['total_amount']),
                    "status": order['status']
                })

            return jsonify({
                "status": "success",
                "count": len(orders),
                "data": formatted_orders
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # UPDATE Order Status
    @app.route('/orders/<int:order_id>/status', methods=['PUT'])
    @validate_session
    def update_order_status(order_id):
        try:
            data = request.json
            if not data or 'status' not in data:
                return jsonify({"error": "Status is required"}), 400

            # Validate status
            if data['status'] not in ['Pending', 'Completed', 'Cancelled']:
                return jsonify({"error": "Invalid status. Must be 'Pending', 'Completed', or 'Cancelled'"}), 400

            cur = mysql.connection.cursor()

            # Verify order exists
<<<<<<< HEAD
            cur.execute(f"SELECT status FROM {DB_NAME}.`order` WHERE order_id = %s", (order_id,))
=======
            cur.execute("SELECT status FROM `order` WHERE order_id = %s", (order_id,))
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
            order = cur.fetchone()
            if not order:
                return jsonify({"error": "Order not found"}), 404

            current_status = order['status']
            new_status = data['status']

            # If status is not changing, return success
            if current_status == new_status:
                return jsonify({
                    "status": "success",
                    "message": f"Order status is already {new_status}"
                })

            # Handle stock updates based on status change
            if current_status != 'Completed' and new_status == 'Completed':
                # Completing an order - reduce stock
<<<<<<< HEAD
                cur.execute(f"""
                    SELECT od.product_id, od.quantity
                    FROM {DB_NAME}.order_details od
=======
                cur.execute("""
                    SELECT od.product_id, od.quantity
                    FROM order_details od
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                    WHERE od.order_id = %s
                """, (order_id,))

                items = cur.fetchall()

                # Check stock availability
                for item in items:
<<<<<<< HEAD
                    cur.execute(f"""
                        SELECT stock_quantity FROM {DB_NAME}.product
=======
                    cur.execute("""
                        SELECT stock_quantity FROM product
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                        WHERE product_id = %s
                    """, (item['product_id'],))

                    product = cur.fetchone()
                    if product['stock_quantity'] < item['quantity']:
                        return jsonify({
                            "error": f"Insufficient stock for product ID {item['product_id']}. Available: {product['stock_quantity']}"
                        }), 400

                # Update stock for each product
                for item in items:
<<<<<<< HEAD
                    cur.execute(f"""
                        UPDATE {DB_NAME}.product
=======
                    cur.execute("""
                        UPDATE product
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                        SET stock_quantity = stock_quantity - %s
                        WHERE product_id = %s
                    """, (item['quantity'], item['product_id']))

                # Get order details for loyalty points
<<<<<<< HEAD
                cur.execute(f"""
                    SELECT customer_id, shop_id, total_amount
                    FROM {DB_NAME}.`order`
=======
                cur.execute("""
                    SELECT customer_id, shop_id, total_amount
                    FROM `order`
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                    WHERE order_id = %s
                """, (order_id,))

                order_info = cur.fetchone()

                # Create loyalty points if customer exists
                if order_info['customer_id']:
                    # Calculate loyalty points (1 point per $10 spent)
                    loyalty_points = int(float(order_info['total_amount']) / 10)

                    if loyalty_points > 0:
<<<<<<< HEAD
                        cur.execute(f"""
                            INSERT INTO {DB_NAME}.loyalty (customer_id, shop_id, purchase_amount, loyalty_points, purchase_date)
=======
                        cur.execute("""
                            INSERT INTO loyalty (customer_id, shop_id, purchase_amount, loyalty_points, purchase_date)
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                            VALUES (%s, %s, %s, %s, CURDATE())
                        """, (order_info['customer_id'], order_info['shop_id'], order_info['total_amount'], loyalty_points))

            elif current_status == 'Completed' and new_status != 'Completed':
                # Changing from completed to another status - restore stock
<<<<<<< HEAD
                cur.execute(f"""
                    SELECT od.product_id, od.quantity
                    FROM {DB_NAME}.order_details od
=======
                cur.execute("""
                    SELECT od.product_id, od.quantity
                    FROM order_details od
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                    WHERE od.order_id = %s
                """, (order_id,))

                items = cur.fetchall()

                # Restore stock for each product
                for item in items:
<<<<<<< HEAD
                    cur.execute(f"""
                        UPDATE {DB_NAME}.product
=======
                    cur.execute("""
                        UPDATE product
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                        SET stock_quantity = stock_quantity + %s
                        WHERE product_id = %s
                    """, (item['quantity'], item['product_id']))

                # Delete loyalty points if they exist
<<<<<<< HEAD
                cur.execute(f"""
                    DELETE FROM {DB_NAME}.loyalty
                    WHERE EXISTS (
                        SELECT 1 FROM {DB_NAME}.`order` o
=======
                cur.execute("""
                    DELETE FROM loyalty
                    WHERE EXISTS (
                        SELECT 1 FROM `order` o
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                        WHERE o.order_id = %s
                        AND loyalty.customer_id = o.customer_id
                        AND loyalty.shop_id = o.shop_id
                        AND loyalty.purchase_amount = o.total_amount
                        AND DATE(loyalty.purchase_date) = DATE(o.order_date)
                    )
                """, (order_id,))

            # Update order status
<<<<<<< HEAD
            cur.execute(f"""
                UPDATE {DB_NAME}.`order`
=======
            cur.execute("""
                UPDATE `order`
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                SET status = %s
                WHERE order_id = %s
            """, (new_status, order_id))

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="UPDATE",
<<<<<<< HEAD
                table=f"{DB_NAME}.order",
=======
                table="order",
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                data={
                    "order_id": order_id,
                    "status": {
                        "from": current_status,
                        "to": new_status
                    }
                },
                user_id=g.user_data['MemberID']
            )

            return jsonify({
                "status": "success",
                "message": f"Order status updated to {new_status}"
            })

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400

    # DELETE Order
    @app.route('/orders/<int:order_id>', methods=['DELETE'])
    @validate_session
    @admin_required  # Only admins can delete orders
    def delete_order(order_id):
        try:
            cur = mysql.connection.cursor()

            # Verify order exists
<<<<<<< HEAD
            cur.execute(f"SELECT status FROM {DB_NAME}.`order` WHERE order_id = %s", (order_id,))
=======
            cur.execute("SELECT status FROM `order` WHERE order_id = %s", (order_id,))
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
            order = cur.fetchone()
            if not order:
                return jsonify({"error": "Order not found"}), 404

            # If order is completed, restore stock
            if order['status'] == 'Completed':
<<<<<<< HEAD
                cur.execute(f"""
                    SELECT od.product_id, od.quantity
                    FROM {DB_NAME}.order_details od
=======
                cur.execute("""
                    SELECT od.product_id, od.quantity
                    FROM order_details od
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                    WHERE od.order_id = %s
                """, (order_id,))

                items = cur.fetchall()

                # Restore stock for each product
                for item in items:
<<<<<<< HEAD
                    cur.execute(f"""
                        UPDATE {DB_NAME}.product
=======
                    cur.execute("""
                        UPDATE product
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                        SET stock_quantity = stock_quantity + %s
                        WHERE product_id = %s
                    """, (item['quantity'], item['product_id']))

                # Delete loyalty points if they exist
<<<<<<< HEAD
                cur.execute(f"""
                    DELETE FROM {DB_NAME}.loyalty
                    WHERE EXISTS (
                        SELECT 1 FROM {DB_NAME}.`order` o
=======
                cur.execute("""
                    DELETE FROM loyalty
                    WHERE EXISTS (
                        SELECT 1 FROM `order` o
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                        WHERE o.order_id = %s
                        AND loyalty.customer_id = o.customer_id
                        AND loyalty.shop_id = o.shop_id
                        AND loyalty.purchase_amount = o.total_amount
                        AND DATE(loyalty.purchase_date) = DATE(o.order_date)
                    )
                """, (order_id,))

            # Delete order details first (foreign key constraint)
<<<<<<< HEAD
            cur.execute(f"DELETE FROM {DB_NAME}.order_details WHERE order_id = %s", (order_id,))

            # Delete order
            cur.execute(f"DELETE FROM {DB_NAME}.`order` WHERE order_id = %s", (order_id,))
=======
            cur.execute("DELETE FROM order_details WHERE order_id = %s", (order_id,))

            # Delete order
            cur.execute("DELETE FROM `order` WHERE order_id = %s", (order_id,))
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="DELETE",
<<<<<<< HEAD
                table=f"{DB_NAME}.order, {DB_NAME}.order_details",
=======
                table="order, order_details",
>>>>>>> 7d3483573724e77da9871ee364481b5913d41064
                data={"order_id": order_id},
                user_id=g.user_data['MemberID']
            )

            return jsonify({
                "status": "success",
                "message": "Order deleted successfully"
            })

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400

    # Return the app for chaining
    return app
