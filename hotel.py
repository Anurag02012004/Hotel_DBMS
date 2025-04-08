import streamlit as st
import mysql.connector
import pandas as pd
import hashlib
from datetime import datetime, timedelta
import random
import time
import decimal
# Database connection function
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="anu@iiit",
    )

# Initialize database
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create database if it doesn't exist
    cursor.execute("CREATE DATABASE IF NOT EXISTS hotel_management")
    cursor.execute("USE hotel_management")
    
    # Create tables

    # Users table for authentication
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role ENUM('admin', 'staff', 'manager') NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Staff table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staff (
        staff_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        position VARCHAR(50) NOT NULL,
        contact VARCHAR(20) NOT NULL,
        email VARCHAR(100) NOT NULL,
        address TEXT,
        salary DECIMAL(10,2) NOT NULL,
        join_date DATE NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
    )
    """)
    
    # Room Types table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS room_types (
        room_type_id INT AUTO_INCREMENT PRIMARY KEY,
        type_name VARCHAR(50) NOT NULL,
        description TEXT,
        price_per_night DECIMAL(10,2) NOT NULL,
        capacity INT NOT NULL,
        amenities TEXT
    )
    """)
    
    # Rooms table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        room_id INT AUTO_INCREMENT PRIMARY KEY,
        room_number VARCHAR(10) NOT NULL UNIQUE,
        room_type_id INT NOT NULL,
        floor INT NOT NULL,
        status ENUM('available', 'occupied', 'maintenance', 'reserved') DEFAULT 'available',
        FOREIGN KEY (room_type_id) REFERENCES room_types(room_type_id)
    )
    """)
    
    # Customers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INT AUTO_INCREMENT PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        email VARCHAR(100),
        phone VARCHAR(20) NOT NULL,
        address TEXT,
        id_proof_type VARCHAR(50) NOT NULL,
        id_proof_number VARCHAR(50) NOT NULL,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Reservations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        reservation_id INT AUTO_INCREMENT PRIMARY KEY,
        customer_id INT NOT NULL,
        room_id INT NOT NULL,
        check_in_date DATE NOT NULL,
        check_out_date DATE NOT NULL,
        adults INT NOT NULL,
        children INT DEFAULT 0,
        status ENUM('confirmed', 'checked_in', 'checked_out', 'cancelled') DEFAULT 'confirmed',
        booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_amount DECIMAL(10,2) NOT NULL,
        staff_id INT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY (room_id) REFERENCES rooms(room_id),
        FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
    )
    """)
    
    # Services table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
        service_id INT AUTO_INCREMENT PRIMARY KEY,
        service_name VARCHAR(100) NOT NULL,
        description TEXT,
        price DECIMAL(10,2) NOT NULL,
        availability BOOLEAN DEFAULT TRUE
    )
    """)
    
    # Service orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_orders (
        order_id INT AUTO_INCREMENT PRIMARY KEY,
        reservation_id INT NOT NULL,
        service_id INT NOT NULL,
        quantity INT NOT NULL,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status ENUM('pending', 'completed', 'cancelled') DEFAULT 'pending',
        staff_id INT,
        notes TEXT,
        FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id),
        FOREIGN KEY (service_id) REFERENCES services(service_id),
        FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
    )
    """)
    
    # Billing table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS billing (
        bill_id INT AUTO_INCREMENT PRIMARY KEY,
        reservation_id INT NOT NULL,
        room_charges DECIMAL(10,2) NOT NULL,
        service_charges DECIMAL(10,2) DEFAULT 0.00,
        tax_amount DECIMAL(10,2) NOT NULL,
        total_amount DECIMAL(10,2) NOT NULL,
        payment_status ENUM('pending', 'partial', 'paid') DEFAULT 'pending',
        payment_method VARCHAR(50),
        billing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id)
    )
    """)
    
    # Payments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        payment_id INT AUTO_INCREMENT PRIMARY KEY,
        bill_id INT NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        payment_method VARCHAR(50) NOT NULL,
        transaction_id VARCHAR(100),
        staff_id INT,
        FOREIGN KEY (bill_id) REFERENCES billing(bill_id),
        FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
    )
    """)
    
    # Insert default admin user if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        admin_password = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                      ("admin", admin_password, "admin"))
    
    # Insert sample room types if not exists
    cursor.execute("SELECT * FROM room_types LIMIT 1")
    if not cursor.fetchone():
        room_types = [
            ("Standard", "Basic room with essential amenities", 1000.00, 2, "Wi-Fi, TV, AC"),
            ("Deluxe", "Comfortable room with extra space", 1500.00, 2, "Wi-Fi, TV, AC, Mini Fridge"),
            ("Suite", "Luxury room with separate living area", 2500.00, 4, "Wi-Fi, TV, AC, Mini Bar, Jacuzzi"),
            ("Executive", "Premium room for business travelers", 2000.00, 2, "Wi-Fi, TV, AC, Work Desk, Coffee Maker")
        ]
        cursor.executemany("INSERT INTO room_types (type_name, description, price_per_night, capacity, amenities) VALUES (%s, %s, %s, %s, %s)", room_types)
    
    # Insert sample services if not exists
    cursor.execute("SELECT * FROM services LIMIT 1")
    if not cursor.fetchone():
        services = [
            ("Room Service", "Food delivered to room", 200.00, True),
            ("Laundry", "Clothes washing and ironing", 300.00, True),
            ("Spa", "Relaxing massage and treatments", 800.00, True),
            ("Airport Pickup", "Transportation from airport", 500.00, True),
            ("Breakfast", "Morning breakfast buffet", 250.00, True)
        ]
        cursor.executemany("INSERT INTO services (service_name, description, price, availability) VALUES (%s, %s, %s, %s)", services)
    
    conn.commit()
    cursor.close()
    conn.close()

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Validation functions
def validate_login(username, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE hotel_management")
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user and user['password'] == hash_password(password):
        return user
    return None

# Create room function
def create_room(room_number, room_type_id, floor):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE hotel_management")
    
    try:
        cursor.execute("INSERT INTO rooms (room_number, room_type_id, floor) VALUES (%s, %s, %s)",
                      (room_number, room_type_id, floor))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as err:
        conn.rollback()
        cursor.close()
        conn.close()
        return False

# Get all room types
def get_room_types():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE hotel_management")
    cursor.execute("SELECT * FROM room_types")
    room_types = cursor.fetchall()
    cursor.close()
    conn.close()
    return room_types

# Get all rooms
def get_rooms():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE hotel_management")
    cursor.execute("""
    SELECT r.room_id, r.room_number, r.floor, r.status, rt.type_name, rt.price_per_night
    FROM rooms r
    JOIN room_types rt ON r.room_type_id = rt.room_type_id
    ORDER BY r.room_number
    """)
    rooms = cursor.fetchall()
    cursor.close()
    conn.close()
    return rooms

# Get available rooms
def get_available_rooms(check_in, check_out):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE hotel_management")
    
    query = """
    SELECT r.room_id, r.room_number, r.floor, rt.type_name, rt.price_per_night, rt.capacity, rt.amenities
    FROM rooms r
    JOIN room_types rt ON r.room_type_id = rt.room_type_id
    WHERE r.status = 'available'
    AND r.room_id NOT IN (
        SELECT DISTINCT res.room_id
        FROM reservations res
        WHERE (res.check_in_date BETWEEN %s AND %s
            OR res.check_out_date BETWEEN %s AND %s
            OR %s BETWEEN res.check_in_date AND res.check_out_date)
        AND res.status NOT IN ('checked_out', 'cancelled')
    )
    ORDER BY r.room_number
    """
    
    cursor.execute(query, (check_in, check_out, check_in, check_out, check_in))
    rooms = cursor.fetchall()
    cursor.close()
    conn.close()
    return rooms

# Create customer
def create_customer(first_name, last_name, email, phone, address, id_proof_type, id_proof_number):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE hotel_management")
    
    try:
        cursor.execute("""
        INSERT INTO customers (first_name, last_name, email, phone, address, id_proof_type, id_proof_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (first_name, last_name, email, phone, address, id_proof_type, id_proof_number))
        conn.commit()
        customer_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return customer_id
    except mysql.connector.Error as err:
        conn.rollback()
        cursor.close()
        conn.close()
        return None

# Get customer by ID or details
def get_customer(customer_id=None, phone=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE hotel_management")
    
    if customer_id:
        cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
    elif phone:
        cursor.execute("SELECT * FROM customers WHERE phone = %s", (phone,))
    else:
        cursor.close()
        conn.close()
        return None
        
    customer = cursor.fetchone()
    cursor.close()
    conn.close()
    return customer

# Get all customers
def get_all_customers():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE hotel_management")
    cursor.execute("SELECT * FROM customers ORDER BY registration_date DESC")
    customers = cursor.fetchall()
    cursor.close()
    conn.close()
    return customers

# Create reservation
def create_reservation(customer_id, room_id, check_in_date, check_out_date, adults, children, staff_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE hotel_management")
    
    try:
        # Calculate total days
        date_format = "%Y-%m-%d"
        d1 = datetime.strptime(check_in_date, date_format)
        d2 = datetime.strptime(check_out_date, date_format)
        days = (d2 - d1).days
        
        # Get room price
        cursor.execute("""
        SELECT rt.price_per_night
        FROM rooms r
        JOIN room_types rt ON r.room_type_id = rt.room_type_id
        WHERE r.room_id = %s
        """, (room_id,))
        
        price_per_night = cursor.fetchone()[0]
        total_amount = float(price_per_night) * days
        
        # Create reservation
        cursor.execute("""
        INSERT INTO reservations 
        (customer_id, room_id, check_in_date, check_out_date, adults, children, staff_id, total_amount)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (customer_id, room_id, check_in_date, check_out_date, adults, children, staff_id, total_amount))
        
        reservation_id = cursor.lastrowid
        
        # Update room status to reserved
        cursor.execute("UPDATE rooms SET status = 'reserved' WHERE room_id = %s", (room_id,))
        
        # Create initial billing record
        tax_amount = total_amount * 0.18  # 18% tax
        final_amount = total_amount + tax_amount
        
        cursor.execute("""
        INSERT INTO billing 
        (reservation_id, room_charges, tax_amount, total_amount)
        VALUES (%s, %s, %s, %s)
        """, (reservation_id, total_amount, tax_amount, final_amount))
        
        conn.commit()
        cursor.close()
        conn.close()
        return reservation_id
    except mysql.connector.Error as err:
        conn.rollback()
        cursor.close()
        conn.close()
        return None

# Get active reservations
def get_active_reservations():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE hotel_management")
    
    query = """
    SELECT r.reservation_id, r.check_in_date, r.check_out_date, r.status, r.total_amount,
           c.first_name, c.last_name, c.phone,
           rm.room_number, rt.type_name
    FROM reservations r
    JOIN customers c ON r.customer_id = c.customer_id
    JOIN rooms rm ON r.room_id = rm.room_id
    JOIN room_types rt ON rm.room_type_id = rt.room_type_id
    WHERE r.status IN ('confirmed', 'checked_in')
    ORDER BY r.check_in_date
    """
    
    cursor.execute(query)
    reservations = cursor.fetchall()
    cursor.close()
    conn.close()
    return reservations

# Get reservation by ID
def get_reservation(reservation_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE hotel_management")
    
    query = """
    SELECT r.*, c.first_name, c.last_name, c.phone, c.email,
           rm.room_number, rt.type_name, rt.price_per_night
    FROM reservations r
    JOIN customers c ON r.customer_id = c.customer_id
    JOIN rooms rm ON r.room_id = rm.room_id
    JOIN room_types rt ON rm.room_type_id = rt.room_type_id
    WHERE r.reservation_id = %s
    """
    
    cursor.execute(query, (reservation_id,))
    reservation = cursor.fetchone()
    cursor.close()
    conn.close()
    return reservation

# Update reservation status
def update_reservation_status(reservation_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE hotel_management")
    
    try:
        cursor.execute("UPDATE reservations SET status = %s WHERE reservation_id = %s", 
                      (status, reservation_id))
        
        # Get room_id for this reservation
        cursor.execute("SELECT room_id FROM reservations WHERE reservation_id = %s", (reservation_id,))
        room_id = cursor.fetchone()[0]
        
        # Update room status
        room_status = 'occupied' if status == 'checked_in' else 'available' if status == 'checked_out' else 'reserved'
        cursor.execute("UPDATE rooms SET status = %s WHERE room_id = %s", 
                      (room_status, room_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as err:
        conn.rollback()
        cursor.close()
        conn.close()
        return False

# Get services
def get_services():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE hotel_management")
    cursor.execute("SELECT * FROM services WHERE availability = TRUE")
    services = cursor.fetchall()
    cursor.close()
    conn.close()
    return services

# Order service
def order_service(reservation_id, service_id, quantity, staff_id, notes):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE hotel_management")
    
    try:
        cursor.execute("""
        INSERT INTO service_orders (reservation_id, service_id, quantity, staff_id, notes)
        VALUES (%s, %s, %s, %s, %s)
        """, (reservation_id, service_id, quantity, staff_id, notes))
        
        # Get service price
        cursor.execute("SELECT price FROM services WHERE service_id = %s", (service_id,))
        service_price = cursor.fetchone()[0]
        
        service_total = float(service_price) * quantity
        
        # Update billing
        cursor.execute("""
        UPDATE billing 
        SET service_charges = service_charges + %s,
            total_amount = total_amount + %s
        WHERE reservation_id = %s
        """, (service_total, service_total, reservation_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as err:
        conn.rollback()
        cursor.close()
        conn.close()
        return False

# Get service orders for a reservation
def get_service_orders(reservation_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE hotel_management")
    
    query = """
    SELECT so.order_id, so.quantity, so.order_date, so.status, so.notes,
           s.service_name, s.price, (s.price * so.quantity) as total_price
    FROM service_orders so
    JOIN services s ON so.service_id = s.service_id
    WHERE so.reservation_id = %s
    ORDER BY so.order_date DESC
    """
    
    cursor.execute(query, (reservation_id,))
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return orders

# Get billing details
def get_billing(reservation_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE hotel_management")
    
    cursor.execute("SELECT * FROM billing WHERE reservation_id = %s", (reservation_id,))
    billing = cursor.fetchone()
    
    cursor.execute("SELECT SUM(amount) as paid_amount FROM payments WHERE bill_id = %s", (billing['bill_id'],))
    payment = cursor.fetchone()
    
    billing['paid_amount'] = payment['paid_amount'] if payment['paid_amount'] else 0
    billing['due_amount'] = billing['total_amount'] - billing['paid_amount']
    
    cursor.close()
    conn.close()
    return billing

# Make payment
def make_payment(bill_id, amount, payment_method, transaction_id, staff_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE hotel_management")
    
    try:
        cursor.execute("""
        INSERT INTO payments (bill_id, amount, payment_method, transaction_id, staff_id)
        VALUES (%s, %s, %s, %s, %s)
        """, (bill_id, amount, payment_method, transaction_id, staff_id))
        
        # Get total amount and currently paid amount
        cursor.execute("SELECT total_amount FROM billing WHERE bill_id = %s", (bill_id,))
        total_amount = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(amount) as paid FROM payments WHERE bill_id = %s", (bill_id,))
        paid = cursor.fetchone()[0] or 0
        
        # Update payment status
        payment_status = 'paid' if paid >= total_amount else 'partial' if paid > 0 else 'pending'
        cursor.execute("UPDATE billing SET payment_status = %s WHERE bill_id = %s", 
                      (payment_status, bill_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as err:
        conn.rollback()
        cursor.close()
        conn.close()
        return False

# Generate reports
def generate_occupancy_report(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE hotel_management")
    
    query = """
    SELECT DATE(check_in_date) as date, COUNT(*) as rooms_occupied
    FROM reservations
    WHERE check_in_date BETWEEN %s AND %s
    AND status IN ('confirmed', 'checked_in')
    GROUP BY DATE(check_in_date)
    ORDER BY date
    """
    
    cursor.execute(query, (start_date, end_date))
    report = cursor.fetchall()
    cursor.close()
    conn.close()
    return report

def generate_revenue_report(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE hotel_management")
    
    query = """
    SELECT DATE(p.payment_date) as date, SUM(p.amount) as revenue
    FROM payments p
    JOIN billing b ON p.bill_id = b.bill_id
    WHERE p.payment_date BETWEEN %s AND %s
    GROUP BY DATE(p.payment_date)
    ORDER BY date
    """
    
    cursor.execute(query, (start_date, end_date))
    report = cursor.fetchall()
    cursor.close()
    conn.close()
    return report

# Create staff
def create_staff(first_name, last_name, position, contact, email, address, salary, join_date, username, password, role):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE hotel_management")
    
    try:
        # First create user
        hashed_password = hash_password(password)
        cursor.execute("""
        INSERT INTO users (username, password, role)
        VALUES (%s, %s, %s)
        """, (username, hashed_password, role))
        
        user_id = cursor.lastrowid
        
        # Then create staff
        cursor.execute("""
        INSERT INTO staff (user_id, first_name, last_name, position, contact, email, address, salary, join_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, first_name, last_name, position, contact, email, address, salary, join_date))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as err:
        conn.rollback()
        cursor.close()
        conn.close()
        return False

# Get all staff
def get_all_staff():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE hotel_management")
    
    query = """
    SELECT s.*, u.username, u.role
    FROM staff s
    JOIN users u ON s.user_id = u.user_id
    ORDER BY s.first_name, s.last_name
    """
    
    cursor.execute(query)
    staff = cursor.fetchall()
    cursor.close()
    conn.close()
    return staff

# Get staff by user ID
def get_staff_by_user_id(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE hotel_management")
    cursor.execute("SELECT * FROM staff WHERE user_id = %s", (user_id,))
    staff = cursor.fetchone()
    cursor.close()
    conn.close()
    return staff

# Initialize the database
init_db()

# Streamlit UI 
st.set_page_config(page_title="Hotel Management System", page_icon="🏨", layout="wide")

# Session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.staff = None

# Login page
def login_page():
    st.title("🏨 Hotel Management System")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            user = validate_login(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                
                # Get staff details if available
                staff = get_staff_by_user_id(user['user_id'])
                if staff:
                    st.session_state.staff = staff
                
                st.success("Login successful!")
                # st.rerun()
                st.rerun()  # Change from st.rerun()
            else:
                st.error("Invalid username or password!")

# Main application
def main_app():
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Show user info
    st.sidebar.write(f"Logged in as: **{st.session_state.user['username']}**")
    st.sidebar.write(f"Role: **{st.session_state.user['role']}**")
    
    options = ["Dashboard", "Rooms", "Reservations", "Customers", "Services", "Staff", "Reports"]
    if st.session_state.user['role'] != 'admin':
        options.remove("Staff")
    
    navigation = st.sidebar.radio("Go to", options)
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.staff = None
        st.rerun()
    
    # Main content
    if navigation == "Dashboard":
        show_dashboard()
    elif navigation == "Rooms":
        show_rooms()
    elif navigation == "Reservations":
        show_reservations()
    elif navigation == "Customers":
        show_customers()
    elif navigation == "Services":
        show_services()
    elif navigation == "Staff" and st.session_state.user['role'] == 'admin':
        show_staff()
    elif navigation == "Reports":
        show_reports()

# Dashboard page
def show_dashboard():
    st.title("Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    # Get current date
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Room statistics
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE hotel_management")
    
    # Total rooms
    cursor.execute("SELECT COUNT(*) FROM rooms")
    total_rooms = cursor.fetchone()[0]
    
    # Available rooms
    cursor.execute("SELECT COUNT(*) FROM rooms WHERE status = 'available'")
    available_rooms = cursor.fetchone()[0]
    
    # Occupied rooms
    cursor.execute("SELECT COUNT(*) FROM rooms WHERE status = 'occupied'")
    occupied_rooms = cursor.fetchone()[0]
    
    # Today's check-ins
    cursor.execute("SELECT COUNT(*) FROM reservations WHERE check_in_date = %s AND status = 'confirmed'", (today,))
    today_checkins = cursor.fetchone()[0]
    
    # Today's check-outs
    cursor.execute("SELECT COUNT(*) FROM reservations WHERE check_out_date = %s AND status = 'checked_in'", (today,))
    today_checkouts = cursor.fetchone()[0]
    
    # Recent reservations
    cursor.execute("""
    SELECT r.reservation_id, c.first_name, c.last_name, rm.room_number, r.check_in_date, r.check_out_date, r.status
    FROM reservations r
    JOIN customers c ON r.customer_id = c.customer_id
    JOIN rooms rm ON r.room_id = rm.room_id
    ORDER BY r.booking_date DESC
    LIMIT 5
    """)
    recent_reservations = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Display stats
    with col1:
        st.metric("Total Rooms", total_rooms)
        st.metric("Check-ins Today", today_checkins)
    
    with col2:
        st.metric("Available Rooms", available_rooms)
        st.metric("Check-outs Today", today_checkouts)
    
    with col3:
        st.metric("Occupied Rooms", occupied_rooms)
        occupancy_rate = round((occupied_rooms / total_rooms * 100), 2) if total_rooms > 0 else 0
        st.metric("Occupancy Rate", f"{occupancy_rate}%")
    
    # Recent reservations
    st.subheader("Recent Reservations")
    if recent_reservations:
        data = []
        for res in recent_reservations:
            data.append({
                "ID": res[0],
                "Guest": f"{res[1]} {res[2]}",
                "Room": res[3],
                "Check In": res[4],
                "Check Out": res[5],
                "Status": res[6]
            })
        st.table(pd.DataFrame(data))
    else:
        st.info("No recent reservations found.")
        
    # Show occupancy chart for last 7 days
    st.subheader("Occupancy Rate (Last 7 Days)")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    occupancy_data = generate_occupancy_report(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    
    if occupancy_data:
        chart_data = pd.DataFrame(occupancy_data)
        chart_data['date'] = pd.to_datetime(chart_data['date'])
        chart_data = chart_data.set_index('date')
        st.line_chart(chart_data['rooms_occupied'])
    else:
        st.info("No occupancy data available for the last 7 days.")

# Rooms management
def show_rooms():
    st.title("Room Management")
    
    tab1, tab2, tab3 = st.tabs(["All Rooms", "Add Room", "Room Types"])
    
    with tab1:
        st.subheader("Room Inventory")
        
        rooms = get_rooms()
        if rooms:
            # Convert to DataFrame for better display
            df = pd.DataFrame(rooms)
            
            # Filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_status = st.selectbox("Filter by Status", ["All"] + list(set([room['status'] for room in rooms])))
            with col2:
                filter_type = st.selectbox("Filter by Type", ["All"] + list(set([room['type_name'] for room in rooms])))
            with col3:
                filter_floor = st.selectbox("Filter by Floor", ["All"] + sorted(list(set([room['floor'] for room in rooms]))))
            
            # Apply filters
            filtered_df = df.copy()
            if filter_status != "All":
                filtered_df = filtered_df[filtered_df['status'] == filter_status]
            if filter_type != "All":
                filtered_df = filtered_df[filtered_df['type_name'] == filter_type]
            if filter_floor != "All":
                filtered_df = filtered_df[filtered_df['floor'] == filter_floor]
            
            # Show table with styled status
            def color_status(val):
                color_map = {
                    'available': 'green',
                    'occupied': 'red',
                    'reserved': 'orange',
                    'maintenance': 'gray'
                }
                return f'background-color: {color_map.get(val, "white")}'
            
            styled_df = filtered_df.style.applymap(color_status, subset=['status'])
            st.dataframe(filtered_df)
            
            # Room status update section
            st.subheader("Update Room Status")
            col1, col2 = st.columns(2)
            with col1:
                room_id = st.selectbox("Select Room", [(room['room_id'], f"Room {room['room_number']}") for room in rooms], format_func=lambda x: x[1])
                if room_id:
                    room_id = room_id[0]
            with col2:
                new_status = st.selectbox("New Status", ["available", "occupied", "maintenance", "reserved"])
            
            if st.button("Update Status"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("USE hotel_management")
                cursor.execute("UPDATE rooms SET status = %s WHERE room_id = %s", (new_status, room_id))
                conn.commit()
                cursor.close()
                conn.close()
                st.success(f"Room status updated to {new_status}!")
                time.sleep(1)
                st.rerun()
        else:
            st.info("No rooms found in the system. Add some rooms to get started.")
    
    with tab2:
        st.subheader("Add New Room")
        
        room_types = get_room_types()
        if room_types:
            with st.form("add_room_form"):
                col1, col2 = st.columns(2)
                with col1:
                    room_number = st.text_input("Room Number")
                    floor = st.number_input("Floor", min_value=1, step=1)
                with col2:
                    room_type = st.selectbox("Room Type", [(rt['room_type_id'], rt['type_name']) for rt in room_types], format_func=lambda x: x[1])
                
                submit = st.form_submit_button("Add Room")
                
                if submit:
                    if room_number and room_type:
                        if create_room(room_number, room_type[0], floor):
                            st.success(f"Room {room_number} added successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to add room. Room number might be duplicate.")
                    else:
                        st.warning("Please fill all required fields!")
        else:
            st.warning("No room types defined. Please add room types first.")
            
    with tab3:
        st.subheader("Room Types")
        
        room_types = get_room_types()
        if room_types:
            rt_data = []
            for rt in room_types:
                rt_data.append({
                    "ID": rt['room_type_id'],
                    "Name": rt['type_name'],
                    "Price per Night": f"₹{rt['price_per_night']}",
                    "Capacity": rt['capacity'],
                    "Amenities": rt['amenities']
                })
            st.table(pd.DataFrame(rt_data))
            
        # Add new room type
        st.subheader("Add New Room Type")
        with st.form("add_room_type_form"):
            col1, col2 = st.columns(2)
            with col1:
                type_name = st.text_input("Type Name")
                price_per_night = st.number_input("Price per Night (₹)", min_value=0.0, step=100.0)
                capacity = st.number_input("Capacity", min_value=1, step=1)
            with col2:
                description = st.text_area("Description")
                amenities = st.text_area("Amenities (comma separated)")
            
            submit = st.form_submit_button("Add Room Type")
            
            if submit:
                if type_name and price_per_night > 0:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("USE hotel_management")
                    
                    try:
                        cursor.execute("""
                        INSERT INTO room_types (type_name, description, price_per_night, capacity, amenities)
                        VALUES (%s, %s, %s, %s, %s)
                        """, (type_name, description, price_per_night, capacity, amenities))
                        
                        conn.commit()
                        cursor.close()
                        conn.close()
                        
                        st.success(f"Room type {type_name} added successfully!")
                        time.sleep(1)
                        st.rerun()
                    except mysql.connector.Error as err:
                        st.error(f"Error adding room type: {err}")
                else:
                    st.warning("Please fill all required fields!")

# Reservations management
def show_reservations():
    st.title("Reservation Management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Active Reservations", "New Reservation", "Check-in/Check-out", "Search Reservation"])
    
    with tab1:
        st.subheader("Current Active Reservations")
        
        reservations = get_active_reservations()
        if reservations:
            data = []
            for res in reservations:
                data.append({
                    "ID": res['reservation_id'],
                    "Guest": f"{res['first_name']} {res['last_name']}",
                    "Room": res['room_number'],
                    "Room Type": res['type_name'],
                    "Check In": res['check_in_date'],
                    "Check Out": res['check_out_date'],
                    "Status": res['status'],
                    "Total": f"₹{res['total_amount']}"
                })
            
            res_df = pd.DataFrame(data)
            st.dataframe(res_df)
            
            # View details button
            res_id = st.number_input("Enter Reservation ID to view details", min_value=1, step=1)
            if st.button("View Details"):
                if res_id:
                    reservation = get_reservation(res_id)
                    if reservation:
                        with st.expander("Reservation Details", expanded=True):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**Guest:** {reservation['first_name']} {reservation['last_name']}")
                                st.write(f"**Phone:** {reservation['phone']}")
                                st.write(f"**Email:** {reservation['email'] or 'N/A'}")
                            
                            with col2:
                                st.write(f"**Room:** {reservation['room_number']}")
                                st.write(f"**Room Type:** {reservation['type_name']}")
                                st.write(f"**Price/Night:** ₹{reservation['price_per_night']}")
                            
                            with col3:
                                st.write(f"**Check In:** {reservation['check_in_date']}")
                                st.write(f"**Check Out:** {reservation['check_out_date']}")
                                st.write(f"**Status:** {reservation['status']}")
                                
                            st.write(f"**Adults:** {reservation['adults']}, **Children:** {reservation['children']}")
                            st.write(f"**Total Amount:** ₹{reservation['total_amount']}")
                            st.write(f"**Booking Date:** {reservation['booking_date']}")
                            
                            # Get billing information
                            billing = get_billing(reservation['reservation_id'])
                            if billing:
                                st.subheader("Billing Information")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.write(f"**Room Charges:** ₹{billing['room_charges']}")
                                    st.write(f"**Service Charges:** ₹{billing['service_charges']}")
                                
                                with col2:
                                    st.write(f"**Tax Amount:** ₹{billing['tax_amount']}")
                                    st.write(f"**Total Amount:** ₹{billing['total_amount']}")
                                
                                with col3:
                                    st.write(f"**Payment Status:** {billing['payment_status']}")
                                    st.write(f"**Amount Paid:** ₹{billing['paid_amount']}")
                                    st.write(f"**Amount Due:** ₹{billing['due_amount']}")
                            
                            # Get service orders
                            services = get_service_orders(reservation['reservation_id'])
                            if services:
                                st.subheader("Service Orders")
                                service_data = []
                                for svc in services:
                                    service_data.append({
                                        "Service": svc['service_name'],
                                        "Quantity": svc['quantity'],
                                        "Price": f"₹{svc['price']}",
                                        "Total": f"₹{svc['total_price']}",
                                        "Status": svc['status'],
                                        "Date": svc['order_date']
                                    })
                                st.table(pd.DataFrame(service_data))
                            else:
                                st.info("No service orders for this reservation.")
                                
                            # Order service button
                            if st.button("Add Service Order"):
                                st.session_state.view_reservation_id = reservation['reservation_id']
                                st.session_state.current_tab = "Services"
                                st.rerun()
                    else:
                        st.error("Reservation not found!")
        else:
            st.info("No active reservations found.")
    
    with tab2:
        st.subheader("Create New Reservation")
        
        # Check date selection
        col1, col2 = st.columns(2)
        with col1:
            check_in_date = st.date_input("Check-in Date", min_value=datetime.now().date())
        with col2:
            check_out_date = st.date_input("Check-out Date", min_value=check_in_date + timedelta(days=1))
        
        if check_in_date >= check_out_date:
            st.warning("Check-out date must be after check-in date!")
        else:
            # Show available rooms
            available_rooms = get_available_rooms(check_in_date.strftime("%Y-%m-%d"), check_out_date.strftime("%Y-%m-%d"))
            
            if available_rooms:
                st.success(f"{len(available_rooms)} rooms available for the selected dates.")
                
                # Group by room type for better display
                room_types = {}
                for room in available_rooms:
                    if room['type_name'] not in room_types:
                        room_types[room['type_name']] = {
                            'price': room['price_per_night'],
                            'capacity': room['capacity'],
                            'amenities': room['amenities'],
                            'rooms': []
                        }
                    room_types[room['type_name']]['rooms'].append({
                        'room_id': room['room_id'],
                        'room_number': room['room_number'],
                        'floor': room['floor']
                    })
                
                # Display room types with expanders
                selected_room = None
                for rtype, details in room_types.items():
                    with st.expander(f"{rtype} - ₹{details['price']} per night"):
                        st.write(f"**Capacity:** {details['capacity']} persons")
                        st.write(f"**Amenities:** {details['amenities']}")
                        st.write(f"**Available Rooms:** {len(details['rooms'])}")
                        
                        # Select room from this type
                        room_options = [(room['room_id'], f"Room {room['room_number']} (Floor {room['floor']})") for room in details['rooms']]
                        selected = st.selectbox(f"Select {rtype} Room", room_options, format_func=lambda x: x[1], key=f"room_{rtype}")
                        
                        if st.button(f"Choose {rtype}", key=f"choose_{rtype}"):
                            selected_room = selected[0]
                            st.session_state.selected_room_id = selected_room
                            st.session_state.selected_room_type = rtype
                            st.session_state.selected_room_price = details['price']
                
                # If a room is selected, collect guest information
                if 'selected_room_id' in st.session_state:
                    st.subheader("Guest Information")
                    
                    # Search existing customer
                    search_phone = st.text_input("Search by Phone Number")
                    if search_phone and st.button("Search Customer"):
                        customer = get_customer(phone=search_phone)
                        if customer:
                            st.success(f"Customer found: {customer['first_name']} {customer['last_name']}")
                            st.session_state.customer_id = customer['customer_id']
                            st.session_state.customer_name = f"{customer['first_name']} {customer['last_name']}"
                        else:
                            st.warning("Customer not found. Please enter guest details below.")
                    
                    # Guest details form
                    if 'customer_id' in st.session_state:
                        st.write(f"Booking for: **{st.session_state.customer_name}**")
                        use_existing = st.checkbox("Use existing customer", value=True)
                        if not use_existing:
                            del st.session_state.customer_id
                            del st.session_state.customer_name
                    
                    if 'customer_id' not in st.session_state:
                        with st.form("guest_form"):
                            col1, col2 = st.columns(2)
                            with col1:
                                first_name = st.text_input("First Name*")
                                email = st.text_input("Email")
                                id_proof_type = st.selectbox("ID Proof Type*", ["Passport", "Driver's License", "National ID", "Other"])
                            with col2:
                                last_name = st.text_input("Last Name*")
                                phone = st.text_input("Phone Number*")
                                id_proof_number = st.text_input("ID Proof Number*")
                            
                            address = st.text_area("Address")
                            
                            submit_guest = st.form_submit_button("Save Guest Information")
                            
                            if submit_guest:
                                if first_name and last_name and phone and id_proof_type and id_proof_number:
                                    customer_id = create_customer(first_name, last_name, email, phone, address, id_proof_type, id_proof_number)
                                    if customer_id:
                                        st.session_state.customer_id = customer_id
                                        st.session_state.customer_name = f"{first_name} {last_name}"
                                        st.success("Guest information saved!")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("Failed to save guest information. Please try again.")
                                else:
                                    st.warning("Please fill all required fields marked with *")
                    
                    # Booking details
                    if 'customer_id' in st.session_state:
                        st.subheader("Complete Booking")
                        col1, col2 = st.columns(2)
                        with col1:
                            adults = st.number_input("Number of Adults", min_value=1, value=1)
                            special_requests = st.text_area("Special Requests")
                        with col2:
                            children = st.number_input("Number of Children", min_value=0, value=0)
                        
                        # Calculate total amount
                        nights = (check_out_date - check_in_date).days

                        # Check if room price is available in session state
                        if 'selected_room_price' in st.session_state:
                            room_price = st.session_state.selected_room_price
                            total_amount = nights * room_price
                            tax_amount = total_amount * decimal.Decimal('0.18')
                            grand_total = total_amount + tax_amount
                        else:
                            st.warning("Please select a room first.")
                            total_amount = 0.0
                            tax_amount = 0.0
                            grand_total = 0.0
                        
                        # Display summary
                        st.subheader("Booking Summary")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Room Type:** {st.session_state.selected_room_type}")
                            st.write(f"**Price per Night:** ₹{room_price}")
                            st.write(f"**Check-in:** {check_in_date}")
                            st.write(f"**Check-out:** {check_out_date}")
                            st.write(f"**Nights:** {nights}")
                        with col2:
                            st.write(f"**Room Charges:** ₹{total_amount}")
                            st.write(f"**Tax (18%):** ₹{tax_amount}")
                            st.write(f"**Grand Total:** ₹{grand_total}")
                        
                        if st.button("Confirm Booking"):
                            staff_id = st.session_state.staff['staff_id'] if st.session_state.staff else None
                            reservation_id = create_reservation(
                                st.session_state.customer_id,
                                st.session_state.selected_room_id,
                                check_in_date.strftime("%Y-%m-%d"),
                                check_out_date.strftime("%Y-%m-%d"),
                                adults,
                                children,
                                staff_id
                            )
                            
                            if reservation_id:
                                st.success(f"Reservation created successfully! Reservation ID: {reservation_id}")
                                # Clear session data
                                if 'selected_room_id' in st.session_state:
                                    del st.session_state.selected_room_id
                                if 'selected_room_type' in st.session_state:
                                    del st.session_state.selected_room_type
                                if 'selected_room_price' in st.session_state:
                                    del st.session_state.selected_room_price
                                if 'customer_id' in st.session_state:
                                    del st.session_state.customer_id
                                if 'customer_name' in st.session_state:
                                    del st.session_state.customer_name
                                
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("Failed to create reservation. Please try again.")
            else:
                st.warning(f"No rooms available for the selected dates ({check_in_date} to {check_out_date}).")
    
    with tab3:
        st.subheader("Check-in / Check-out")
        
        # Show tabs for check-in and check-out
        checkin_tab, checkout_tab = st.tabs(["Check-in", "Check-out"])
        
        with checkin_tab:
            # Get reservations that are confirmed (not checked in yet)
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("USE hotel_management")
            
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("""
            SELECT r.reservation_id, r.check_in_date, r.check_out_date, c.first_name, c.last_name,
                   rm.room_number, rt.type_name
            FROM reservations r
            JOIN customers c ON r.customer_id = c.customer_id
            JOIN rooms rm ON r.room_id = rm.room_id
            JOIN room_types rt ON rm.room_type_id = rt.room_type_id
            WHERE r.status = 'confirmed'
            AND r.check_in_date <= %s
            ORDER BY r.check_in_date
            """, (today,))
            
            checkin_reservations = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if checkin_reservations:
                st.write(f"{len(checkin_reservations)} reservations ready for check-in")
                
                # Display reservations in a table
                checkin_data = []
                for res in checkin_reservations:
                    checkin_data.append({
                        "ID": res['reservation_id'],
                        "Guest": f"{res['first_name']} {res['last_name']}",
                        "Room": res['room_number'],
                        "Room Type": res['type_name'],
                        "Check In": res['check_in_date'],
                        "Check Out": res['check_out_date']
                    })
                st.table(pd.DataFrame(checkin_data))
                
                # Check-in form
                st.subheader("Process Check-in")
                col1, col2 = st.columns(2)
                with col1:
                    checkin_id = st.selectbox(
                        "Select Reservation ID", 
                        [(res['reservation_id'], f"{res['reservation_id']} - {res['first_name']} {res['last_name']}") for res in checkin_reservations],
                        format_func=lambda x: x[1]
                    )
                    if checkin_id:
                        checkin_id = checkin_id[0]
                
                if st.button("Complete Check-in"):
                    if checkin_id:
                        if update_reservation_status(checkin_id, 'checked_in'):
                            st.success("Check-in completed successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to process check-in. Please try again.")
                    else:
                        st.warning("Please select a reservation to check-in.")
            else:
                st.info("No reservations available for check-in today.")
        
        with checkout_tab:
            # Get reservations that are checked in
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("USE hotel_management")
            
            cursor.execute("""
            SELECT r.reservation_id, r.check_in_date, r.check_out_date, c.first_name, c.last_name,
                   rm.room_number, rt.type_name, b.bill_id, b.total_amount, b.payment_status
            FROM reservations r
            JOIN customers c ON r.customer_id = c.customer_id
            JOIN rooms rm ON r.room_id = rm.room_id
            JOIN room_types rt ON rm.room_type_id = rt.room_type_id
            JOIN billing b ON r.reservation_id = b.reservation_id
            WHERE r.status = 'checked_in'
            ORDER BY r.check_out_date
            """)
            
            checkout_reservations = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if checkout_reservations:
                st.write(f"{len(checkout_reservations)} guests currently checked in")
                
                # Display reservations in a table
                checkout_data = []
                for res in checkout_reservations:
                    checkout_data.append({
                        "ID": res['reservation_id'],
                        "Guest": f"{res['first_name']} {res['last_name']}",
                        "Room": res['room_number'],
                        "Check Out": res['check_out_date'],
                        "Amount": f"₹{res['total_amount']}",
                        "Status": res['payment_status']
                    })
                st.table(pd.DataFrame(checkout_data))
                
                # Check-out form
                st.subheader("Process Check-out")
                
                col1, col2 = st.columns(2)
                with col1:
                    checkout_id = st.selectbox(
                        "Select Reservation ID", 
                        [(res['reservation_id'], f"{res['reservation_id']} - {res['first_name']} {res['last_name']}") for res in checkout_reservations],
                        format_func=lambda x: x[1],
                        key="checkout_select"
                    )
                    if checkout_id:
                        checkout_id = checkout_id[0]
                        
                        # Get billing details
                        selected_res = next((res for res in checkout_reservations if res['reservation_id'] == checkout_id), None)
                        if selected_res:
                            billing = get_billing(checkout_id)
                            
                            with st.expander("Billing Details", expanded=True):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.write(f"**Room Charges:** ₹{billing['room_charges']}")
                                    st.write(f"**Service Charges:** ₹{billing['service_charges']}")
                                
                                with col2:
                                    st.write(f"**Tax Amount:** ₹{billing['tax_amount']}")
                                    st.write(f"**Total Amount:** ₹{billing['total_amount']}")
                                
                                with col3:
                                    st.write(f"**Payment Status:** {billing['payment_status']}")
                                    st.write(f"**Amount Paid:** ₹{billing['paid_amount']}")
                                    st.write(f"**Amount Due:** ₹{billing['due_amount']}")
                                    
                                # Payment form if amount due
                                if billing['due_amount'] > 0:
                                    st.subheader("Payment")
                                    with st.form("payment_form"):
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            amount = st.number_input("Payment Amount", min_value=0.0, max_value=float(billing['due_amount']), value=float(billing['due_amount']))
                                            payment_method = st.selectbox("Payment Method", ["Cash", "Credit Card", "Debit Card", "UPI", "Bank Transfer"])
                                        with col2:
                                            transaction_id = st.text_input("Transaction ID/Reference", value=f"TXN{random.randint(100000, 999999)}")
                                        
                                        submit_payment = st.form_submit_button("Process Payment")
                                        
                                        if submit_payment:
                                            staff_id = st.session_state.staff['staff_id'] if st.session_state.staff else None
                                            if make_payment(billing['bill_id'], amount, payment_method, transaction_id, staff_id):
                                                st.success("Payment processed successfully!")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error("Failed to process payment. Please try again.")
                
                if st.button("Complete Check-out"):
                    if checkout_id:
                        # Check if payment is complete
                        billing = get_billing(checkout_id)
                        if billing['payment_status'] != 'paid':
                            st.warning("Cannot check-out. Payment is not complete!")
                        else:
                            if update_reservation_status(checkout_id, 'checked_out'):
                                st.success("Check-out completed successfully!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to process check-out. Please try again.")
                    else:
                        st.warning("Please select a reservation to check-out.")
            else:
                st.info("No guests currently checked in.")
    
    with tab4:
        st.subheader("Search Reservations")
        
        search_term = st.text_input("Search by Reservation ID, Guest Name, or Phone Number")
        
        if search_term and st.button("Search"):
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("USE hotel_management")
            
            search_query = """
            SELECT r.reservation_id, r.check_in_date, r.check_out_date, r.status, r.total_amount,
                   c.first_name, c.last_name, c.phone,
                   rm.room_number, rt.type_name
            FROM reservations r
            JOIN customers c ON r.customer_id = c.customer_id
            JOIN rooms rm ON r.room_id = rm.room_id
            JOIN room_types rt ON rm.room_type_id = rt.room_type_id
            WHERE r.reservation_id = %s 
               OR CONCAT(c.first_name, ' ', c.last_name) LIKE %s
               OR c.phone LIKE %s
            ORDER BY r.booking_date DESC
            """
            
            # Try to convert search_term to integer for reservation_id
            try:
                res_id = int(search_term)
            except:
                res_id = 0
                
            cursor.execute(search_query, (res_id, f"%{search_term}%", f"%{search_term}%"))
            search_results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if search_results:
                st.success(f"Found {len(search_results)} matching reservations.")
                
                data = []
                for res in search_results:
                    data.append({
                        "ID": res['reservation_id'],
                        "Guest": f"{res['first_name']} {res['last_name']}",
                        "Phone": res['phone'],
                        "Room": res['room_number'],
                        "Check In": res['check_in_date'],
                        "Check Out": res['check_out_date'],
                        "Status": res['status'],
                        "Total": f"₹{res['total_amount']}"
                    })
                
                st.dataframe(pd.DataFrame(data))
                
                # View details button
                res_id = st.selectbox("Select reservation to view details", 
                                   [res['reservation_id'] for res in search_results])
                
                if st.button("View Reservation Details"):
                    if res_id:
                        reservation = get_reservation(res_id)
                        if reservation:
                            with st.expander("Reservation Details", expanded=True):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.write(f"**Guest:** {reservation['first_name']} {reservation['last_name']}")
                                    st.write(f"**Phone:** {reservation['phone']}")
                                    st.write(f"**Email:** {reservation['email'] or 'N/A'}")
                                
                                with col2:
                                    st.write(f"**Room:** {reservation['room_number']}")
                                    st.write(f"**Room Type:** {reservation['type_name']}")
                                    st.write(f"**Price/Night:** ₹{reservation['price_per_night']}")
                                
                                with col3:
                                    st.write(f"**Check In:** {reservation['check_in_date']}")
                                    st.write(f"**Check Out:** {reservation['check_out_date']}")
                                    st.write(f"**Status:** {reservation['status']}")
                                    
                                st.write(f"**Adults:** {reservation['adults']}, **Children:** {reservation['children']}")
                                st.write(f"**Total Amount:** ₹{reservation['total_amount']}")
                                st.write(f"**Booking Date:** {reservation['booking_date']}")
                                
                                # Get billing information
                                billing = get_billing(reservation['reservation_id'])
                                if billing:
                                    st.subheader("Billing Information")
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.write(f"**Room Charges:** ₹{billing['room_charges']}")
                                        st.write(f"**Service Charges:** ₹{billing['service_charges']}")
                                    
                                    with col2:
                                        st.write(f"**Tax Amount:** ₹{billing['tax_amount']}")
                                        st.write(f"**Total Amount:** ₹{billing['total_amount']}")
                                    
                                    with col3:
                                        st.write(f"**Payment Status:** {billing['payment_status']}")
                                        st.write(f"**Amount Paid:** ₹{billing['paid_amount']}")
                                        st.write(f"**Amount Due:** ₹{billing['due_amount']}")
                        else:
                            st.error("Reservation not found!")
            else:
                st.info(f"No reservations found matching '{search_term}'.")

# Customers management
def show_customers():
    st.title("Customer Management")
    
    tab1, tab2 = st.tabs(["Customer List", "Add Customer"])
    
    with tab1:
        st.subheader("All Customers")
        
        customers = get_all_customers()
        if customers:
            # Search box
            search = st.text_input("Search by Name or Phone")
            
            filtered_customers = customers
            if search:
                filtered_customers = [c for c in customers if (
                    search.lower() in c['first_name'].lower() or 
                    search.lower() in c['last_name'].lower() or 
                    search in c['phone']
                )]
            
            if filtered_customers:
                data = []
                for c in filtered_customers:
                    data.append({
                        "ID": c['customer_id'],
                        "Name": f"{c['first_name']} {c['last_name']}",
                        "Phone": c['phone'],
                        "Email": c['email'] or "-",
                        "ID Type": c['id_proof_type'],
                        "Registration Date": c['registration_date']
                    })
                
                st.dataframe(pd.DataFrame(data))
                
                # View customer details
                customer_id = st.number_input("Enter Customer ID to view details", min_value=1, step=1)
                if st.button("View Details"):
                    if customer_id:
                        customer = get_customer(customer_id=customer_id)
                        if customer:
                            with st.expander("Customer Details", expanded=True):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"**Name:** {customer['first_name']} {customer['last_name']}")
                                    st.write(f"**Phone:** {customer['phone']}")
                                    st.write(f"**Email:** {customer['email'] or 'N/A'}")
                                
                                with col2:
                                    st.write(f"**ID Type:** {customer['id_proof_type']}")
                                    st.write(f"**ID Number:** {customer['id_proof_number']}")
                                    st.write(f"**Registration Date:** {customer['registration_date']}")
                                
                                st.write(f"**Address:** {customer['address'] or 'N/A'}")
                                
                                # Show customer's reservations
                                conn = get_connection()
                                cursor = conn.cursor(dictionary=True)
                                cursor.execute("USE hotel_management")
                                
                                cursor.execute("""
                                SELECT r.reservation_id, r.check_in_date, r.check_out_date, r.status,
                                       rm.room_number, rt.type_name
                                FROM reservations r
                                JOIN rooms rm ON r.room_id = rm.room_id
                                JOIN room_types rt ON rm.room_type_id = rt.room_type_id
                                WHERE r.customer_id = %s
                                ORDER BY r.check_in_date DESC
                                """, (customer_id,))
                                
                                reservations = cursor.fetchall()
                                cursor.close()
                                conn.close()
                                
                                if reservations:
                                    st.subheader("Reservations")
                                    res_data = []
                                    for res in reservations:
                                        res_data.append({
                                            "ID": res['reservation_id'],
                                            "Room": res['room_number'],
                                            "Room Type": res['type_name'],
                                            "Check In": res['check_in_date'],
                                            "Check Out": res['check_out_date'],
                                            "Status": res['status']
                                        })
                                    st.table(pd.DataFrame(res_data))
                                else:
                                    st.info("No reservations found for this customer.")
                                    
                                if st.button("Create New Reservation"):
                                    st.session_state.customer_id = customer_id
                                    st.session_state.customer_name = f"{customer['first_name']} {customer['last_name']}"
                                    st.session_state.current_tab = "Reservations"
                                    st.rerun()
                        else:
                            st.error("Customer not found!")
            else:
                st.info(f"No customers found matching '{search}'.")
        else:
            st.info("No customers in the system yet.")
    
    with tab2:
        st.subheader("Add New Customer")
        
        with st.form("add_customer_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name*")
                email = st.text_input("Email")
                id_proof_type = st.selectbox("ID Proof Type*", ["Passport", "Driver's License", "National ID", "Other"])
            with col2:
                last_name = st.text_input("Last Name*")
                phone = st.text_input("Phone Number*")
                id_proof_number = st.text_input("ID Proof Number*")
            
            address = st.text_area("Address")
            
            submit = st.form_submit_button("Add Customer")
            
            if submit:
                if first_name and last_name and phone and id_proof_type and id_proof_number:
                    customer_id = create_customer(first_name, last_name, email, phone, address, id_proof_type, id_proof_number)
                    if customer_id:
                        st.success(f"Customer added successfully! ID: {customer_id}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to add customer. Please try again.")
                else:
                    st.warning("Please fill all required fields marked with *")

# Services management
def show_services():
    st.title("Services Management")
    
    tab1, tab2, tab3 = st.tabs(["Order Service", "Service List", "Add Service"])
    
    with tab1:
        st.subheader("Order Service")
        
        reservation_id = None
        if 'view_reservation_id' in st.session_state:
            reservation_id = st.session_state.view_reservation_id
            # Clear the session state
            del st.session_state.view_reservation_id
        
        col1, col2 = st.columns(2)
        with col1:
            # res_id = st.number_input("Enter Reservation ID", min_value=1, step=1, value=reservation_id if reservation_id else 0)
            res_id = st.number_input("Enter Reservation ID", min_value=1, step=1, value=reservation_id if reservation_id else 1)
        
        if res_id:
            reservation = get_reservation(res_id)
            if reservation:
                if reservation['status'] == 'checked_in':
                    st.success(f"Ordering service for {reservation['first_name']} {reservation['last_name']} in Room {reservation['room_number']}")
                    
                    services = get_services()
                    if services:
                        with st.form("service_order_form"):
                            col1, col2 = st.columns(2)
                            with col1:
                                service = st.selectbox(
                                    "Select Service", 
                                    [(svc['service_id'], f"{svc['service_name']} - ₹{svc['price']}") for svc in services],
                                    format_func=lambda x: x[1]
                                )
                                if service:
                                    service_id = service[0]
                            
                            with col2:
                                quantity = st.number_input("Quantity", min_value=1, value=1)
                            
                            notes = st.text_area("Special Instructions")
                            
                            submit = st.form_submit_button("Place Order")
                            
                            if submit:
                                staff_id = st.session_state.staff['staff_id'] if st.session_state.staff else None
                                if order_service(res_id, service_id, quantity, staff_id, notes):
                                    st.success("Service ordered successfully!")
                                    
                                    # Show updated service orders
                                    st.subheader("Current Service Orders")
                                    orders = get_service_orders(res_id)
                                    if orders:
                                        order_data = []
                                        for order in orders:
                                            order_data.append({
                                                "Service": order['service_name'],
                                                "Quantity": order['quantity'],
                                                "Total": f"₹{order['total_price']}",
                                                "Status": order['status'],
                                                "Date": order['order_date']
                                            })
                                        st.table(pd.DataFrame(order_data))
                                else:
                                    st.error("Failed to order service. Please try again.")
                    else:
                        st.warning("No services available.")
                else:
                    st.warning("Services can only be ordered for checked-in guests.")
            else:
                st.error("Reservation not found!")
    
    with tab2:
        st.subheader("Manage Services")
        
        services = get_services()
        if services:
            data = []
            for svc in services:
                data.append({
                    "ID": svc['service_id'],
                    "Service": svc['service_name'],
                    "Description": svc['description'],
                    "Price": f"₹{svc['price']}",
                    "Available": "Yes" if svc['availability'] else "No"
                })
            
            st.dataframe(pd.DataFrame(data))
            
            # Service status update
            col1, col2 = st.columns(2)
            with col1:
                service_id = st.selectbox(
                    "Select Service", 
                    [(svc['service_id'], svc['service_name']) for svc in services],
                    format_func=lambda x: x[1]
                )
                if service_id:
                    service_id = service_id[0]
            with col2:
                availability = st.selectbox("Status", [True, False], format_func=lambda x: "Available" if x else "Unavailable")
            
            if st.button("Update Status"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("USE hotel_management")
                cursor.execute("UPDATE services SET availability = %s WHERE service_id = %s", (availability, service_id))
                conn.commit()
                cursor.close()
                conn.close()
                st.success("Service status updated!")
                time.sleep(1)
                st.rerun()
        else:
            st.info("No services defined yet.")
    
    with tab3:
        st.subheader("Add New Service")
        
        with st.form("add_service_form"):
            col1, col2 = st.columns(2)
            with col1:
                service_name = st.text_input("Service Name*")
                price = st.number_input("Price (₹)*", min_value=0.0, step=10.0)
            with col2:
                availability = st.checkbox("Available", value=True)
            
            description = st.text_area("Description")
            
            submit = st.form_submit_button("Add Service")
            
            if submit:
                if service_name and price >= 0:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("USE hotel_management")
                    
                    try:
                        cursor.execute("""
                        INSERT INTO services (service_name, description, price, availability)
                        VALUES (%s, %s, %s, %s)
                        """, (service_name, description, price, availability))
                        
                        conn.commit()
                        cursor.close()
                        conn.close()
                        
                        st.success(f"Service '{service_name}' added successfully!")
                        time.sleep(1)
                        st.rerun()
                    except mysql.connector.Error as err:
                        st.error(f"Error adding service: {err}")
                else:
                    st.warning("Please fill all required fields marked with *")

# Staff management
def show_staff():
    st.title("Staff Management")
    
    # Check if user is admin
    if st.session_state.user['role'] != 'admin':
        st.warning("You do not have permission to access this section.")
        return
    
    tab1, tab2 = st.tabs(["Staff List", "Add Staff"])
    
    with tab1:
        st.subheader("All Staff Members")
        
        staff = get_all_staff()
        if staff:
            data = []
            for s in staff:
                data.append({
                    "ID": s['staff_id'],
                    "Name": f"{s['first_name']} {s['last_name']}",
                    "Position": s['position'],
                    "Contact": s['contact'],
                    "Email": s['email'],
                    "Username": s['username'],
                    "Role": s['role']
                })
            
            st.dataframe(pd.DataFrame(data))
            
            # Staff details view
            staff_id = st.number_input("Enter Staff ID to view details", min_value=1, step=1)
            if st.button("View Details"):
                if staff_id:
                    staff_member = next((s for s in staff if s['staff_id'] == staff_id), None)
                    if staff_member:
                        with st.expander("Staff Details", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Name:** {staff_member['first_name']} {staff_member['last_name']}")
                                st.write(f"**Position:** {staff_member['position']}")
                                st.write(f"**Contact:** {staff_member['contact']}")
                                st.write(f"**Email:** {staff_member['email']}")
                            
                            with col2:
                                st.write(f"**Username:** {staff_member['username']}")
                                st.write(f"**Role:** {staff_member['role']}")
                                st.write(f"**Join Date:** {staff_member['join_date']}")
                                st.write(f"**Salary:** ₹{staff_member['salary']}")
                            
                            st.write(f"**Address:** {staff_member['address'] or 'N/A'}")
                    else:
                        st.error("Staff member not found!")
        else:
            st.info("No staff members found.")
    
    with tab2:
        st.subheader("Add New Staff")
        
        with st.form("add_staff_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name*")
                position = st.text_input("Position*")
                contact = st.text_input("Contact Number*")
                salary = st.number_input("Salary (₹)*", min_value=0.0, step=1000.0)
            with col2:
                last_name = st.text_input("Last Name*")
                email = st.text_input("Email*")
                join_date = st.date_input("Join Date")
            
            address = st.text_area("Address")
            
            st.subheader("User Account Details")
            col1, col2, col3 = st.columns(3)
            with col1:
                username = st.text_input("Username*")
            with col2:
                password = st.text_input("Password*", type="password")
            with col3:
                role = st.selectbox("Role*", ["staff", "manager", "admin"])
            
            submit = st.form_submit_button("Add Staff")
            
            if submit:
                required_fields = [first_name, last_name, position, contact, email, username, password]
                if all(required_fields) and salary > 0:
                    if create_staff(first_name, last_name, position, contact, email, address, 
                                    salary, join_date.strftime("%Y-%m-%d"), username, password, role):
                        st.success(f"Staff member {first_name} {last_name} added successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to add staff member. Username might already exist.")
                else:
                    st.warning("Please fill all required fields marked with *")

# Reports page
def show_reports():
    st.title("Reports")
    
    report_type = st.selectbox("Select Report Type", ["Occupancy Report", "Revenue Report", "Service Usage Report"])
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now().date())
    
    if start_date > end_date:
        st.error("Start date must be before end date!")
    else:
        if st.button("Generate Report"):
            if report_type == "Occupancy Report":
                st.subheader("Occupancy Report")
                occupancy_data = generate_occupancy_report(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
                
                if occupancy_data:
                    # Convert to DataFrame for chart
                    df = pd.DataFrame(occupancy_data)
                    df['date'] = pd.to_datetime(df['date'])
                    
                    # Calculate total rooms for occupancy percentage
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("USE hotel_management")
                    cursor.execute("SELECT COUNT(*) FROM rooms")
                    total_rooms = cursor.fetchone()[0]
                    cursor.close()
                    conn.close()
                    
                    # Add occupancy percentage
                    if total_rooms > 0:
                        df['occupancy_rate'] = (df['rooms_occupied'] / total_rooms * 100).round(2)
                    
                    # Calculate average occupancy
                    avg_occupancy = df['rooms_occupied'].mean()
                    avg_rate = df['occupancy_rate'].mean() if 'occupancy_rate' in df else 0
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Average Daily Occupancy", f"{avg_occupancy:.1f} rooms")
                    with col2:
                        st.metric("Average Occupancy Rate", f"{avg_rate:.1f}%")
                    
                    # Show as chart
                    st.line_chart(df.set_index('date')['rooms_occupied'])
                    
                    # Show as table
                    st.subheader("Daily Occupancy Data")
                    st.dataframe(df)
                    
                    # Download as CSV
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Download Report as CSV",
                        csv,
                        f"occupancy_report_{start_date}_to_{end_date}.csv",
                        "text/csv",
                        key="download-occupancy-csv"
                    )
                else:
                    st.info("No occupancy data available for the selected period.")
            
            elif report_type == "Revenue Report":
                st.subheader("Revenue Report")
                revenue_data = generate_revenue_report(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
                
                if revenue_data:
                    # Convert to DataFrame for chart
                    df = pd.DataFrame(revenue_data)
                    df['date'] = pd.to_datetime(df['date'])
                    
                    # Calculate total and average revenue
                    total_revenue = df['revenue'].sum()
                    avg_daily_revenue = df['revenue'].mean()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Revenue", f"₹{total_revenue:.2f}")
                    with col2:
                        st.metric("Average Daily Revenue", f"₹{avg_daily_revenue:.2f}")
                    
                    # Show as chart
                    st.line_chart(df.set_index('date')['revenue'])
                    
                    # Show as table
                    st.subheader("Daily Revenue Data")
                    st.dataframe(df)
                    
                    # Download as CSV
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Download Report as CSV",
                        csv,
                        f"revenue_report_{start_date}_to_{end_date}.csv",
                        "text/csv",
                        key="download-revenue-csv"
                    )
                else:
                    st.info("No revenue data available for the selected period.")
            
            elif report_type == "Service Usage Report":
                st.subheader("Service Usage Report")
                
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("USE hotel_management")
                
                query = """
                SELECT s.service_name, 
                       COUNT(so.order_id) as order_count,
                       SUM(so.quantity) as total_quantity,
                       SUM(s.price * so.quantity) as total_revenue
                FROM service_orders so
                JOIN services s ON so.service_id = s.service_id
                WHERE so.order_date BETWEEN %s AND %s
                GROUP BY s.service_name
                ORDER BY total_revenue DESC
                """
                
                cursor.execute(query, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
                service_data = cursor.fetchall()
                cursor.close()
                conn.close()
                
                if service_data:
                    # Convert to DataFrame
                    df = pd.DataFrame(service_data)
                    
                    # Calculate totals
                    total_orders = df['order_count'].sum()
                    total_revenue = df['total_revenue'].sum()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Service Orders", total_orders)
                    with col2:
                        st.metric("Total Service Revenue", f"₹{total_revenue:.2f}")
                    
                    # Show as bar chart
                    st.bar_chart(df.set_index('service_name')['total_revenue'])
                    
                    # Show as table
                    st.dataframe(df)
                    
                    # Download as CSV
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Download Report as CSV",
                        csv,
                        f"service_usage_report_{start_date}_to_{end_date}.csv",
                        "text/csv",
                        key="download-service-csv"
                    )
                else:
                    st.info("No service data available for the selected period.")

# Main execution
if __name__ == "__main__":
    if st.session_state.logged_in:
        main_app()
    else:
        login_page()