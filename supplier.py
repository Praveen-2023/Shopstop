from flask import Flask, request, jsonify, g
from flask_mysqldb import MySQL
from datetime import datetime

def add_supplier_routes(app, mysql, validate_session, admin_required, log_db_change):
    # Constants
    CIMS_DB = 'cs432cims'
    
    # CREATE Supplier
    @app.route('/suppliers', methods=['POST'])
    @validate_session
    @admin_required  # Only admins can create suppliers
    def create_supplier():
        try:
            data = request.json
            if not all(k in data for k in ['supplier_id', 'name', 'contact', 'email', 'address']):
                return jsonify({"error": "Missing required fields"}), 400
            
            cur = mysql.connection.cursor()
            
            # Check if supplier ID already exists
            cur.execute("SELECT 1 FROM supplier WHERE supplier_id = %s", (data['supplier_id'],))
            if cur.fetchone():
                return jsonify({"error": "Supplier ID already exists"}), 409
            
            # Check if contact already exists
            cur.execute("SELECT 1 FROM supplier WHERE contact = %s", (data['contact'],))
            if cur.fetchone():
                return jsonify({"error": "Contact number already exists"}), 409
            
            # Check if email already exists
            cur.execute("SELECT 1 FROM supplier WHERE email = %s", (data['email'],))
            if cur.fetchone():
                return jsonify({"error": "Email already exists"}), 409
            
            # Create supplier
            cur.execute("""
                INSERT INTO supplier (supplier_id, name, contact, email, address)
                VALUES (%s, %s, %s, %s, %s)
            """, (data['supplier_id'], data['name'], data['contact'], data['email'], data['address']))
            
            mysql.connection.commit()
            
            # Log the database change
            log_db_change(
                action="CREATE",
                table="supplier",
                data={
                    "supplier_id": data['supplier_id'],
                    "name": data['name']
                },
                user_id=g.user_data['MemberID']
            )
            
            return jsonify({
                "status": "success", 
                "message": "Supplier created successfully",
                "supplier_id": data['supplier_id']
            }), 201
            
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400
    
    # READ Supplier
    @app.route('/suppliers/<supplier_id>', methods=['GET'])
    @validate_session
    def get_supplier(supplier_id):
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT * FROM supplier
                WHERE supplier_id = %s
            """, (supplier_id,))
            
            supplier = cur.fetchone()
            if not supplier:
                return jsonify({"error": "Supplier not found"}), 404
            
            return jsonify({
                "status": "success",
                "data": {
                    "supplier_id": supplier['supplier_id'],
                    "name": supplier['name'],
                    "contact": supplier['contact'],
                    "email": supplier['email'],
                    "address": supplier['address']
                }
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    
    # READ All Suppliers
    @app.route('/suppliers', methods=['GET'])
    @validate_session
    def get_all_suppliers():
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM supplier")
            
            suppliers = cur.fetchall()
            
            return jsonify({
                "status": "success",
                "count": len(suppliers),
                "data": suppliers
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    
    # UPDATE Supplier
    @app.route('/suppliers/<supplier_id>', methods=['PUT'])
    @validate_session
    @admin_required  # Only admins can update suppliers
    def update_supplier(supplier_id):
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No update data provided"}), 400
            
            cur = mysql.connection.cursor()
            
            # Verify supplier exists
            cur.execute("SELECT 1 FROM supplier WHERE supplier_id = %s", (supplier_id,))
            if not cur.fetchone():
                return jsonify({"error": "Supplier not found"}), 404
            
            # Update supplier
            update_fields = []
            update_values = []
            
            if 'name' in data:
                update_fields.append("name = %s")
                update_values.append(data['name'])
            
            if 'contact' in data:
                # Check if contact already exists for another supplier
                cur.execute("SELECT 1 FROM supplier WHERE contact = %s AND supplier_id != %s", 
                           (data['contact'], supplier_id))
                if cur.fetchone():
                    return jsonify({"error": "Contact number already exists for another supplier"}), 409
                
                update_fields.append("contact = %s")
                update_values.append(data['contact'])
            
            if 'email' in data:
                # Check if email already exists for another supplier
                cur.execute("SELECT 1 FROM supplier WHERE email = %s AND supplier_id != %s", 
                           (data['email'], supplier_id))
                if cur.fetchone():
                    return jsonify({"error": "Email already exists for another supplier"}), 409
                
                update_fields.append("email = %s")
                update_values.append(data['email'])
            
            if 'address' in data:
                update_fields.append("address = %s")
                update_values.append(data['address'])
            
            if not update_fields:
                return jsonify({"error": "No valid fields to update"}), 400
            
            # Add supplier_id to values
            update_values.append(supplier_id)
            
            # Execute update
            cur.execute(f"""
                UPDATE supplier
                SET {', '.join(update_fields)}
                WHERE supplier_id = %s
            """, update_values)
            
            mysql.connection.commit()
            
            # Log the database change
            log_db_change(
                action="UPDATE",
                table="supplier",
                data={
                    "supplier_id": supplier_id,
                    "updated_fields": list(data.keys())
                },
                user_id=g.user_data['MemberID']
            )
            
            return jsonify({
                "status": "success",
                "message": "Supplier updated successfully"
            })
            
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400
    
    # DELETE Supplier
    @app.route('/suppliers/<supplier_id>', methods=['DELETE'])
    @validate_session
    @admin_required  # Only admins can delete suppliers
    def delete_supplier(supplier_id):
        try:
            cur = mysql.connection.cursor()
            
            # Verify supplier exists
            cur.execute("SELECT 1 FROM supplier WHERE supplier_id = %s", (supplier_id,))
            if not cur.fetchone():
                return jsonify({"error": "Supplier not found"}), 404
            
            # Check if supplier is referenced in products
            cur.execute("SELECT 1 FROM product WHERE supplier_id = %s LIMIT 1", (supplier_id,))
            if cur.fetchone():
                return jsonify({
                    "error": "Cannot delete supplier as it is referenced by products. Remove the products first."
                }), 400
            
            # Delete supplier
            cur.execute("DELETE FROM supplier WHERE supplier_id = %s", (supplier_id,))
            
            mysql.connection.commit()
            
            # Log the database change
            log_db_change(
                action="DELETE",
                table="supplier",
                data={"supplier_id": supplier_id},
                user_id=g.user_data['MemberID']
            )
            
            return jsonify({
                "status": "success",
                "message": "Supplier deleted successfully"
            })
            
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400
    
    # Return the app for chaining
    return app
