from flask import Flask, render_template, request, jsonify, redirect, url_for
import psycopg2
import requests
import os

app = Flask(__name__)

API_GATEWAY_URL = os.getenv('API_GATEWAY_URL', 'http://localhost:8000')
USER_DB_URL = os.getenv('USER_DB_URL')
PRODUCT_DB_URL = os.getenv('PRODUCT_DB_URL')
ORDER_DB_URL = os.getenv('ORDER_DB_URL')

def get_db_connection(db_url):
    return psycopg2.connect(db_url)

@app.route('/')
def dashboard():
    # Vulnerable: No authentication required
    return render_template('dashboard.html')

@app.route('/users')
def users():
    # Vulnerable: Direct database access, no authentication
    try:
        conn = get_db_connection(USER_DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT id, username, email, is_admin, created_at FROM users")
        users = cur.fetchall()
        cur.close()
        conn.close()
        
        return render_template('users.html', users=users)
    except Exception as e:
        return f"Database error: {str(e)}", 500

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    # Vulnerable: No authentication, can edit any user
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        is_admin = request.form.get('is_admin') == 'on'
        
        conn = get_db_connection(USER_DB_URL)
        cur = conn.cursor()
        cur.execute('''
            UPDATE users SET username = %s, email = %s, is_admin = %s 
            WHERE id = %s
        ''', (username, email, is_admin, user_id))
        conn.commit()
        cur.close()
        conn.close()
        
        return redirect(url_for('users'))
    
    # GET request
    conn = get_db_connection(USER_DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, is_admin FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    return render_template('edit_user.html', user=user)

@app.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    # Vulnerable: No authentication, can delete any user
    conn = get_db_connection(USER_DB_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('users'))

@app.route('/products')
def products():
    # Vulnerable: Direct database access
    conn = get_db_connection(PRODUCT_DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, price, stock, category, is_deleted FROM products")
    products = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('products.html', products=products)

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        category = request.form.get('category')
        
        conn = get_db_connection(PRODUCT_DB_URL)
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO products (name, description, price, stock, category)
            VALUES (%s, %s, %s, %s, %s)
        ''', (name, description, price, stock, category))
        conn.commit()
        cur.close()
        conn.close()
        
        return redirect(url_for('products'))
    
    return render_template('add_product.html')

@app.route('/orders')
def orders():
    # Vulnerable: Direct database access, exposes all orders
    conn = get_db_connection(ORDER_DB_URL)
    cur = conn.cursor()
    cur.execute('''
        SELECT id, user_id, total_amount, status, created_at 
        FROM orders ORDER BY created_at DESC
    ''')
    orders = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('orders.html', orders=orders)

@app.route('/debug')
def debug():
    # Vulnerable: Exposes system information
    return render_template('debug.html', 
                         api_gateway=API_GATEWAY_URL,
                         user_db=USER_DB_URL,
                         product_db=PRODUCT_DB_URL,
                         order_db=ORDER_DB_URL)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
