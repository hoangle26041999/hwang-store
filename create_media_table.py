import sqlite3

# Kết nối đến file database
conn = sqlite3.connect('instance/products.db')  # Đảm bảo đúng đường dẫn tới DB của anh

# Tạo cursor để thực thi lệnh SQL
cursor = conn.cursor()

# Lệnh tạo bảng product_media
cursor.execute("""
CREATE TABLE IF NOT EXISTS product_media (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER NOT NULL,
  media_type TEXT CHECK(media_type IN ('image', 'video')) NOT NULL,
  media_url TEXT NOT NULL,
  sort_order INTEGER DEFAULT 0,
  FOREIGN KEY (product_id) REFERENCES products(id)
)
""")

# Lưu thay đổi và đóng kết nối
conn.commit()
conn.close()

print("✅ Đã tạo bảng product_media thành công!")


conn = sqlite3.connect('instance/products.db')
cursor = conn.cursor()

# Lấy toàn bộ sản phẩm
products = cursor.execute('SELECT id FROM products').fetchall()

# Ảnh mockup
mock_images = ['mock1.jpg', 'mock2.jpg', 'mock3.jpg']

for product in products:
    product_id = product[0]
    for i, img in enumerate(mock_images):
        cursor.execute('''
            INSERT INTO product_media (product_id, media_type, media_url, sort_order)
            VALUES (?, 'image', ?, ?)
        ''', (product_id, img, i))

conn.commit()
conn.close()


print("✅ Đã thêm mockup media cho tất cả sản phẩm!")







# Bước 1: Mở file SQL
with open("path/to/create_order_tables.sql", "r", encoding="utf-8") as f:
    sql_script = f.read()

# Bước 2: Kết nối tới database
conn = sqlite3.connect("instance/products.db")
cursor = conn.cursor()

# Bước 3: Chạy script
cursor.executescript(sql_script)

# Bước 4: Hoàn tất và đóng kết nối
conn.commit()
conn.close()
print("✅ Đã thêm mockup media cho tất cả sản phẩm!")

with open("mnt/data/create_order_tables.sql", "r", encoding="utf-8") as f:
    sql_script = f.read()

    import sqlite3

    with open("mnt/data/create_order_tables.sql", "r", encoding="utf-8") as f:
        sql_script = f.read()

    conn = sqlite3.connect("instance/products.db")
    cursor = conn.cursor()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()

    with open("mnt/data/create_order_tables.sql", "r", encoding="utf-8") as f:
        sql_script = f.read()

    conn = sqlite3.connect("instance/products.db")
    cursor = conn.cursor()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()
