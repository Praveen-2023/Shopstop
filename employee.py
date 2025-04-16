from flask import Flask, request, jsonify, g
from flask_mysqldb import MySQL
from datetime import datetime

def add_employee_routes(app, mysql, validate_session, admin_required, log_db_change):
    # Constants
    CIMS_DB = 'cs432cims'
    
    # CREATE Employee
    @app.route('/employees', methods=['POST'])
    @validate_session
    @admin_required  # Only admins can create employees
    def create_employee():
        try:
            data = request.json
            if not all(k in data for k in ['name', 'role', 'contact', 'shop_id', 'salary']):
                return jsonify({"error": "Missing required fields"}), 400
            
            cur = mysql.connection.cursor()
            
            # Check if contact already exists
            cur.execute("SELECT 1 FROM employee WHERE contact = %s", (data['contact'],))
            if cur.fetchone():
                return jsonify({"error": "Contact number already exists"}), 409
            
            # Verify shop exists
            if data['shop_id']:
                cur.execute("SELECT 1 FROM shop WHERE shop_id = %s", (data['shop_id'],))
                if not cur.fetchone():
                    return jsonify({"error": "Shop not found"}), 404
            
            # Create employee
            cur.execute("""
                INSERT INTO employee (name, role, contact, shop_id, salary, salary_status)
                VALUES (%s, %s, %s, %s, %s, 'Pending')
            """, (data['name'], data['role'], data['contact'], data['shop_id'], data['salary']))
            
            # Get the auto-generated employee ID
            employee_id = cur.lastrowid
            
            mysql.connection.commit()
            
            # Log the database change
            log_db_change(
                action="CREATE",
                table="employee",
                data={
                    "employee_id": employee_id,
                    "name": data['name'],
                    "role": data['role'],
                    "shop_id": data['shop_id']
                },
                user_id=g.user_data['MemberID']
            )
            
            return jsonify({
                "status": "success", 
                "message": "Employee created successfully",
                "employee_id": employee_id
            }), 201
            
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400
    
    # READ Employee
    @app.route('/employees/<int:employee_id>', methods=['GET'])
    @validate_session
    def get_employee(employee_id):
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT e.*, s.name as shop_name
                FROM employee e
                LEFT JOIN shop s ON e.shop_id = s.shop_id
                WHERE e.employee_id = %s
            """, (employee_id,))
            
            employee = cur.fetchone()
            if not employee:
                return jsonify({"error": "Employee not found"}), 404
            
            return jsonify({
                "status": "success",
                "data": employee
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    
    # READ All Employees
    @app.route('/employees', methods=['GET'])
    @validate_session
    def get_all_employees():
        try:
            cur = mysql.connection.cursor()
            
            # Get query parameters
            shop_id = request.args.get('shop_id')
            role = request.args.get('role')
            
            # Base query
            query = """
                SELECT e.*, s.name as shop_name
                FROM employee e
                LEFT JOIN shop s ON e.shop_id = s.shop_id
            """
            
            params = []
            where_clauses = []
            
            # Add filters if provided
            if shop_id:
                where_clauses.append("e.shop_id = %s")
                params.append(shop_id)
            
            if role:
                where_clauses.append("e.role = %s")
                params.append(role)
            
            # Add WHERE clause if filters exist
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Execute query
            cur.execute(query, params)
            
            employees = cur.fetchall()
            
            return jsonify({
                "status": "success",
                "count": len(employees),
                "data": employees
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    
    # UPDATE Employee
    @app.route('/employees/<int:employee_id>', methods=['PUT'])
    @validate_session
    @admin_required  # Only admins can update employees
    def update_employee(employee_id):
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No update data provided"}), 400
            
            cur = mysql.connection.cursor()
            
            # Verify employee exists
            cur.execute("SELECT 1 FROM employee WHERE employee_id = %s", (employee_id,))
            if not cur.fetchone():
                return jsonify({"error": "Employee not found"}), 404
            
            # Update employee
            update_fields = []
            update_values = []
            
            if 'name' in data:
                update_fields.append("name = %s")
                update_values.append(data['name'])
            
            if 'role' in data:
                update_fields.append("role = %s")
                update_values.append(data['role'])
            
            if 'contact' in data:
                # Check if contact already exists for another employee
                cur.execute("SELECT 1 FROM employee WHERE contact = %s AND employee_id != %s", 
                           (data['contact'], employee_id))
                if cur.fetchone():
                    return jsonify({"error": "Contact number already exists for another employee"}), 409
                
                update_fields.append("contact = %s")
                update_values.append(data['contact'])
            
            if 'shop_id' in data:
                # Verify shop exists if provided
                if data['shop_id']:
                    cur.execute("SELECT 1 FROM shop WHERE shop_id = %s", (data['shop_id'],))
                    if not cur.fetchone():
                        return jsonify({"error": "Shop not found"}), 404
                
                update_fields.append("shop_id = %s")
                update_values.append(data['shop_id'])
            
            if 'salary' in data:
                update_fields.append("salary = %s")
                update_values.append(data['salary'])
            
            if 'salary_status' in data:
                if data['salary_status'] not in ['Paid', 'Pending']:
                    return jsonify({"error": "Invalid salary status. Must be 'Paid' or 'Pending'"}), 400
                
                update_fields.append("salary_status = %s")
                update_values.append(data['salary_status'])
            
            if not update_fields:
                return jsonify({"error": "No valid fields to update"}), 400
            
            # Add employee_id to values
            update_values.append(employee_id)
            
            # Execute update
            cur.execute(f"""
                UPDATE employee
                SET {', '.join(update_fields)}
                WHERE employee_id = %s
            """, update_values)
            
            mysql.connection.commit()
            
            # Log the database change
            log_db_change(
                action="UPDATE",
                table="employee",
                data={
                    "employee_id": employee_id,
                    "updated_fields": list(data.keys())
                },
                user_id=g.user_data['MemberID']
            )
            
            return jsonify({
                "status": "success",
                "message": "Employee updated successfully"
            })
            
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400
    
    # DELETE Employee
    @app.route('/employees/<int:employee_id>', methods=['DELETE'])
    @validate_session
    @admin_required  # Only admins can delete employees
    def delete_employee(employee_id):
        try:
            cur = mysql.connection.cursor()
            
            # Verify employee exists
            cur.execute("SELECT 1 FROM employee WHERE employee_id = %s", (employee_id,))
            if not cur.fetchone():
                return jsonify({"error": "Employee not found"}), 404
            
            # Check if employee has attendance records
            cur.execute("SELECT 1 FROM attendance WHERE employee_id = %s LIMIT 1", (employee_id,))
            if cur.fetchone():
                return jsonify({
                    "error": "Cannot delete employee as they have attendance records. Consider updating their status instead."
                }), 400
            
            # Delete employee
            cur.execute("DELETE FROM employee WHERE employee_id = %s", (employee_id,))
            
            mysql.connection.commit()
            
            # Log the database change
            log_db_change(
                action="DELETE",
                table="employee",
                data={"employee_id": employee_id},
                user_id=g.user_data['MemberID']
            )
            
            return jsonify({
                "status": "success",
                "message": "Employee deleted successfully"
            })
            
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400
    
    # Return the app for chaining
    return app
