from flask import Flask, request, jsonify, g
from flask_mysqldb import MySQL
from datetime import datetime, date

def add_attendance_routes(app, mysql, validate_session, admin_required, log_db_change):
    # Constants
    CIMS_DB = 'cs432cims'
    
    # CREATE Attendance
    @app.route('/attendance', methods=['POST'])
    @validate_session
    @admin_required  # Only admins can create attendance records
    def create_attendance():
        try:
            data = request.json
            if not all(k in data for k in ['employee_id', 'attendance_date', 'check_in', 'status']):
                return jsonify({"error": "Missing required fields"}), 400
            
            cur = mysql.connection.cursor()
            
            # Verify employee exists
            cur.execute("SELECT 1 FROM employee WHERE employee_id = %s", (data['employee_id'],))
            if not cur.fetchone():
                return jsonify({"error": "Employee not found"}), 404
            
            # Check if attendance record already exists for this employee on this date
            cur.execute("""
                SELECT 1 FROM attendance 
                WHERE employee_id = %s AND attendance_date = %s
            """, (data['employee_id'], data['attendance_date']))
            
            if cur.fetchone():
                return jsonify({"error": "Attendance record already exists for this employee on this date"}), 409
            
            # Validate status
            if data['status'] not in ['Present', 'Absent', 'On Leave']:
                return jsonify({"error": "Invalid status. Must be 'Present', 'Absent', or 'On Leave'"}), 400
            
            # Create attendance record
            check_out = data.get('check_out')  # Optional field
            
            cur.execute("""
                INSERT INTO attendance (employee_id, attendance_date, check_in, check_out, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (data['employee_id'], data['attendance_date'], data['check_in'], check_out, data['status']))
            
            mysql.connection.commit()
            
            # Log the database change
            log_db_change(
                action="CREATE",
                table="attendance",
                data={
                    "employee_id": data['employee_id'],
                    "attendance_date": data['attendance_date'],
                    "status": data['status']
                },
                user_id=g.user_data['MemberID']
            )
            
            return jsonify({
                "status": "success", 
                "message": "Attendance record created successfully"
            }), 201
            
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400
    
    # READ Attendance for an Employee
    @app.route('/attendance/employee/<int:employee_id>', methods=['GET'])
    @validate_session
    def get_employee_attendance(employee_id):
        try:
            cur = mysql.connection.cursor()
            
            # Verify employee exists
            cur.execute("SELECT name FROM employee WHERE employee_id = %s", (employee_id,))
            employee = cur.fetchone()
            if not employee:
                return jsonify({"error": "Employee not found"}), 404
            
            # Get query parameters for date range
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            query = """
                SELECT a.*, e.name as employee_name
                FROM attendance a
                JOIN employee e ON a.employee_id = e.employee_id
                WHERE a.employee_id = %s
            """
            
            params = [employee_id]
            
            # Add date range filter if provided
            if start_date and end_date:
                query += " AND a.attendance_date BETWEEN %s AND %s"
                params.extend([start_date, end_date])
            
            # Order by date
            query += " ORDER BY a.attendance_date DESC"
            
            cur.execute(query, params)
            
            attendance_records = cur.fetchall()
            
            # Format response
            formatted_records = []
            for record in attendance_records:
                formatted_records.append({
                    "employee_id": record['employee_id'],
                    "employee_name": record['employee_name'],
                    "attendance_date": record['attendance_date'].strftime('%Y-%m-%d'),
                    "check_in": record['check_in'].strftime('%H:%M:%S') if record['check_in'] else None,
                    "check_out": record['check_out'].strftime('%H:%M:%S') if record['check_out'] else None,
                    "status": record['status']
                })
            
            return jsonify({
                "status": "success",
                "employee_name": employee['name'],
                "count": len(attendance_records),
                "data": formatted_records
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    
    # READ Attendance for a Date
    @app.route('/attendance/date/<date_str>', methods=['GET'])
    @validate_session
    def get_date_attendance(date_str):
        try:
            cur = mysql.connection.cursor()
            
            # Validate date format
            try:
                attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
            
            # Get query parameter for shop
            shop_id = request.args.get('shop_id')
            
            query = """
                SELECT a.*, e.name as employee_name, e.role, e.shop_id, s.name as shop_name
                FROM attendance a
                JOIN employee e ON a.employee_id = e.employee_id
                LEFT JOIN shop s ON e.shop_id = s.shop_id
                WHERE a.attendance_date = %s
            """
            
            params = [attendance_date]
            
            # Add shop filter if provided
            if shop_id:
                query += " AND e.shop_id = %s"
                params.append(shop_id)
            
            # Order by employee name
            query += " ORDER BY e.name"
            
            cur.execute(query, params)
            
            attendance_records = cur.fetchall()
            
            # Format response
            formatted_records = []
            for record in attendance_records:
                formatted_records.append({
                    "employee_id": record['employee_id'],
                    "employee_name": record['employee_name'],
                    "role": record['role'],
                    "shop_id": record['shop_id'],
                    "shop_name": record['shop_name'],
                    "check_in": record['check_in'].strftime('%H:%M:%S') if record['check_in'] else None,
                    "check_out": record['check_out'].strftime('%H:%M:%S') if record['check_out'] else None,
                    "status": record['status']
                })
            
            return jsonify({
                "status": "success",
                "date": date_str,
                "count": len(attendance_records),
                "data": formatted_records
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    
    # UPDATE Attendance
    @app.route('/attendance/<int:employee_id>/<date_str>', methods=['PUT'])
    @validate_session
    @admin_required  # Only admins can update attendance
    def update_attendance(employee_id, date_str):
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No update data provided"}), 400
            
            # Validate date format
            try:
                attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
            
            cur = mysql.connection.cursor()
            
            # Verify attendance record exists
            cur.execute("""
                SELECT 1 FROM attendance 
                WHERE employee_id = %s AND attendance_date = %s
            """, (employee_id, attendance_date))
            
            if not cur.fetchone():
                return jsonify({"error": "Attendance record not found"}), 404
            
            # Update attendance
            update_fields = []
            update_values = []
            
            if 'check_in' in data:
                update_fields.append("check_in = %s")
                update_values.append(data['check_in'])
            
            if 'check_out' in data:
                update_fields.append("check_out = %s")
                update_values.append(data['check_out'])
            
            if 'status' in data:
                if data['status'] not in ['Present', 'Absent', 'On Leave']:
                    return jsonify({"error": "Invalid status. Must be 'Present', 'Absent', or 'On Leave'"}), 400
                
                update_fields.append("status = %s")
                update_values.append(data['status'])
            
            if not update_fields:
                return jsonify({"error": "No valid fields to update"}), 400
            
            # Add primary key values to params
            update_values.extend([employee_id, attendance_date])
            
            # Execute update
            cur.execute(f"""
                UPDATE attendance
                SET {', '.join(update_fields)}
                WHERE employee_id = %s AND attendance_date = %s
            """, update_values)
            
            mysql.connection.commit()
            
            # Log the database change
            log_db_change(
                action="UPDATE",
                table="attendance",
                data={
                    "employee_id": employee_id,
                    "attendance_date": date_str,
                    "updated_fields": list(data.keys())
                },
                user_id=g.user_data['MemberID']
            )
            
            return jsonify({
                "status": "success",
                "message": "Attendance record updated successfully"
            })
            
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400
    
    # DELETE Attendance
    @app.route('/attendance/<int:employee_id>/<date_str>', methods=['DELETE'])
    @validate_session
    @admin_required  # Only admins can delete attendance
    def delete_attendance(employee_id, date_str):
        try:
            # Validate date format
            try:
                attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
            
            cur = mysql.connection.cursor()
            
            # Verify attendance record exists
            cur.execute("""
                SELECT 1 FROM attendance 
                WHERE employee_id = %s AND attendance_date = %s
            """, (employee_id, attendance_date))
            
            if not cur.fetchone():
                return jsonify({"error": "Attendance record not found"}), 404
            
            # Delete attendance record
            cur.execute("""
                DELETE FROM attendance 
                WHERE employee_id = %s AND attendance_date = %s
            """, (employee_id, attendance_date))
            
            mysql.connection.commit()
            
            # Log the database change
            log_db_change(
                action="DELETE",
                table="attendance",
                data={
                    "employee_id": employee_id,
                    "attendance_date": date_str
                },
                user_id=g.user_data['MemberID']
            )
            
            return jsonify({
                "status": "success",
                "message": "Attendance record deleted successfully"
            })
            
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 400
    
    # Return the app for chaining
    return app
