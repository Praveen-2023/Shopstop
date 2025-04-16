# CS432 Module 3 - Database Integration and Secure API Development

This project implements a secure API system that connects project-specific databases to a central database (CIMS - Central Information Management System) with role-based access control and comprehensive logging.

## Project Structure

- `main.py`: Main application file that initializes the Flask app and registers all routes
- `createUser.py`: Handles member creation and authentication
- `addUser.py`: Handles adding new users to the system
- `deleteUser.py`: Handles member deletion with integrity checks
- `shops.py`: Manages shop-related operations
- `products.py`: Manages product-related operations
- `Customer.py`: Manages customer-related operations
- `portfolio.py`: Implements member portfolio management

## Features

### 1. Database Integration
- Connects to the centralized CIMS database for shared tables
- Uses project-specific database for project-specific tables
- Avoids duplication of data by using shared tables

### 2. Secure API Development
- Session validation for all API calls
- Role-based access control (RBAC)
- Comprehensive logging of all database changes
- Detection of unauthorized modifications

### 3. Member Management
- Member creation with automatic login credentials
- Member deletion with integrity checks
- Member portfolio management

### 4. Role-Based Access Control
- Regular users have limited access
- Admin users have full access to perform administrative actions

## API Endpoints

### Authentication
- `POST /shopstop/authUser`: Authenticate a user and get a session token

### Member Management
- `POST /shopstop/members/create`: Create a new member (admin only)
- `POST /shopstop/members/add`: Add a new user (admin only)
- `POST /shopstop/members/delete`: Delete a member (admin only)

### Portfolio Management
- `GET /portfolio/members`: List all members in the group
- `GET /portfolio/member/<member_id>`: Get detailed portfolio for a specific member
- `PUT /portfolio/member/<member_id>`: Update portfolio information (self or admin only)

### Shop Management
- `POST /shops`: Create a new shop (admin only)
- `GET /shops`: List all shops
- `GET /shops/<shop_id>`: Get shop details
- `PUT /shops/<shop_id>`: Update shop information (admin only)
- `DELETE /shops/<shop_id>`: Delete a shop (admin only)

### Product Management
- `POST /products`: Create a new product (admin only)
- `GET /products/<product_id>`: Get product details
- `PUT /products/<product_id>`: Update product information (admin only)
- `DELETE /products/<product_id>`: Delete a product (admin only)
- `GET /shops/<shop_id>/products`: List all products in a shop

### Customer Management
- `POST /customers`: Create a new customer
- `GET /customers/<customer_id>`: Get customer details
- `PUT /customers/<customer_id>`: Update customer information
- `DELETE /customers/<customer_id>`: Delete a customer (admin only)

## Security Features

1. **Session Validation**: All API calls validate the session token before processing
2. **Role-Based Access Control**: Admin-level actions are restricted to admin users
3. **Logging**: All database changes are logged for audit purposes
4. **Unauthorized Access Detection**: Any attempt to bypass session validation is logged and flagged

## Running the Application

```bash
python main.py
```

The application will start on port 5000 by default.

## Testing

You can test the API endpoints using tools like Postman or curl. Make sure to:

1. First authenticate using the `/shopstop/authUser` endpoint to get a session token
2. Include the session token in the Authorization header for all subsequent requests
