-- Initialize database schema for the parameter reference system

-- Create the parameters_reference table
CREATE TABLE parameters_reference (
    parameter_name TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    data_type TEXT NOT NULL
);

-- Create the products table (as an example table to query)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER NOT NULL,
    rating DECIMAL(3, 1),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Insert parameter descriptions
INSERT INTO parameters_reference (parameter_name, description, data_type) VALUES
    ('id', 'Unique identifier for the product', 'INTEGER'),
    ('name', 'Name of the product', 'TEXT'),
    ('category', 'Product category (e.g., electronics, clothing, food)', 'TEXT'),
    ('price', 'Price of the product in USD', 'DECIMAL'),
    ('stock', 'Current stock quantity available', 'INTEGER'),
    ('rating', 'Customer rating from 0.0 to 5.0', 'DECIMAL'),
    ('description', 'Detailed product description', 'TEXT'),
    ('created_at', 'Date and time when the product was added', 'TIMESTAMP'),
    ('is_active', 'Whether the product is currently active (TRUE) or not (FALSE)', 'BOOLEAN');

-- Insert sample products
INSERT INTO products (name, category, price, stock, rating, description) VALUES
    ('Smartphone X', 'electronics', 999.99, 50, 4.5, 'Latest smartphone with advanced features'),
    ('Laptop Pro', 'electronics', 1499.99, 30, 4.8, 'Professional laptop for developers'),
    ('Cotton T-Shirt', 'clothing', 19.99, 200, 4.2, 'Comfortable cotton t-shirt'),
    ('Running Shoes', 'footwear', 89.99, 75, 4.6, 'Lightweight running shoes'),
    ('Coffee Maker', 'appliances', 129.99, 25, 4.3, 'Automatic coffee maker with timer'),
    ('Wireless Headphones', 'electronics', 199.99, 40, 4.7, 'Noise-cancelling wireless headphones'),
    ('Desk Chair', 'furniture', 149.99, 15, 4.0, 'Ergonomic desk chair with lumbar support'),
    ('Protein Powder', 'food', 29.99, 100, 4.4, 'Whey protein powder, chocolate flavor'),
    ('Yoga Mat', 'fitness', 24.99, 60, 4.1, 'Non-slip yoga mat'),
    ('Smart Watch', 'electronics', 249.99, 35, 4.6, 'Fitness tracking smart watch');

-- Create the customers table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    address TEXT,
    city TEXT,
    country TEXT,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Add customer parameters to reference table
INSERT INTO parameters_reference (parameter_name, description, data_type) VALUES
    ('first_name', 'Customer''s first name', 'TEXT'),
    ('last_name', 'Customer''s last name', 'TEXT'),
    ('email', 'Customer''s email address', 'TEXT'),
    ('phone', 'Customer''s phone number', 'TEXT'),
    ('address', 'Customer''s street address', 'TEXT'),
    ('city', 'Customer''s city', 'TEXT'),
    ('country', 'Customer''s country', 'TEXT'),
    ('registration_date', 'Date when customer registered', 'TIMESTAMP'),
    ('is_active', 'Whether the customer account is active (TRUE) or not (FALSE)', 'BOOLEAN');

-- Insert sample customers
INSERT INTO customers (first_name, last_name, email, phone, address, city, country) VALUES
    ('John', 'Doe', 'john.doe@example.com', '+1-555-123-4567', '123 Main St', 'New York', 'USA'),
    ('Jane', 'Smith', 'jane.smith@example.com', '+1-555-987-6543', '456 Oak Ave', 'Los Angeles', 'USA'),
    ('Michael', 'Johnson', 'michael.j@example.com', '+1-555-567-8901', '789 Pine Rd', 'Chicago', 'USA'),
    ('Emily', 'Brown', 'emily.b@example.com', '+1-555-234-5678', '101 Maple Dr', 'Houston', 'USA'),
    ('David', 'Wilson', 'david.w@example.com', '+1-555-345-6789', '202 Cedar Ln', 'Phoenix', 'USA');

-- Create the orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Add order parameters to reference table
INSERT INTO parameters_reference (parameter_name, description, data_type) VALUES
    ('customer_id', 'ID of the customer who placed the order', 'INTEGER'),
    ('order_date', 'Date and time when the order was placed', 'TIMESTAMP'),
    ('total_amount', 'Total amount of the order in USD', 'DECIMAL'),
    ('status', 'Order status (e.g., pending, shipped, delivered, cancelled)', 'TEXT');

-- Insert sample orders
INSERT INTO orders (customer_id, order_date, total_amount, status) VALUES
    (1, '2023-01-15 10:30:00', 1299.98, 'delivered'),
    (2, '2023-02-20 14:45:00', 199.99, 'delivered'),
    (3, '2023-03-10 09:15:00', 174.98, 'shipped'),
    (4, '2023-04-05 16:20:00', 249.99, 'pending'),
    (5, '2023-05-12 11:00:00', 129.99, 'processing'),
    (1, '2023-06-18 13:30:00', 89.99, 'delivered'),
    (2, '2023-07-22 15:45:00', 449.97, 'shipped'),
    (3, '2023-08-30 10:10:00', 24.99, 'delivered');
