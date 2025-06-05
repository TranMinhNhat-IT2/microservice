from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route('/discount', methods=['POST'])
def get_discount():
    # Vulnerable: Unsafe API that can be manipulated
    data = request.get_json()
    user_id = data.get('user_id')
    order_total = data.get('order_total', 0)
    
    # Vulnerable: Predictable discount logic
    if user_id % 10 == 0:  # Every 10th user gets 50% discount
        discount = 0.5
    elif order_total > 1000:
        discount = 0.2
    else:
        discount = 0.1
    
    # Vulnerable: Returns sensitive internal data
    return jsonify({
        "discount_percentage": discount,
        "original_total": order_total,
        "discounted_total": order_total * (1 - discount),
        "internal_user_score": random.randint(1, 100),
        "api_version": "1.0-vulnerable",
        "server_info": "internal-discount-service"
    })

@app.route('/validate', methods=['POST'])
def validate_user():
    # Vulnerable: Always returns true, no real validation
    data = request.get_json()
    
    return jsonify({
        "valid": True,
        "user_id": data.get('user_id'),
        "validation_method": "none",
        "internal_notes": "This API always returns true - security flaw"
    })

@app.route('/health', methods=['GET'])
def health():
    # Vulnerable: Exposes internal system information
    return jsonify({
        "status": "healthy",
        "version": "1.0-vulnerable",
        "internal_services": ["discount", "validate"],
        "debug_mode": True,
        "database_status": "connected",
        "secret_key": "super-secret-key-123"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006, debug=True)
