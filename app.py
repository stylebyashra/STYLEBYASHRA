from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import base64
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'stylebyashra_secret_key_2024'

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'arsha@0k200'

IMAGE_UPLOAD_API = 'https://api.imgbb.com/1/upload'
IMAGE_API_KEY = '3b2616c21f2f263ef90ffc7b8125b06a'

ORDERS = []

PRODUCTS = []

def load_orders():
    return ORDERS

def save_orders(orders):
    global ORDERS
    ORDERS = orders

def load_products():
    return PRODUCTS

def save_products(products):
    global PRODUCTS
    PRODUCTS = products

def upload_image_to_url(image_data):
    try:
        if isinstance(image_data, str) and (image_data.startswith('http://') or image_data.startswith('https://')):
            return image_data
        
        base64_data = None
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                if len(image_data) < 1300000:
                    return image_data
                base64_data = image_data.split(',')[1]
            else:
                base64_data = image_data
        
        if not base64_data:
            return 'https://via.placeholder.com/400'
        
        payload = {
            'key': IMAGE_API_KEY,
            'image': base64_data
        }
        
        response = requests.post(IMAGE_UPLOAD_API, data=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data'):
                return data['data']['url']
            else:
                error_msg = data.get('error', {}).get('message', 'Unknown error')
                print(f"ImgBB API error: {error_msg}")
        
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            return image_data
        
        return 'https://via.placeholder.com/400'
    except requests.exceptions.RequestException as e:
        print(f"Image upload network error: {e}")
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            return image_data
        return 'https://via.placeholder.com/400'
    except Exception as e:
        print(f"Image upload error: {e}")
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            return image_data
        return 'https://via.placeholder.com/400'

def get_products():
    return load_products()

@app.route('/')
def home():
    products = get_products()
    return render_template('index.html', products=products)

@app.route('/products')
def products():
    products_list = get_products()
    category = request.args.get('category', '')
    if category:
        filtered_products = [p for p in products_list if p['category'].lower() == category.lower()]
    else:
        filtered_products = products_list
    return render_template('products.html', products=filtered_products, all_products=products_list)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    products_list = get_products()
    product = next((p for p in products_list if p['id'] == product_id), None)
    if not product:
        return redirect(url_for('home'))
    return render_template('product_detail.html', product=product)

@app.route('/cart')
def cart():
    products_list = get_products()
    cart_items = session.get('cart', [])
    cart_products = []
    total = 0
    for item in cart_items:
        product = next((p for p in products_list if p['id'] == item['id']), None)
        if product:
            product['quantity'] = item['quantity']
            price = product.get('discount_price') or product['price']
            product['display_price'] = price
            product['original_price'] = product['price']
            cart_products.append(product)
            total += price * item['quantity']
    return render_template('cart.html', cart_items=cart_products, total=total)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if 'cart' not in session:
        session['cart'] = []
    
    cart = session['cart']
    existing_item = next((item for item in cart if item['id'] == product_id), None)
    
    if existing_item:
        existing_item['quantity'] += quantity
    else:
        cart.append({'id': product_id, 'quantity': quantity})
    
    session['cart'] = cart
    return jsonify({'success': True, 'cart_count': len(cart)})

@app.route('/update_cart', methods=['POST'])
def update_cart():
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    cart = session.get('cart', [])
    item = next((item for item in cart if item['id'] == product_id), None)
    
    if item:
        if quantity <= 0:
            cart.remove(item)
        else:
            item['quantity'] = quantity
        session['cart'] = cart
    
    return jsonify({'success': True})

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    data = request.json
    product_id = data.get('product_id')
    
    cart = session.get('cart', [])
    cart = [item for item in cart if item['id'] != product_id]
    session['cart'] = cart
    
    return jsonify({'success': True})

@app.route('/checkout')
def checkout():
    products_list = get_products()
    cart_items = session.get('cart', [])
    if not cart_items:
        return redirect(url_for('cart'))
    
    cart_products = []
    total = 0
    for item in cart_items:
        product = next((p for p in products_list if p['id'] == item['id']), None)
        if product:
            product['quantity'] = item['quantity']
            cart_products.append(product)
            price = product.get('discount_price') or product['price']
            total += price * item['quantity']
    
    return render_template('checkout.html', cart_items=cart_products, total=total)

@app.route('/order_placed', methods=['POST'])
def order_placed():
    cart_items = session.get('cart', [])
    if not cart_items:
        return redirect(url_for('cart'))
    
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    whatsapp = request.form.get('whatsapp')
    address = request.form.get('address')
    city = request.form.get('city')
    postal = request.form.get('postal')
    payment_method = request.form.get('payment')
    
    products_list = get_products()
    cart_products = []
    total = 0
    for item in cart_items:
        product = next((p for p in products_list if p['id'] == item['id']), None)
        if product:
            product['quantity'] = item['quantity']
            price = product.get('discount_price') or product['price']
            cart_products.append({
                'id': product['id'],
                'name': product['name'],
                'price': price,
                'original_price': product['price'],
                'discount_price': product.get('discount_price'),
                'quantity': item['quantity'],
                'image': product['image']
            })
            total += price * item['quantity']
    
    orders = load_orders()
    order = {
        'id': len(orders) + 1,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'customer': {
            'name': name,
            'email': email,
            'phone': phone,
            'whatsapp': whatsapp,
            'address': address,
            'city': city,
            'postal': postal
        },
        'items': cart_products,
        'total': total,
        'payment_method': payment_method,
        'status': 'Pending'
    }
    
    orders.append(order)
    save_orders(orders)
    
    session['cart'] = []
    return render_template('order_placed.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    orders = load_orders()
    orders.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template('admin_panel.html', orders=orders)

@app.route('/admin/order/<int:order_id>')
def admin_order_detail(order_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    orders = load_orders()
    order = next((o for o in orders if o['id'] == order_id), None)
    
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('admin_panel'))
    
    return render_template('admin_order_detail.html', order=order)

@app.route('/admin/order/<int:order_id>/update_status', methods=['POST'])
def update_order_status(order_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    new_status = request.form.get('status')
    orders = load_orders()
    
    for order in orders:
        if order['id'] == order_id:
            order['status'] = new_status
            break
    
    save_orders(orders)
    flash('Order status updated successfully', 'success')
    return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/products')
def admin_products():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    products = get_products()
    return render_template('admin_products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
def admin_add_product():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        products = get_products()
        
        name = request.form.get('name')
        price = float(request.form.get('price', 0))
        discount_price = request.form.get('discount_price', '').strip()
        discount_price = float(discount_price) if discount_price else None
        description = request.form.get('description')
        category = request.form.get('category')
        image_url = request.form.get('image_url', '').strip()
        
        if image_url:
            if image_url.startswith('data:image'):
                image_url = upload_image_to_url(image_url)
        else:
            image_url = ''
        
        new_id = max([p['id'] for p in products], default=0) + 1
        new_product = {
            'id': new_id,
            'name': name,
            'price': price,
            'discount_price': discount_price,
            'image': image_url,
            'description': description,
            'category': category
        }
        
        products.append(new_product)
        save_products(products)
        flash('Product added successfully', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin_product_form.html', product=None)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    products = get_products()
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('admin_products'))
    
    if request.method == 'POST':
        product['name'] = request.form.get('name')
        product['price'] = float(request.form.get('price', 0))
        discount_price = request.form.get('discount_price', '').strip()
        product['discount_price'] = float(discount_price) if discount_price else None
        product['description'] = request.form.get('description')
        product['category'] = request.form.get('category')
        
        image_url = request.form.get('image_url', '').strip()
        if image_url:
            if image_url.startswith('data:image'):
                product['image'] = upload_image_to_url(image_url)
            elif image_url.startswith('http://') or image_url.startswith('https://'):
                product['image'] = image_url
        
        save_products(products)
        flash('Product updated successfully', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin_product_form.html', product=product)

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
def admin_delete_product(product_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    products = get_products()
    products = [p for p in products if p['id'] != product_id]
    save_products(products)
    flash('Product deleted successfully', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/upload_image', methods=['POST'])
def admin_upload_image():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        image_data = request.json.get('image')
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        image_url = upload_image_to_url(image_data)
        
        if image_url and (image_url.startswith('http') or image_url.startswith('data:image')):
            return jsonify({'url': image_url, 'success': True})
        else:
            return jsonify({'error': 'Failed to upload image. Please try using a direct image URL or get an API key from https://api.imgbb.com/'}), 500
    except Exception as e:
        print(f"Upload endpoint error: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)

