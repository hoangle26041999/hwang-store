from flask import Flask, render_template, request, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime

app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.secret_key = 'hwang-store-key'
app.config['UPLOAD_FOLDER'] = os.path.join('app', 'static', 'images')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

    products = conn.execute('''
                            SELECT p.*,
                                   (SELECT media_url
                                    FROM product_media
                                    WHERE product_id = p.id
                                      AND sort_order = 0
                                      AND media_type = 'image'
                                       LIMIT 1 ) AS image_url
                            FROM products p
                            ORDER BY p.id DESC
                                LIMIT ?
                            OFFSET ?
                            ''', (per_page, offset)).fetchall()
    banners = conn.execute('SELECT * FROM banners ORDER BY id DESC').fetchall()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    best_sellers = conn.execute('''
                                SELECT p.*,
                                       (SELECT media_url
                                        FROM product_media
                                        WHERE product_id = p.id
                                          AND sort_order = 0 LIMIT 1 ) AS image_url,
        SUM(od.quantity) AS total_sold
                                FROM order_details od
                                    JOIN products p
                                ON p.id = od.product_id
                                GROUP BY od.product_id
                                ORDER BY total_sold DESC
                                    LIMIT 2
                                ''').fetchall()

    conn.close()

    total_pages = (total_products + per_page - 1) // per_page

    return render_template(
        'index.html',
        products=products,
        categories=categories,
        banners=banners,
        page=page,
        best_sellers =best_sellers,
        total_pages=total_pages
    )

@app.route('/category/<int:category_id>')
def category_products(category_id):
    page = request.args.get('page', default=1, type=int)
    per_page = 6
    offset = (page - 1) * per_page

    conn = get_db_connection()
    category = conn.execute('SELECT * FROM categories WHERE id = ?', (category_id,)).fetchone()

    total_products = conn.execute('SELECT COUNT(*) FROM products WHERE category_id = ?', (category_id,)).fetchone()[0]

    products = conn.execute('''
        SELECT p.*, (
            SELECT media_url FROM product_media
            WHERE product_id = p.id AND sort_order = 0
            LIMIT 1
        ) AS image_url
        FROM products p
        WHERE p.category_id = ?
        ORDER BY p.id DESC
        LIMIT ? OFFSET ?
    ''', (category_id, per_page, offset)).fetchall()
    best_sellers = conn.execute('''
                                SELECT p.*,
                                       (SELECT media_url
                                        FROM product_media
                                        WHERE product_id = p.id
                                          AND sort_order = 0 LIMIT 1 ) AS image_url,
        SUM(od.quantity) AS total_sold
                                FROM order_details od
                                    JOIN products p
                                ON p.id = od.product_id
                                GROUP BY od.product_id
                                ORDER BY total_sold DESC
                                    LIMIT 3
                                ''').fetchall()

    categories = conn.execute('SELECT * FROM categories').fetchall()
    banners = conn.execute('SELECT * FROM banners').fetchall()
    conn.close()

    total_pages = (total_products + per_page - 1) // per_page

    return render_template('index.html',
                           products=products,
                           categories=categories,
                           banners=banners,
                           page=page,
                           total_pages=total_pages,
                           current_category=category,
                           best_sellers=best_sellers
                           )


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()

    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    media = conn.execute('SELECT * FROM product_media WHERE product_id = ? ORDER BY sort_order', (product_id,)).fetchall()

    # ✅ Lấy danh sách best seller
    best_sellers = conn.execute('''
        SELECT p.*, (
            SELECT media_url FROM product_media
            WHERE product_id = p.id AND sort_order = 0
            LIMIT 1
        ) AS image_url,
        SUM(od.quantity) AS total_sold
        FROM order_details od
        JOIN products p ON p.id = od.product_id
        GROUP BY od.product_id
        ORDER BY total_sold DESC
        LIMIT 3
    ''').fetchall()

    conn.close()

    if not product:
        return "Sản phẩm không tồn tại", 404

    return render_template('product_detail.html', product=product, media=media, best_sellers=best_sellers)


@app.route('/test-image')
def test_image():
    return '''
    <html>
      <body>
        <h3>🖼️ Test ảnh trực tiếp</h3>
        <img src="/static/images/1.jpg" style="max-width: 300px;">
      </body>
    </html>
    '''


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
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template("cart.html", cart_items=cart_items, total_price=total_price)


@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    redirect_to = request.form.get('redirect')
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    session['cart'] = cart

    # Nếu gọi từ fetch(), không cần chuyển hướng
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return '', 204

    if redirect_to == 'checkout':
        return redirect(url_for('cart'))
    return redirect(url_for('product_detail', product_id=product_id))




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
def update_cart_quantity(product_id):
    quantity = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    if quantity > 0:
        cart[str(product_id)] = quantity
    else:
        cart.pop(str(product_id), None)
    session['cart'] = cart
    return '', 204 if request.headers.get("X-Requested-With") == "XMLHttpRequest" else redirect(url_for('cart'))




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

    try:
        total_price = 0
        items = []

        for product_id, quantity in cart.items():
            product = cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
            if not product:
                continue
            price = product['price']
            total_price += price * quantity
            items.append({
                'id': product['id'],
                'price': price,
                'quantity': quantity
            })

        if not items:
            return redirect(url_for('cart'))

        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO orders (customer_name, phone, address, note, total_price, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (customer_name, phone, address, note, total_price, created_at))

        order_id = cursor.lastrowid

        for item in items:
            cursor.execute('''
                INSERT INTO order_details (order_id, product_id, quantity, price_at_time)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['id'], item['quantity'], item['price']))

        conn.commit()
        session.pop('cart', None)
        return render_template('thank_you.html', order_id=order_id)

    except Exception as e:
        conn.rollback()
        print("❌ Lỗi lưu đơn hàng:", e)
        return "Có lỗi khi đặt hàng. Vui lòng thử lại sau.", 500

    finally:
        conn.close()




#banner
def get_banners():
    conn = get_db_connection()
    banners = conn.execute('SELECT * FROM banners').fetchall()
    conn.close()
    return banners

@app.template_filter('currency')
def currency_format(value):
    try:
        return "{:,.0f}".format(value).replace(",", ".")
    except:
        return value

@app.route('/checkout-page')
def checkout_page():
    return render_template('checkout.html')















































#admin
from functools import wraps

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or session.get('role') != required_role:
                return redirect(url_for('admin_login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

admin_required = role_required('admin')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and password == user['password']:
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['username'] = user['username']

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return "Bạn không có quyền truy cập", 403
        else:
            return render_template('admin_login.html', error="Sai tài khoản hoặc mật khẩu")

    return render_template('admin_login.html')


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    total_products = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    total_orders = conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
    #total_feedbacks = conn.execute('SELECT COUNT(*) FROM feedbacks').fetchone()[0]

    today = datetime.now().strftime('%Y-%m-%d')
    today_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = ?", (today,)).fetchone()[0]

    recent_orders = conn.execute('SELECT * FROM orders ORDER BY created_at DESC LIMIT 5').fetchall()
    total_categories = conn.execute('SELECT COUNT(*) FROM categories').fetchone()[0]
    total_banners = conn.execute('SELECT COUNT(*) FROM banners').fetchone()[0]
    conn.close()

    return render_template('admin_dashboard.html',
                           total_products=total_products,
                           total_orders=total_orders,
                           #total_feedbacks=total_feedbacks,
                           total_categories=total_categories,
                           today_orders=today_orders,
                           total_banners=total_banners,
                           recent_orders=recent_orders)
@app.route('/admin/logout')
def admin_logout():
    session.clear()  # hoặc session.pop('user_id')...
    return redirect(url_for('admin_login'))

@app.route('/admin/orders/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    details = conn.execute('''
        SELECT od.*, p.name FROM order_details od
        JOIN products p ON od.product_id = p.id
        WHERE od.order_id = ?
    ''', (order_id,)).fetchall()
    conn.close()
    return render_template('admin_order_detail.html', order=order, details=details)

@app.template_filter('currency')
def currency_format(value):
    try:
        return "{:,.0f}".format(float(value)).replace(",", ".")
    except:
        return value

@app.route('/admin/orders')
@admin_required
def admin_orders():
    conn = get_db_connection()
    orders = conn.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin_orders.html', orders=orders)


@app.route('/admin/products')
@admin_required
def admin_products():
    conn = get_db_connection()

    # ✅ Lấy danh sách sản phẩm kèm ảnh từ bảng product_media
    products = conn.execute('''
        SELECT p.*, (
            SELECT media_url
            FROM product_media
            WHERE product_id = p.id AND sort_order = 0
            LIMIT 1
        ) AS image_url
        FROM products p
        ORDER BY p.id DESC
    ''').fetchall()

    categories = conn.execute('SELECT * FROM categories').fetchall()
    conn.close()

    return render_template('admin_products.html', products=products, categories=categories)


@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_products'))

# ✅ Cấu hình đầu file run.py
app.config['UPLOAD_FOLDER'] = os.path.join('app', 'static', 'images')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ✅ Thêm sản phẩm với ảnh chính + ảnh phụ
@app.route('/admin/products/add', methods=['POST'])
@admin_required
def admin_add_product():
    name = request.form['name']
    price = request.form['price']
    sale_price = request.form.get('sale_price') or None
    description = request.form['description']
    category_id = request.form['category_id']

    # Ảnh chính
    image = request.files['image']
    filename = None
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO products (name, price, sale_price, description, category_id, image_url) VALUES (?, ?, ?, ?, ?, ?)',
        (name, price, sale_price, description, category_id, filename)
    )
    product_id = cursor.lastrowid

    # ✅ Thêm ảnh vào product_media (ảnh chính)
    if filename:
        cursor.execute(
            'INSERT INTO product_media (product_id, media_url, sort_order, media_type) VALUES (?, ?, 0, "image")',
            (product_id, filename)
        )

    # ✅ Ảnh phụ (dạng multiple input)
    for i, extra in enumerate(request.files.getlist('extra_images')):
        if extra and allowed_file(extra.filename):
            extra_filename = secure_filename(extra.filename)
            extra.save(os.path.join(app.config['UPLOAD_FOLDER'], extra_filename))
            cursor.execute(
                'INSERT INTO product_media (product_id, media_url, sort_order, media_type) VALUES (?, ?, ?, "image")',
                (product_id, extra_filename, i + 1)
            )

    conn.commit()
    conn.close()
    return '', 204


# ✅ Sửa sản phẩm + xóa ảnh phụ cũ, thay ảnh mới
@app.route('/admin/products/edit/<int:product_id>', methods=['POST'])
@admin_required
def admin_edit_product(product_id):
    name = request.form['name']
    price = request.form['price']
    sale_price = request.form.get('sale_price') or None
    description = request.form['description']
    category_id = request.form['category_id']

    image = request.files['image']
    conn = get_db_connection()
    cursor = conn.cursor()

    current = cursor.execute('SELECT image_url FROM products WHERE id = ?', (product_id,)).fetchone()
    filename = current['image_url']

    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Xóa ảnh chính cũ khỏi product_media
        cursor.execute('DELETE FROM product_media WHERE product_id = ? AND sort_order = 0', (product_id,))
        cursor.execute(
            'INSERT INTO product_media (product_id, media_url, sort_order, media_type) VALUES (?, ?, 0, "image")',
            (product_id, filename)
        )

    # Cập nhật sản phẩm
    cursor.execute(
        'UPDATE products SET name=?, price=?, sale_price=?, description=?, category_id=?, image_url=? WHERE id=?',
        (name, price, sale_price, description, category_id, filename, product_id)
    )

    # Xóa ảnh phụ cũ
    cursor.execute('DELETE FROM product_media WHERE product_id = ? AND sort_order > 0', (product_id,))

    # Thêm ảnh phụ mới
    for i, extra in enumerate(request.files.getlist('extra_images')):
        if extra and allowed_file(extra.filename):
            extra_filename = secure_filename(extra.filename)
            extra.save(os.path.join(app.config['UPLOAD_FOLDER'], extra_filename))
            cursor.execute(
                'INSERT INTO product_media (product_id, media_url, sort_order, media_type) VALUES (?, ?, ?, "image")',
                (product_id, extra_filename, i + 1)
            )

    conn.commit()
    conn.close()
    return '', 204
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#catagory
@app.route('/admin/categories')
@admin_required
def admin_categories():
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin_categories.html', categories=categories)

@app.route('/admin/categories/add', methods=['POST'])
@admin_required
def admin_add_category():
    name = request.form['name']
    conn = get_db_connection()
    conn.execute('INSERT INTO categories (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def admin_delete_category(category_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_categories'))


#banner
@app.route('/admin/banners/add', methods=['POST'])
@admin_required
def admin_add_banner():
    image = request.files['image']
    title = request.form.get('title')
    description = request.form.get('description')

    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = get_db_connection()
        conn.execute('INSERT INTO banners (image_url, title, description) VALUES (?, ?, ?)',
                     (filename, title, description))
        conn.commit()
        conn.close()
    return redirect(url_for('admin_banners'))

@app.route('/admin/banners')
@admin_required
def admin_banners():
    conn = get_db_connection()
    banners = conn.execute('SELECT * FROM banners ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin_banners.html', banners=banners)

@app.route('/admin/banners/delete/<int:banner_id>', methods=['POST'])
@admin_required
def admin_delete_banner(banner_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM banners WHERE id = ?', (banner_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_banners'))