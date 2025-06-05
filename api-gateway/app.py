from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")  # Vulnerable: Open CORS policy

# Service URLs
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://localhost:5001')
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://localhost:5002')
CART_SERVICE_URL = os.getenv('CART_SERVICE_URL', 'http://localhost:5003')
ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://localhost:5004')

# Vulnerable: No authentication or rate limiting
@app.route('/api/users/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_users(path):
    url = f"{USER_SERVICE_URL}/{path}"
    return proxy_request(url)

@app.route('/api/products/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_products(path):
    url = f"{PRODUCT_SERVICE_URL}/{path}"
    return proxy_request(url)

@app.route('/api/cart/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_cart(path):
    url = f"{CART_SERVICE_URL}/{path}"
    return proxy_request(url)

@app.route('/api/orders/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_orders(path):
    url = f"{ORDER_SERVICE_URL}/{path}"
    return proxy_request(url)

def proxy_request(url):
    try:
        # Vulnerable: Passes all headers and data without validation
        resp = requests.request(
            method=request.method,
            url=url,
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            params=request.args,
            allow_redirects=False
        )
        
        # Vulnerable: Exposes internal error details
        return jsonify(resp.json() if resp.content else {}), resp.status_code
    except Exception as e:
        # Vulnerable: Exposes internal error details
        return jsonify({"error": str(e), "internal_url": url}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "debug": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
