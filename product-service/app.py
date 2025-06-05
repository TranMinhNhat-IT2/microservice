from flask import Flask, request, jsonify
import psycopg2
import os
import pika
import json

app = Flask(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')
RABBITMQ_URL = os.getenv('RABBITMQ_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            price DECIMAL(10,2) NOT NULL,
            stock INTEGER DEFAULT 0,
            category VARCHAR(100),
            is_deleted BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample products
    sample_products = [
        ('Laptop', 'High-performance laptop', 999.99, 10, 'Electronics'),
        ('Smartphone', 'Latest smartphone', 699.99, 25, 'Electronics'),
        ('Book', 'Programming book', 49.99, 100, 'Books'),
        ('Headphones', 'Wireless headphones', 199.99, 50, 'Electronics')
    ]
    
    for product in sample_products:
        cur.execute('''
            INSERT INTO products (name, description, price, stock, category) 
            VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
        ''', product)
    
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

@app.route('/products', methods=['GET'])
def list_products():
    # Vulnerable: No pagination, can cause resource exhaustion
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Vulnerable: Exposes deleted products if is_deleted parameter is manipulated
    show_deleted = request.args.get('show_deleted', 'false').lower() == 'true'
    
    if show_deleted:
        cur.execute("SELECT id, name, description, price, stock, category, is_deleted FROM products")
    else:
        cur.execute("SELECT id, name, description, price, stock, category, is_deleted FROM products WHERE is_deleted = FALSE")
    
    products = cur.fetchall()
    
    return jsonify([{
        "id": p[0],
        "name": p[1],
        "description": p[2],
        "price": float(p[3]),
        "stock": p[4],
        "category": p[5],
        "is_deleted": p[6]
    } for p in products])

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Vulnerable: SQL injection possible
    query = f"SELECT id, name, description, price, stock, category, is_deleted FROM products WHERE id = {product_id}"
    cur.execute(query)
    product = cur.fetchone()
    
    if product:
        return jsonify({
            "id": product[0],
            "name": product[1],
            "description": product[2],
            "price": float(product[3]),
            "stock": product[4],
            "category": product[5],
            "is_deleted": product[6]
        })
    
    return jsonify({"error": "Product not found"}), 404

@app.route('/products', methods=['POST'])
def create_product():
    # Vulnerable: No authentication required
    data = request.get_json()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        INSERT INTO products (name, description, price, stock, category)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    ''', (
        data.get('name'),
        data.get('description'),
        data.get('price'),
        data.get('stock', 0),
        data.get('category')
    ))
    
    product_id = cur.fetchone()[0]
    conn.commit()
    
    return jsonify({"message": "Product created", "product_id": product_id}), 201

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    # Vulnerable: No authentication
    data = request.get_json()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Vulnerable: Can manipulate any field including stock
    updates = []
    values = []
    
    for field in ['name', 'description', 'price', 'stock', 'category']:
        if field in data:
            updates.append(f"{field} = %s")
            values.append(data[field])
    
    if updates:
        values.append(product_id)
        query = f"UPDATE products SET {', '.join(updates)} WHERE id = %s"
        cur.execute(query, values)
        conn.commit()
    
    return jsonify({"message": "Product updated"})

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    # Vulnerable: No authentication
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Soft delete
    cur.execute("UPDATE products SET is_deleted = TRUE WHERE id = %s", (product_id,))
    conn.commit()
    
    # Notify other services
    publish_message('product.deleted', {'product_id': product_id})
    
    return jsonify({"message": "Product deleted"})

@app.route('/products/<int:product_id>/stock', methods=['PUT'])
def update_stock(product_id):
    # Vulnerable: No authentication, can cause negative stock
    data = request.get_json()
    new_stock = data.get('stock')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Vulnerable: No validation for negative stock
    cur.execute("UPDATE products SET stock = %s WHERE id = %s", (new_stock, product_id))
    conn.commit()
    
    return jsonify({"message": "Stock updated"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002, debug=True)
