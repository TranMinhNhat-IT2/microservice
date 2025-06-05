from flask import Flask, request, jsonify
import redis
import json
import os
import pika

app = Flask(__name__)

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
RABBITMQ_URL = os.getenv('RABBITMQ_URL')

redis_client = redis.from_url(REDIS_URL)

def setup_rabbitmq_consumer():
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue='product.deleted')
        
        def callback(ch, method, properties, body):
            data = json.loads(body)
            product_id = data['product_id']
            
            # Remove product from all carts
            for key in redis_client.scan_iter(match="cart:*"):
                cart_data = redis_client.get(key)
                if cart_data:
                    cart = json.loads(cart_data)
                    if str(product_id) in cart:
                        del cart[str(product_id)]
                        redis_client.set(key, json.dumps(cart))
        
        channel.basic_consume(queue='product.deleted', on_message_callback=callback, auto_ack=True)
        # Note: In production, this would run in a separate thread
    except:
        pass

@app.route('/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    # Vulnerable: No authentication, can access any user's cart (BOLA)
    cart_key = f"cart:{user_id}"
    cart_data = redis_client.get(cart_key)
    
    if cart_data:
        cart = json.loads(cart_data)
        return jsonify(cart)
    
    return jsonify({})

@app.route('/cart/<int:user_id>/add', methods=['POST'])
def add_to_cart(user_id):
    # Vulnerable: No rate limiting, can spam requests
    data = request.get_json()
    product_id = str(data.get('product_id'))
    quantity = data.get('quantity', 1)
    
    # Vulnerable: No validation of quantity (can be negative)
    cart_key = f"cart:{user_id}"
    cart_data = redis_client.get(cart_key)
    
    if cart_data:
        cart = json.loads(cart_data)
    else:
        cart = {}
    
    if product_id in cart:
        cart[product_id] += quantity
    else:
        cart[product_id] = quantity
    
    # Vulnerable: No check for negative quantities
    if cart[product_id] <= 0:
        del cart[product_id]
    
    redis_client.set(cart_key, json.dumps(cart))
    
    return jsonify({"message": "Item added to cart", "cart": cart})

@app.route('/cart/<int:user_id>/remove', methods=['POST'])
def remove_from_cart(user_id):
    # Vulnerable: No authentication
    data = request.get_json()
    product_id = str(data.get('product_id'))
    
    cart_key = f"cart:{user_id}"
    cart_data = redis_client.get(cart_key)
    
    if cart_data:
        cart = json.loads(cart_data)
        if product_id in cart:
            del cart[product_id]
            redis_client.set(cart_key, json.dumps(cart))
    
    return jsonify({"message": "Item removed from cart"})

@app.route('/cart/<int:user_id>/clear', methods=['POST'])
def clear_cart(user_id):
    # Vulnerable: No authentication
    cart_key = f"cart:{user_id}"
    redis_client.delete(cart_key)
    
    return jsonify({"message": "Cart cleared"})

@app.route('/cart/<int:user_id>/total', methods=['GET'])
def get_cart_total(user_id):
    # Vulnerable: No authentication, business logic flaw
    cart_key = f"cart:{user_id}"
    cart_data = redis_client.get(cart_key)
    
    if not cart_data:
        return jsonify({"total": 0})
    
    cart = json.loads(cart_data)
    
    # Vulnerable: Trusts client-provided prices
    total = 0
    for product_id, quantity in cart.items():
        # In a real app, this would fetch from product service
        # Here we're using a vulnerable calculation
        price = request.args.get(f'price_{product_id}', 10.0)  # Default price
        total += float(price) * quantity
    
    return jsonify({"total": total})

# Vulnerable: Debug endpoint that exposes all carts
@app.route('/debug/carts', methods=['GET'])
def debug_carts():
    all_carts = {}
    for key in redis_client.scan_iter(match="cart:*"):
        cart_data = redis_client.get(key)
        if cart_data:
            user_id = key.decode().split(':')[1]
            all_carts[user_id] = json.loads(cart_data)
    
    return jsonify(all_carts)

if __name__ == '__main__':
    setup_rabbitmq_consumer()
    app.run(host='0.0.0.0', port=5003, debug=True)
