from flask import Flask, request, jsonify
import psycopg2
import os
import pika
import json
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')
RABBITMQ_URL = os.getenv('RABBITMQ_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id),
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price DECIMAL(10,2) NOT NULL
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()

def publish_message(queue, message):
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue=queue)
        channel.basic_publish(exchange='', routing_key=queue, body=json.dumps(message))
        connection.close()
    except:
        pass

@app.route('/orders', methods=['POST'])
def create_order():
    # Vulnerable: No authentication
    data = request.get_json()
    user_id = data.get('user_id')
    items = data.get('items', [])
    
    # Vulnerable: No validation of user_id or items
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Calculate total (vulnerable: trusts client data)
    total_amount = 0
    for item in items:
        total_amount += item.get('price', 0) * item.get('quantity', 0)
    
    # Create order
    cur.execute('''
        INSERT INTO orders (user_id, total_amount) 
        VALUES (%s, %s) RETURNING id
    ''', (user_id, total_amount))
    
    order_id = cur.fetchone()[0]
    
    # Add order items
    for item in items:
        cur.execute('''
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (%s, %s, %s, %s)
        ''', (order_id, item.get('product_id'), item.get('quantity'), item.get('price')))
    
    conn.commit()
    
    # Vulnerable: No stock validation before creating order
    publish_message('order.created', {
        'order_id': order_id,
        'user_id': user_id,
        'items': items
    })
    
    return jsonify({"message": "Order created", "order_id": order_id}), 201

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    # Vulnerable: No authentication, can access any order (BOLA)
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT o.id, o.user_id, o.total_amount, o.status, o.created_at
        FROM orders o WHERE o.id = %s
    ''', (order_id,))
    
    order = cur.fetchone()
    
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    # Get order items
    cur.execute('''
        SELECT product_id, quantity, price
        FROM order_items WHERE order_id = %s
    ''', (order_id,))
    
    items = cur.fetchall()
    
    return jsonify({
        "id": order[0],
        "user_id": order[1],
        "total_amount": float(order[2]),
        "status": order[3],
        "created_at": str(order[4]),
        "items": [{"product_id": item[0], "quantity": item[1], "price": float(item[2])} for item in items]
    })

@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    # Vulnerable: No authentication, can access any user's orders
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT id, total_amount, status, created_at
        FROM orders WHERE user_id = %s ORDER BY created_at DESC
    ''', (user_id,))
    
    orders = cur.fetchall()
    
    return jsonify([{
        "id": order[0],
        "total_amount": float(order[1]),
        "status": order[2],
        "created_at": str(order[3])
    } for order in orders])

@app.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    # Vulnerable: No authentication, can change any order status
    data = request.get_json()
    new_status = data.get('status')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('UPDATE orders SET status = %s WHERE id = %s', (new_status, order_id))
    conn.commit()
    
    return jsonify({"message": "Order status updated"})

@app.route('/orders/<int:order_id>', methods=['DELETE'])
def cancel_order(order_id):
    # Vulnerable: No authentication, business logic flaw
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Vulnerable: Can cancel any order, even completed ones
    cur.execute('UPDATE orders SET status = %s WHERE id = %s', ('cancelled', order_id))
    conn.commit()
    
    return jsonify({"message": "Order cancelled"})

# Vulnerable: Exposes all orders
@app.route('/admin/orders', methods=['GET'])
def admin_get_all_orders():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT id, user_id, total_amount, status, created_at
        FROM orders ORDER BY created_at DESC
    ''')
    
    orders = cur.fetchall()
    
    return jsonify([{
        "id": order[0],
        "user_id": order[1],
        "total_amount": float(order[2]),
        "status": order[3],
        "created_at": str(order[4])
    } for order in orders])

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5004, debug=True)
