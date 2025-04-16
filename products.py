from flask import Flask, request, jsonify, g
from flask_mysqldb import MySQL
from datetime import datetime

def add_product_routes(app, mysql, validate_session, admin_required, log_db_change):
    # Constants
    CIMS_DB = 'cs432cims'

    # CREATE Product
    @app.route('/products', methods=['POST'])
    @validate_session
    @admin_required
    def create_product():
        try:
            data = request.json
            cur = mysql.connection.cursor()

            # Verify shop exists
            if 'shop_id' in data:
                cur.execute("SELECT 1 FROM shop WHERE shop_id = %s", (data['shop_id'],))
                if not cur.fetchone():
                    return jsonify({"error": "Shop not found"}), 400

            # Verify supplier exists
            if 'supplier_id' in data:
                cur.execute("SELECT 1 FROM supplier WHERE supplier_id = %s", (data['supplier_id'],))
                if not cur.fetchone():
                    return jsonify({"error": "Supplier not found"}), 400

            # Create product
            cur.execute("""
                INSERT INTO product (name, category, supplier_id, shop_id, price, stock_quantity)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (data['name'], data['category'], data.get('supplier_id'),
                 data.get('shop_id'), data['price'], data['stock_quantity']))

            product_id = cur.lastrowid
            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="CREATE",
                table="product",
                data={
                    "product_id": product_id,
                    "name": data['name'],
                    "shop_id": data.get('shop_id')
                },
                user_id=g.user_data['MemberID']
            )

            return jsonify({"status": "success", "product_id": product_id}), 201

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400

    # READ Product
    @app.route('/products/<int:product_id>', methods=['GET'])
    @validate_session
    def get_product(product_id):
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT * FROM product
                WHERE product_id = %s
            """, (product_id,))

            product = cur.fetchone()
            if not product:
                return jsonify({"error": "Product not found"}), 404

            # Map column indices to names based on your schema
            return jsonify({
                "status": "success",
                "data": {
                    "product_id": product['product_id'],
                    "name": product['name'],
                    "category": product['category'],
                    "supplier_id": product['supplier_id'],
                    "shop_id": product['shop_id'],
                    "price": float(product['price']),
                    "stock_quantity": product['stock_quantity'],
                    "stock_status": product['stock_status'] if 'stock_status' in product else None
                }
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # UPDATE Product
    @app.route('/products/<int:product_id>', methods=['PUT'])
    @validate_session
    @admin_required
    def update_product(product_id):
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No update data provided"}), 400

            cur = mysql.connection.cursor()

            # Verify product exists
            cur.execute("SELECT 1 FROM product WHERE product_id = %s", (product_id,))
            if not cur.fetchone():
                return jsonify({"error": "Product not found"}), 404

            # Update product
            update_fields = []
            update_values = []

            if 'name' in data:
                update_fields.append("name = %s")
                update_values.append(data['name'])

            if 'category' in data:
                update_fields.append("category = %s")
                update_values.append(data['category'])

            if 'supplier_id' in data:
                update_fields.append("supplier_id = %s")
                update_values.append(data['supplier_id'])

            if 'shop_id' in data:
                update_fields.append("shop_id = %s")
                update_values.append(data['shop_id'])

            if 'price' in data:
                update_fields.append("price = %s")
                update_values.append(data['price'])

            if 'stock_quantity' in data:
                update_fields.append("stock_quantity = %s")
                update_values.append(data['stock_quantity'])

            if not update_fields:
                return jsonify({"error": "No valid fields to update"}), 400

            # Add product_id to values
            update_values.append(product_id)

            # Execute update
            cur.execute(f"""
                UPDATE product
                SET {', '.join(update_fields)}
                WHERE product_id = %s
            """, update_values)

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="UPDATE",
                table="product",
                data={
                    "product_id": product_id,
                    "updated_fields": list(data.keys())
                },
                user_id=g.user_data['MemberID']
            )

            return jsonify({"status": "success"})

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400

    # List all products from cs432g17 database
    @app.route('/api/products', methods=['GET'])
    @validate_session
    def list_products():
        try:
            cur = mysql.connection.cursor()

            # Check if shop_id filter is provided
            shop_id = request.args.get('shop_id')

            if shop_id:
                cur.execute("""
                    SELECT p.*, s.name as shop_name
                    FROM cs432g17.product p
                    JOIN cs432g17.shop s ON p.shop_id = s.shop_id
                    WHERE p.shop_id = %s
                    ORDER BY p.product_id
                """, (shop_id,))
            else:
                cur.execute("""
                    SELECT p.*, s.name as shop_name
                    FROM cs432g17.product p
                    JOIN cs432g17.shop s ON p.shop_id = s.shop_id
                    ORDER BY p.product_id
                """)

            products = cur.fetchall()

            # Format price as float and add stock status
            for product in products:
                product['price'] = float(product['price'])
                if product['stock_quantity'] <= 5:
                    product['stock_status'] = 'Low'
                else:
                    product['stock_status'] = 'In Stock'

            return jsonify({"status": "success", "data": products})

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # DELETE Product
    @app.route('/products/<int:product_id>', methods=['DELETE'])
    @validate_session
    @admin_required
    def delete_product(product_id):
        try:
            cur = mysql.connection.cursor()

            # Verify product exists
            cur.execute("SELECT 1 FROM product WHERE product_id = %s", (product_id,))
            if not cur.fetchone():
                return jsonify({"error": "Product not found"}), 404

            # Delete product
            cur.execute("DELETE FROM product WHERE product_id = %s", (product_id,))

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="DELETE",
                table="product",
                data={"product_id": product_id},
                user_id=g.user_data['MemberID']
            )

            return jsonify({"status": "success"})

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400

    # Return the app for chaining
    return app
