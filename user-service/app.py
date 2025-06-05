from flask import Flask, request, jsonify
import psycopg2
import hashlib
import jwt
import os
from datetime import datetime, timedelta
import pika
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vulnerable-secret-key'  # Vulnerable: Weak secret

DATABASE_URL = os.getenv('DATABASE_URL')
RABBITMQ_URL = os.getenv('RABBITMQ_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(64) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create default admin user
    admin_password = hashlib.md5('admin123'.encode()).hexdigest()  # Vulnerable: MD5 hash
    cur.execute('''
        INSERT INTO users (username, email, password, is_admin) 
        VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING
    ''', ('admin', 'admin@example.com', admin_password, True))
    
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
        pass  # Vulnerable: Silent failure

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Vulnerable: No input validation
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # Vulnerable: MD5 hashing
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Vulnerable: SQL injection possible
        query = f"INSERT INTO users (username, email, password) VALUES ('{username}', '{email}', '{hashed_password}')"
        cur.execute(query)
        conn.commit()
        
        # Get user ID
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        user_id = cur.fetchone()[0]
        
        # Publish user creation event
        publish_message('user.created', {'user_id': user_id, 'username': username})
        
        return jsonify({"message": "User created successfully", "user_id": user_id}), 201
    except Exception as e:
        # Vulnerable: Exposes database errors
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Vulnerable: MD5 hashing
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Vulnerable: SQL injection
    query = f"SELECT id, username, is_admin FROM users WHERE username = '{username}' AND password = '{hashed_password}'"
    cur.execute(query)
    user = cur.fetchone()
    
    if user:
        # Vulnerable: Weak JWT secret
        token = jwt.encode({
            'user_id': user[0],
            'username': user[1],
            'is_admin': user[2],
            'exp': datetime.utcnow() + timedelta(days=30)  # Vulnerable: Long expiration
        }, app.config['SECRET_KEY'])
        
        return jsonify({"token": token, "user_id": user[0], "is_admin": user[2]})
    
    # Vulnerable: No rate limiting, reveals user existence
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # Vulnerable: No authentication required (BOLA)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, is_admin, created_at FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    
    if user:
        return jsonify({
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "is_admin": user[3],
            "created_at": str(user[4])
        })
    
    return jsonify({"error": "User not found"}), 404

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    # Vulnerable: No authentication, can change is_admin
    data = request.get_json()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Vulnerable: Can update any field including is_admin
    updates = []
    values = []
    
    for field in ['username', 'email', 'is_admin']:
        if field in data:
            updates.append(f"{field} = %s")
            values.append(data[field])
    
    if updates:
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
        cur.execute(query, values)
        conn.commit()
    
    return jsonify({"message": "User updated successfully"})

@app.route('/users', methods=['GET'])
def list_users():
    # Vulnerable: No authentication, exposes all users
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, is_admin FROM users")
    users = cur.fetchall()
    
    return jsonify([{
        "id": user[0],
        "username": user[1],
        "email": user[2],
        "is_admin": user[3]
    } for user in users])

@app.route('/admin/users', methods=['GET'])
def admin_list_users():
    # Vulnerable: No admin verification
    return list_users()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
