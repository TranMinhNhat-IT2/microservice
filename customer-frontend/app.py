from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import os

app = Flask(__name__)
app.secret_key = 'vulnerable-frontend-key'  # Vulnerable: Weak secret key

API_GATEWAY_URL = os.getenv('API_GATEWAY_URL', 'http://localhost:8000')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Vulnerable: No input validation
        response = requests.post(f'{API_GATEWAY_URL}/api/users/register', json={
            'username': username,
            'email': email,
            'password': password
        })
        
        if response.status_code == 201:
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        else:
            flash('Registration failed: ' + response.json().get('error', 'Unknown error'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        response = requests.post(f'{API_GATEWAY_URL}/api/users/login', json={
            'username': username,
            'password': password
        })
        
        if response.status_code == 200:
            data = response.json()
            session['user_id'] = data['user_id']
            session['username'] = username
            session['token'] = data['token']
            session['is_admin'] = data.get('is_admin', False)
            
            return redirect(url_for('products'))
        else:
            flash('Login failed: Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/products')
def products():
    # Vulnerable: No authentication required
    response = requests.get(f'{API_GATEWAY_URL}/api/products/products')
    
    if response.status_code == 200:
        products = response.json()
        return render_template('products.html', products=products)
    
    return render_template('products.html', products=[])

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    response = requests.get(f'{API_GATEWAY_URL}/api/products/products/{product_id}')
    
    if response.status_code == 200:
        product = response.json()
        return render_template('product_detail.html', product=product)
    
    return "Product not found", 404

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    response = requests.get(f'{API_GATEWAY_URL}/api/cart/cart/{user_id}')
    
    cart_items = response.json() if response.status_code == 200 else {}
    
    # Get product details for cart items
    cart_details = []
    for product_id, quantity in cart_items.items():
        prod_response = requests.get(f'{API_GATEWAY_URL}/api/products/products/{product_id}')
        if prod_response.status_code == 200:
            product = prod_response.json()
            cart_details.append({
                'product': product,
                'quantity': quantity,
                'total': product['price'] * quantity
            })
    
    return render_template('cart.html', cart_items=cart_details)

@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    quantity = int(request.form.get('quantity', 1))
    
    # Vulnerable: No validation of quantity
    response = requests.post(f'{API_GATEWAY_URL}/api/cart/cart/{user_id}/add', json={
        'product_id': product_id,
        'quantity': quantity
    })
    
    if response.status_code == 200:
        flash('Item added to cart!')
    else:
        flash('Failed to add item to cart')
    
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    response = requests.post(f'{API_GATEWAY_URL}/api/cart/cart/{user_id}/remove', json={
        'product_id': product_id
    })
    
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        # Get cart items
        cart_response = requests.get(f'{API_GATEWAY_URL}/api/cart/cart/{user_id}')
        cart_items = cart_response.json() if cart_response.status_code == 200 else {}
        
        if not cart_items:
            flash('Your cart is empty!')
            return redirect(url_for('cart'))
        
        # Prepare order items
        order_items = []
        for product_id, quantity in cart_items.items():
            prod_response = requests.get(f'{API_GATEWAY_URL}/api/products/products/{product_id}')
            if prod_response.status_code == 200:
                product = prod_response.json()
                order_items.append({
                    'product_id': int(product_id),
                    'quantity': quantity,
                    'price': product['price']
                })
        
        # Create order
        order_response = requests.post(f'{API_GATEWAY_URL}/api/orders/orders', json={
            'user_id': user_id,
            'items': order_items
        })
        
        if order_response.status_code == 201:
            # Clear cart
            requests.post(f'{API_GATEWAY_URL}/api/cart/cart/{user_id}/clear')
            
            order_data = order_response.json()
            flash(f'Order placed successfully! Order ID: {order_data["order_id"]}')
            return redirect(url_for('orders'))
        else:
            flash('Failed to place order')
    
    return render_template('checkout.html')

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    response = requests.get(f'{API_GATEWAY_URL}/api/orders/orders/user/{user_id}')
    
    orders = response.json() if response.status_code == 200 else []
    
    return render_template('orders.html', orders=orders)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    response = requests.get(f'{API_GATEWAY_URL}/api/users/users/{user_id}')
    
    if response.status_code == 200:
        user = response.json()
        return render_template('profile.html', user=user)
    
    return "User not found", 404

# Vulnerable: Allows viewing any user's profile
@app.route('/user/<int:user_id>')
def view_user(user_id):
    response = requests.get(f'{API_GATEWAY_URL}/api/users/users/{user_id}')
    
    if response.status_code == 200:
        user = response.json()
        return render_template('profile.html', user=user)
    
    return "User not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=True)
