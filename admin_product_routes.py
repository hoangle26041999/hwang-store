
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
