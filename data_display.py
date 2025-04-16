from flask import Flask, request, jsonify, g
from flask_mysqldb import MySQL

def add_data_display_routes(app, mysql, validate_session, admin_required, log_db_change):
    # Get all shops from cs432g17 database
    @app.route('/api/shops', methods=['GET'])
    @validate_session
    def get_all_shops():
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT * FROM cs432g17.shop
                ORDER BY shop_id
            """)

            shops = cur.fetchall()
            cur.close()

            return jsonify({
                "status": "success",
                "data": shops
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get shop by ID from cs432g17 database
    @app.route('/api/shops/<shop_id>', methods=['GET'])
    @validate_session
    def get_shop_by_id(shop_id):
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT * FROM cs432g17.shop
                WHERE shop_id = %s
            """, (shop_id,))

            shop = cur.fetchone()

            if not shop:
                return jsonify({"error": "Shop not found"}), 404

            # Get owner name from cs432cims database
            if shop['member_id']:
                cur.execute("""
                    SELECT name FROM cs432cims.members
                    WHERE ID = %s
                """, (shop['member_id'],))

                member = cur.fetchone()
                if member:
                    shop['owner_name'] = member['name']

            cur.close()

            return jsonify({
                "status": "success",
                "data": shop
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get all products from cs432g17 database
    @app.route('/api/products', methods=['GET'])
    @validate_session
    def get_all_products():
        try:
            cur = mysql.connection.cursor()

            # Check if shop_id filter is provided
            shop_id = request.args.get('shop_id')

            if shop_id:
                cur.execute("""
                    SELECT p.*, s.name as shop_name
                    FROM cs432g17.product p
                    LEFT JOIN cs432g17.shop s ON p.shop_id = s.shop_id
                    WHERE p.shop_id = %s
                    ORDER BY p.product_id
                """, (shop_id,))
            else:
                cur.execute("""
                    SELECT p.*, s.name as shop_name
                    FROM cs432g17.product p
                    LEFT JOIN cs432g17.shop s ON p.shop_id = s.shop_id
                    ORDER BY p.product_id
                """)

            products = cur.fetchall()
            cur.close()

            # Add stock status
            for product in products:
                if product['stock_quantity'] <= 5:
                    product['stock_status'] = 'Low'
                else:
                    product['stock_status'] = 'In Stock'

            return jsonify({
                "status": "success",
                "data": products
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get product by ID from cs432g17 database
    @app.route('/api/products/<int:product_id>', methods=['GET'])
    @validate_session
    def get_product_by_id(product_id):
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT p.*, s.name as shop_name
                FROM cs432g17.product p
                LEFT JOIN cs432g17.shop s ON p.shop_id = s.shop_id
                WHERE p.product_id = %s
            """, (product_id,))

            product = cur.fetchone()

            if not product:
                return jsonify({"error": "Product not found"}), 404

            # Add stock status
            if product['stock_quantity'] <= 5:
                product['stock_status'] = 'Low'
            else:
                product['stock_status'] = 'In Stock'

            cur.close()

            return jsonify({
                "status": "success",
                "data": product
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get all suppliers from cs432g17 database
    @app.route('/api/cs432g17/suppliers', methods=['GET'])
    @validate_session
    def get_all_cs432g17_suppliers():
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT * FROM cs432g17.supplier
                ORDER BY supplier_id
            """)

            suppliers = cur.fetchall()
            cur.close()

            return jsonify({
                "status": "success",
                "data": suppliers
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get supplier by ID from cs432g17 database
    @app.route('/api/suppliers/<supplier_id>', methods=['GET'])
    @validate_session
    def get_supplier_by_id(supplier_id):
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT * FROM cs432g17.supplier
                WHERE supplier_id = %s
            """, (supplier_id,))

            supplier = cur.fetchone()

            if not supplier:
                return jsonify({"error": "Supplier not found"}), 404

            cur.close()

            return jsonify({
                "status": "success",
                "data": supplier
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get all employees from cs432g17 database
    @app.route('/api/cs432g17/employees', methods=['GET'])
    @validate_session
    def get_all_cs432g17_employees():
        try:
            cur = mysql.connection.cursor()

            # Check if shop_id filter is provided
            shop_id = request.args.get('shop_id')

            if shop_id:
                cur.execute("""
                    SELECT e.*, s.name as shop_name
                    FROM cs432g17.employee e
                    LEFT JOIN cs432g17.shop s ON e.shop_id = s.shop_id
                    WHERE e.shop_id = %s
                    ORDER BY e.employee_id
                """, (shop_id,))
            else:
                cur.execute("""
                    SELECT e.*, s.name as shop_name
                    FROM cs432g17.employee e
                    LEFT JOIN cs432g17.shop s ON e.shop_id = s.shop_id
                    ORDER BY e.employee_id
                """)

            employees = cur.fetchall()
            cur.close()

            return jsonify({
                "status": "success",
                "data": employees
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get all orders from cs432g17 database
    @app.route('/api/cs432g17/orders', methods=['GET'])
    @validate_session
    def get_all_cs432g17_orders():
        try:
            cur = mysql.connection.cursor()

            # Check if shop_id filter is provided
            shop_id = request.args.get('shop_id')

            if shop_id:
                cur.execute("""
                    SELECT o.*, s.name as shop_name, c.name as customer_name
                    FROM cs432g17.`order` o
                    LEFT JOIN cs432g17.shop s ON o.shop_id = s.shop_id
                    LEFT JOIN cs432cims.G17_customer c ON o.customer_id = c.customer_id
                    WHERE o.shop_id = %s
                    ORDER BY o.order_date DESC
                """, (shop_id,))
            else:
                cur.execute("""
                    SELECT o.*, s.name as shop_name, c.name as customer_name
                    FROM cs432g17.`order` o
                    LEFT JOIN cs432g17.shop s ON o.shop_id = s.shop_id
                    LEFT JOIN cs432cims.G17_customer c ON o.customer_id = c.customer_id
                    ORDER BY o.order_date DESC
                """)

            orders = cur.fetchall()

            # Format the order_date and total_amount
            for order in orders:
                if order['order_date']:
                    order['order_date'] = order['order_date'].strftime('%Y-%m-%d %H:%M:%S')
                order['total_amount'] = float(order['total_amount'])

            cur.close()

            return jsonify({
                "status": "success",
                "data": orders
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get order details by order ID from cs432g17 database
    @app.route('/api/cs432g17/orders/<int:order_id>/details', methods=['GET'])
    @validate_session
    def get_cs432g17_order_details(order_id):
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT od.*, p.name as product_name
                FROM cs432g17.order_details od
                LEFT JOIN cs432g17.product p ON od.product_id = p.product_id
                WHERE od.order_id = %s
            """, (order_id,))

            order_details = cur.fetchall()

            # Format the price
            for detail in order_details:
                detail['price'] = float(detail['price'])

            cur.close()

            return jsonify({
                "status": "success",
                "data": order_details
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get all loyalty points from cs432g17 database
    @app.route('/api/cs432g17/loyalty', methods=['GET'])
    @validate_session
    def get_all_cs432g17_loyalty():
        try:
            cur = mysql.connection.cursor()

            # Check if customer_id filter is provided
            customer_id = request.args.get('customer_id')

            if customer_id:
                cur.execute("""
                    SELECT l.*, s.name as shop_name, c.name as customer_name
                    FROM cs432g17.loyalty l
                    LEFT JOIN cs432g17.shop s ON l.shop_id = s.shop_id
                    LEFT JOIN cs432cims.G17_customer c ON l.customer_id = c.customer_id
                    WHERE l.customer_id = %s
                    ORDER BY l.purchase_date DESC
                """, (customer_id,))
            else:
                cur.execute("""
                    SELECT l.*, s.name as shop_name, c.name as customer_name
                    FROM cs432g17.loyalty l
                    LEFT JOIN cs432g17.shop s ON l.shop_id = s.shop_id
                    LEFT JOIN cs432cims.G17_customer c ON l.customer_id = c.customer_id
                    ORDER BY l.purchase_date DESC
                """)

            loyalty_points = cur.fetchall()

            # Format the dates and amounts
            for point in loyalty_points:
                if point['purchase_date']:
                    point['purchase_date'] = point['purchase_date'].strftime('%Y-%m-%d')
                if point['points_valid_till']:
                    point['points_valid_till'] = point['points_valid_till'].strftime('%Y-%m-%d')
                point['purchase_amount'] = float(point['purchase_amount'])

            cur.close()

            return jsonify({
                "status": "success",
                "data": loyalty_points
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app
