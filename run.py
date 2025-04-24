from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.secret_key = 'hwang-store-key'

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'products.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    page = request.args.get('page', default=1, type=int)
    per_page = 6
    offset = (page - 1) * per_page

    conn = get_db_connection()
    total_products = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    products = conn.execute('SELECT * FROM products LIMIT ? OFFSET ?', (per_page, offset)).fetchall()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    banners = conn.execute('SELECT * FROM banners').fetchall()
    conn.close()

    total_pages = (total_products + per_page - 1) // per_page  # làm tròn lên
    return render_template(
        'index.html',
        products=products,
        categories=categories,
        banners=banners,
        page=page,
        total_pages=total_pages
    )

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()

    # Lấy toàn bộ media liên quan đến sản phẩm
    media = conn.execute(
        'SELECT * FROM product_media WHERE product_id = ? ORDER BY sort_order',
        (product_id,)
    ).fetchall()

    conn.close()

    if not product:
        return "Sản phẩm không tồn tại", 404
    return render_template('product_detail.html', product=product, media=media)




@app.route('/cart')
def cart():
    cart = session.get('cart', {})

    if not cart:
        return render_template('cart.html', cart_items=[])

    conn = get_db_connection()
    cart_items = []

    for product_id, quantity in cart.items():
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if product:
            cart_items.append({
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'image_url': product['image_url'],
                'quantity': quantity
            })

    conn.close()
    return render_template('cart.html', cart_items=cart_items)

@app.route('/add-to-cart/<int:product_id>')
def add_to_cart(product_id):
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    return redirect(url_for('cart'))  # ➤ chuyển luôn sang giỏ hàng



@app.route('/remove-from-cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/order-cart', methods=['POST'])
def order_cart():
    name = request.form['name']
    phone = request.form['phone']
    address = request.form['address']
    note = request.form.get('note', '')
    cart = session.get('cart', {})

    print("======= ĐƠN HÀNG GIỎ HÀNG TOÀN BỘ =======")
    print(f"Họ tên: {name}")
    print(f"SĐT: {phone}")
    print(f"Địa chỉ: {address}")
    print(f"Ghi chú: {note}")
    print("Sản phẩm trong đơn:")

    conn = get_db_connection()
    for product_id, qty in cart.items():
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if product:
            print(f"- {product['name']} (x{qty})")
    conn.close()

    print("=========================================")

    # Xoá giỏ hàng sau khi đặt
    session['cart'] = {}
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)

# Sửa lỗi thụt lề và ghi lại nội dung chuẩn vào file checkout_route_snippet.txt



@app.route('/update-cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    new_qty = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    if new_qty <= 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = new_qty
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/delete-cart-item/<int:product_id>', methods=['POST'])
def delete_cart_item(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return redirect(url_for('cart'))

from datetime import datetime
import sqlite3

@app.route('/checkout', methods=['POST'])
def checkout():
    customer_name = request.form['customer_name']
    phone = request.form['phone']
    address = request.form['address']
    note = request.form.get('note', '')

    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('cart'))

    conn = sqlite3.connect('instance/products.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Tính tổng tiền
    total_price = 0
    items = []
    for product_id, quantity in cart.items():
        product = cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if product:
            price = product['price']
            line_total = price * quantity
            total_price += line_total
            items.append({
                'id': product['id'],
                'price': price,
                'quantity': quantity
            })

    # Lưu đơn hàng
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO orders (customer_name, phone, address, note, total_price, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (customer_name, phone, address, note, total_price, created_at))
    order_id = cursor.lastrowid

    # Lưu chi tiết đơn hàng
    for item in items:
        cursor.execute('''
            INSERT INTO order_details (order_id, product_id, quantity, price_at_time)
            VALUES (?, ?, ?, ?)
        ''', (order_id, item['id'], item['quantity'], item['price']))

    conn.commit()
    conn.close()

    # Xoá giỏ hàng
    session.pop('cart', None)

    return render_template('thank_you.html')



#banner
def get_banners():
    conn = get_db_connection()
    banners = conn.execute('SELECT * FROM banners').fetchall()
    conn.close()
    return banners















































#admin


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == '1234':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Sai tài khoản hoặc mật khẩu")
    return render_template('admin_login.html')


@app.route('/admin/products')
def admin_products():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('admin_products.html', products=products)

@app.route('/admin/categories')
def admin_categories():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    conn.close()
    return render_template('admin_categories.html', categories=categories)


# 📦 Orders
@app.route('/admin/orders')
def admin_orders():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    orders = conn.execute('SELECT * FROM orders').fetchall()
    conn.close()
    return render_template('admin_orders.html', orders=orders)

# 💬 Feedbacks
@app.route('/admin/feedbacks')
def admin_feedbacks():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    feedbacks = conn.execute('SELECT * FROM feedbacks').fetchall()
    conn.close()
    return render_template('admin_feedbacks.html', feedbacks=feedbacks)


# Thêm trong route admin_add_product
@app.route('/admin/products/add', methods=['GET', 'POST'])
def admin_add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        sale_price = request.form.get('sale_price') or None
        description = request.form['description']
        category_id = request.form['category_id']

        # Ảnh
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None

        conn = get_db_connection()
        conn.execute('INSERT INTO products (name, price, sale_price, description, category_id, image_url) VALUES (?, ?, ?, ?, ?, ?)',
                     (name, price, sale_price, description, category_id, filename))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_products'))

    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    conn.close()
    return render_template('admin_add_product.html', categories=categories)

# Sửa sản phẩm



@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        sale_price = request.form.get('sale_price') or None
        description = request.form['description']
        category_id = request.form['category_id']

        # Xử lý ảnh mới nếu có
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = product['image_url']

        conn.execute('UPDATE products SET name = ?, price = ?, sale_price = ?, description = ?, category_id = ?, image_url = ? WHERE id = ?',
                     (name, price, sale_price, description, category_id, filename, product_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_products'))

    categories = conn.execute('SELECT * FROM categories').fetchall()
    conn.close()
    return render_template('admin_edit_product.html', product=product, categories=categories)


