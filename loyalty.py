from flask import Flask, request, jsonify, g
from flask_mysqldb import MySQL
from datetime import datetime, date, timedelta

def add_loyalty_routes(app, mysql, validate_session, admin_required, log_db_change):
    # Constants
    CIMS_DB = 'cs432cims'

    # CREATE Loyalty Points (usually created automatically when an order is completed)
    @app.route('/loyalty', methods=['POST'])
    @validate_session
    @admin_required  # Only admins can manually create loyalty points
    def create_loyalty():
        try:
            data = request.json
            if not all(k in data for k in ['customer_id', 'shop_id', 'purchase_amount', 'loyalty_points', 'purchase_date']):
                return jsonify({"error": "Missing required fields"}), 400

            cur = mysql.connection.cursor()

            # Verify customer exists
            cur.execute("SELECT 1 FROM cs432cims.G17_customer WHERE customer_id = %s", (data['customer_id'],))
            if not cur.fetchone():
                return jsonify({"error": "Customer not found"}), 404

            # Verify shop exists
            cur.execute("SELECT 1 FROM shop WHERE shop_id = %s", (data['shop_id'],))
            if not cur.fetchone():
                return jsonify({"error": "Shop not found"}), 404

            # Create loyalty record
            cur.execute("""
                INSERT INTO loyalty (customer_id, shop_id, purchase_amount, loyalty_points, purchase_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                data['customer_id'],
                data['shop_id'],
                data['purchase_amount'],
                data['loyalty_points'],
                data['purchase_date']
            ))

            # Get the auto-generated loyalty ID
            loyalty_id = cur.lastrowid

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="CREATE",
                table="loyalty",
                data={
                    "loyalty_id": loyalty_id,
                    "customer_id": data['customer_id'],
                    "shop_id": data['shop_id'],
                    "loyalty_points": data['loyalty_points']
                },
                user_id=g.user_data['MemberID']
            )

            return jsonify({
                "status": "success",
                "message": "Loyalty points added successfully",
                "loyalty_id": loyalty_id
            }), 201

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400

    # READ Loyalty Points for a Customer
    @app.route('/loyalty/customer/<customer_id>', methods=['GET'])
    @validate_session
    def get_loyalty_for_customer(customer_id):
        try:
            cur = mysql.connection.cursor()

            # Verify customer exists
            cur.execute("SELECT name FROM cs432cims.G17_customer WHERE customer_id = %s", (customer_id,))
            customer = cur.fetchone()
            if not customer:
                return jsonify({"error": "Customer not found"}), 404

            # Get loyalty points
            cur.execute("""
                SELECT l.*, s.name as shop_name
                FROM loyalty l
                JOIN shop s ON l.shop_id = s.shop_id
                WHERE l.customer_id = %s
                ORDER BY l.purchase_date DESC
            """, (customer_id,))

            loyalty_records = cur.fetchall()

            # Calculate total valid points
            today = date.today()
            total_valid_points = 0

            # Format response
            formatted_records = []
            for record in loyalty_records:
                is_valid = record['points_valid_till'] is None or record['points_valid_till'] >= today

                if is_valid:
                    total_valid_points += record['loyalty_points']

                formatted_records.append({
                    "loyalty_id": record['loyalty_id'],
                    "shop_id": record['shop_id'],
                    "shop_name": record['shop_name'],
                    "purchase_amount": float(record['purchase_amount']),
                    "loyalty_points": record['loyalty_points'],
                    "purchase_date": record['purchase_date'].strftime('%Y-%m-%d'),
                    "points_valid_till": record['points_valid_till'].strftime('%Y-%m-%d') if record['points_valid_till'] else "No expiry",
                    "is_valid": is_valid
                })

            return jsonify({
                "status": "success",
                "customer_name": customer['name'],
                "total_valid_points": total_valid_points,
                "count": len(loyalty_records),
                "data": formatted_records
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # READ Loyalty Points for a Shop
    @app.route('/loyalty/shop/<shop_id>', methods=['GET'])
    @validate_session
    def get_shop_loyalty(shop_id):
        try:
            cur = mysql.connection.cursor()

            # Verify shop exists
            cur.execute("SELECT name FROM shop WHERE shop_id = %s", (shop_id,))
            shop = cur.fetchone()
            if not shop:
                return jsonify({"error": "Shop not found"}), 404

            # Get loyalty points
            cur.execute("""
                SELECT l.*, c.name as customer_name
                FROM loyalty l
                JOIN cs432cims.G17_customer c ON l.customer_id = c.customer_id
                WHERE l.shop_id = %s
                ORDER BY l.purchase_date DESC
            """, (shop_id,))

            loyalty_records = cur.fetchall()

            # Format response
            formatted_records = []
            for record in loyalty_records:
                is_valid = record['points_valid_till'] is None or record['points_valid_till'] >= date.today()

                formatted_records.append({
                    "loyalty_id": record['loyalty_id'],
                    "customer_id": record['customer_id'],
                    "customer_name": record['customer_name'],
                    "purchase_amount": float(record['purchase_amount']),
                    "loyalty_points": record['loyalty_points'],
                    "purchase_date": record['purchase_date'].strftime('%Y-%m-%d'),
                    "points_valid_till": record['points_valid_till'].strftime('%Y-%m-%d') if record['points_valid_till'] else "No expiry",
                    "is_valid": is_valid
                })

            return jsonify({
                "status": "success",
                "shop_name": shop['name'],
                "count": len(loyalty_records),
                "data": formatted_records
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # UPDATE Loyalty Points (adjust points or extend validity)
    @app.route('/loyalty/<int:loyalty_id>', methods=['PUT'])
    @validate_session
    @admin_required  # Only admins can update loyalty points
    def update_loyalty(loyalty_id):
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No update data provided"}), 400

            cur = mysql.connection.cursor()

            # Verify loyalty record exists
            cur.execute("SELECT 1 FROM loyalty WHERE loyalty_id = %s", (loyalty_id,))
            if not cur.fetchone():
                return jsonify({"error": "Loyalty record not found"}), 404

            # Update loyalty record
            update_fields = []
            update_values = []

            if 'loyalty_points' in data:
                update_fields.append("loyalty_points = %s")
                update_values.append(data['loyalty_points'])

            if 'points_valid_till' in data:
                update_fields.append("points_valid_till = %s")
                update_values.append(data['points_valid_till'])

            if not update_fields:
                return jsonify({"error": "No valid fields to update"}), 400

            # Add loyalty_id to values
            update_values.append(loyalty_id)

            # Execute update
            cur.execute(f"""
                UPDATE loyalty
                SET {', '.join(update_fields)}
                WHERE loyalty_id = %s
            """, update_values)

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="UPDATE",
                table="loyalty",
                data={
                    "loyalty_id": loyalty_id,
                    "updated_fields": list(data.keys())
                },
                user_id=g.user_data['MemberID']
            )

            return jsonify({
                "status": "success",
                "message": "Loyalty record updated successfully"
            })

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400

    # DELETE Loyalty Points
    @app.route('/loyalty/<int:loyalty_id>', methods=['DELETE'])
    @validate_session
    @admin_required  # Only admins can delete loyalty points
    def delete_loyalty(loyalty_id):
        try:
            cur = mysql.connection.cursor()

            # Verify loyalty record exists
            cur.execute("SELECT 1 FROM loyalty WHERE loyalty_id = %s", (loyalty_id,))
            if not cur.fetchone():
                return jsonify({"error": "Loyalty record not found"}), 404

            # Delete loyalty record
            cur.execute("DELETE FROM loyalty WHERE loyalty_id = %s", (loyalty_id,))

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="DELETE",
                table="loyalty",
                data={"loyalty_id": loyalty_id},
                user_id=g.user_data['MemberID']
            )

            return jsonify({
                "status": "success",
                "message": "Loyalty record deleted successfully"
            })

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400

    # Redeem Loyalty Points
    @app.route('/loyalty/redeem', methods=['POST'])
    @validate_session
    def redeem_loyalty_points():
        try:
            data = request.json
            if not all(k in data for k in ['customer_id', 'shop_id', 'points_to_redeem']):
                return jsonify({"error": "Missing required fields"}), 400

            customer_id = data['customer_id']
            shop_id = data['shop_id']
            points_to_redeem = int(data['points_to_redeem'])

            if points_to_redeem <= 0:
                return jsonify({"error": "Points to redeem must be greater than zero"}), 400

            cur = mysql.connection.cursor()

            # Verify customer exists
            cur.execute("SELECT name FROM cs432cims.G17_customer WHERE customer_id = %s", (customer_id,))
            customer = cur.fetchone()
            if not customer:
                return jsonify({"error": "Customer not found"}), 404

            # Verify shop exists
            cur.execute("SELECT name FROM shop WHERE shop_id = %s", (shop_id,))
            shop = cur.fetchone()
            if not shop:
                return jsonify({"error": "Shop not found"}), 404

            # Get valid loyalty points for this customer at this shop
            today = date.today()
            cur.execute("""
                SELECT loyalty_id, loyalty_points
                FROM loyalty
                WHERE customer_id = %s AND shop_id = %s
                AND (points_valid_till IS NULL OR points_valid_till >= %s)
                ORDER BY purchase_date ASC
            """, (customer_id, shop_id, today))

            valid_points = cur.fetchall()

            # Calculate total available points
            total_available_points = sum(record['loyalty_points'] for record in valid_points)

            if total_available_points < points_to_redeem:
                return jsonify({
                    "error": f"Insufficient loyalty points. Available: {total_available_points}, Requested: {points_to_redeem}"
                }), 400

            # Redeem points starting from oldest
            points_remaining = points_to_redeem
            redeemed_records = []

            for record in valid_points:
                if points_remaining <= 0:
                    break

                loyalty_id = record['loyalty_id']
                available_points = record['loyalty_points']

                if available_points <= points_remaining:
                    # Use all points from this record
                    cur.execute("DELETE FROM loyalty WHERE loyalty_id = %s", (loyalty_id,))
                    points_remaining -= available_points
                    redeemed_records.append({
                        "loyalty_id": loyalty_id,
                        "points_redeemed": available_points,
                        "action": "deleted"
                    })
                else:
                    # Use partial points from this record
                    new_points = available_points - points_remaining
                    cur.execute("""
                        UPDATE loyalty
                        SET loyalty_points = %s
                        WHERE loyalty_id = %s
                    """, (new_points, loyalty_id))

                    redeemed_records.append({
                        "loyalty_id": loyalty_id,
                        "points_redeemed": points_remaining,
                        "points_remaining": new_points,
                        "action": "updated"
                    })

                    points_remaining = 0

            # Create a record of the redemption (negative points)
            redemption_value = points_to_redeem * 0.5  # Each point is worth $0.50

            cur.execute("""
                INSERT INTO loyalty (customer_id, shop_id, purchase_amount, loyalty_points, purchase_date, points_valid_till)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                customer_id,
                shop_id,
                -redemption_value,  # Negative amount for redemption
                -points_to_redeem,  # Negative points for redemption
                today,
                None  # No expiry for redemption record
            ))

            redemption_id = cur.lastrowid

            mysql.connection.commit()

            # Log the database change
            log_db_change(
                action="REDEEM",
                table="loyalty",
                data={
                    "customer_id": customer_id,
                    "shop_id": shop_id,
                    "points_redeemed": points_to_redeem,
                    "redemption_value": redemption_value,
                    "redemption_id": redemption_id
                },
                user_id=g.user_data['MemberID']
            )

            return jsonify({
                "status": "success",
                "message": f"Successfully redeemed {points_to_redeem} loyalty points",
                "customer_name": customer['name'],
                "shop_name": shop['name'],
                "points_redeemed": points_to_redeem,
                "redemption_value": redemption_value,
                "remaining_points": total_available_points - points_to_redeem,
                "redemption_details": redeemed_records
            })

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400

    # Return the app for chaining
    return app
