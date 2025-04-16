from flask import Flask, request, jsonify, g
from flask_mysqldb import MySQL

def add_dashboard_routes(app, mysql, validate_session, admin_required, log_db_change):
    # Get shop count
    @app.route('/api/dashboard/shops/count', methods=['GET'])
    @validate_session
    def get_shop_count():
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT COUNT(*) as count FROM cs432g17.shop")
            result = cur.fetchone()
            cur.close()

            return jsonify({
                "status": "success",
                "count": result['count']
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get product count
    @app.route('/api/dashboard/products/count', methods=['GET'])
    @validate_session
    def get_product_count():
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT COUNT(*) as count FROM cs432g17.product")
            result = cur.fetchone()
            cur.close()

            return jsonify({
                "status": "success",
                "count": result['count']
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get customer count
    @app.route('/api/dashboard/customers/count', methods=['GET'])
    @validate_session
    def get_customer_count():
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT COUNT(*) as count FROM cs432cims.G17_customer")
            result = cur.fetchone()
            cur.close()

            return jsonify({
                "status": "success",
                "count": result['count']
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get products by category
    @app.route('/api/dashboard/products/by-category', methods=['GET'])
    @validate_session
    def get_products_by_category():
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT category, COUNT(*) as count
                FROM cs432g17.product
                GROUP BY category
                ORDER BY count DESC
            """)
            categories = cur.fetchall()
            cur.close()

            return jsonify({
                "status": "success",
                "data": categories
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get recent shops
    @app.route('/api/dashboard/shops/recent', methods=['GET'])
    @validate_session
    def get_recent_shops():
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT shop_id, name, address, contact
                FROM cs432g17.shop
                ORDER BY shop_id DESC
                LIMIT 5
            """)
            shops = cur.fetchall()
            cur.close()

            return jsonify({
                "status": "success",
                "data": shops
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get recent products
    @app.route('/api/dashboard/products/recent', methods=['GET'])
    @validate_session
    def get_recent_products():
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT p.product_id, p.name, p.category, p.price, p.stock_quantity, s.name as shop_name
                FROM cs432g17.product p
                LEFT JOIN cs432g17.shop s ON p.shop_id = s.shop_id
                ORDER BY p.product_id DESC
                LIMIT 5
            """)
            products = cur.fetchall()
            cur.close()

            # Format the price as a float
            formatted_products = []
            for product in products:
                product_dict = dict(product)
                product_dict['price'] = float(product_dict['price'])
                formatted_products.append(product_dict)

            return jsonify({
                "status": "success",
                "data": formatted_products
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get recent orders
    @app.route('/api/dashboard/orders/recent', methods=['GET'])
    @validate_session
    def get_recent_orders():
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT o.order_id, o.customer_id, o.shop_id, o.order_date, o.total_amount, o.status,
                       s.name as shop_name
                FROM cs432g17.`order` o
                LEFT JOIN cs432g17.shop s ON o.shop_id = s.shop_id
                ORDER BY o.order_date DESC
                LIMIT 5
            """)
            orders = cur.fetchall()
            cur.close()

            # Format the date and amount
            formatted_orders = []
            for order in orders:
                order_dict = dict(order)
                order_dict['order_date'] = order_dict['order_date'].strftime('%Y-%m-%d %H:%M:%S') if order_dict['order_date'] else None
                order_dict['total_amount'] = float(order_dict['total_amount'])
                formatted_orders.append(order_dict)

            return jsonify({
                "status": "success",
                "data": formatted_orders
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get recent loyalty points
    @app.route('/api/dashboard/loyalty/recent', methods=['GET'])
    @validate_session
    def get_recent_loyalty():
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT l.loyalty_id, l.customer_id, l.shop_id, l.purchase_date, l.purchase_amount, l.loyalty_points,
                       s.name as shop_name
                FROM cs432g17.loyalty l
                LEFT JOIN cs432g17.shop s ON l.shop_id = s.shop_id
                WHERE l.loyalty_points > 0
                ORDER BY l.purchase_date DESC
                LIMIT 5
            """)
            loyalty = cur.fetchall()
            cur.close()

            # Format the date and amount
            formatted_loyalty = []
            for point in loyalty:
                loyalty_dict = dict(point)
                loyalty_dict['purchase_date'] = loyalty_dict['purchase_date'].strftime('%Y-%m-%d') if loyalty_dict['purchase_date'] else None
                loyalty_dict['purchase_amount'] = float(loyalty_dict['purchase_amount'])
                formatted_loyalty.append(loyalty_dict)

            return jsonify({
                "status": "success",
                "data": formatted_loyalty
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get total sales by shop
    @app.route('/api/dashboard/sales/by-shop', methods=['GET'])
    @validate_session
    def get_sales_by_shop():
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT s.shop_id, s.name, SUM(o.total_amount) as total_sales, COUNT(o.order_id) as order_count
                FROM cs432g17.shop s
                LEFT JOIN cs432g17.`order` o ON s.shop_id = o.shop_id
                GROUP BY s.shop_id, s.name
                ORDER BY total_sales DESC
            """)
            sales = cur.fetchall()
            cur.close()

            # Format the total sales
            formatted_sales = []
            for shop in sales:
                shop_dict = dict(shop)
                shop_dict['total_sales'] = float(shop_dict['total_sales']) if shop_dict['total_sales'] else 0
                formatted_sales.append(shop_dict)

            return jsonify({
                "status": "success",
                "data": formatted_sales
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app
