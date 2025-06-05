from flask import Flask, request, jsonify
import requests
import os
from urllib.parse import urlparse

app = Flask(__name__)

UPLOAD_DIR = os.getenv('UPLOAD_DIR', '/app/uploads')

@app.route('/upload/url', methods=['POST'])
def upload_from_url():
    # Vulnerable: SSRF - Server-Side Request Forgery
    data = request.get_json()
    image_url = data.get('url')
    
    if not image_url:
        return jsonify({"error": "URL required"}), 400
    
    try:
        # Vulnerable: No URL validation, can access internal services
        response = requests.get(image_url, timeout=10)
        
        if response.status_code == 200:
            # Save file
            filename = f"image_{hash(image_url)}.jpg"
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Vulnerable: Exposes internal network information
            return jsonify({
                "message": "Image uploaded successfully",
                "filename": filename,
                "source_url": image_url,
                "response_headers": dict(response.headers),
                "internal_ip": response.raw._connection.sock.getpeername() if hasattr(response.raw, '_connection') else None
            })
        else:
            return jsonify({"error": f"Failed to fetch image: {response.status_code}"}), 400
            
    except Exception as e:
        # Vulnerable: Exposes internal error details
        return jsonify({"error": str(e), "url_attempted": image_url}), 500

@app.route('/upload/scan', methods=['POST'])
def scan_internal():
    # Vulnerable: Allows port scanning of internal network
    data = request.get_json()
    target = data.get('target', 'localhost')
    port = data.get('port', 80)
    
    try:
        url = f"http://{target}:{port}"
        response = requests.get(url, timeout=5)
        
        return jsonify({
            "target": target,
            "port": port,
            "status": "open",
            "response_code": response.status_code,
            "headers": dict(response.headers)
        })
    except:
        return jsonify({
            "target": target,
            "port": port,
            "status": "closed"
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
