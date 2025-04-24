import sqlite3
import os

# Tạo lại đường dẫn sau khi reset kernel
db_path = "/hwang1/instance/products.db"

# Kết nối đến SQLite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Xoá bảng nếu đã tồn tại
cursor.execute("DROP TABLE IF EXISTS orders;")
cursor.execute("DROP TABLE IF EXISTS order_details;")

# Tạo lại bảng orders
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT,
    phone TEXT,
    address TEXT,
    note TEXT,
    total_price REAL,
    created_at TEXT
)
""")

# Tạo lại bảng order_details
cursor.execute("""
CREATE TABLE IF NOT EXISTS order_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    unit_price REAL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
)
""")



# Tạo lại bảng order_details
cursor.execute("""
CREATE TABLE IF NOT EXISTS banners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_url TEXT NOT NULL,
    title TEXT,
    description TEXT
)
""")

# Lưu và đóng kết nối
conn.commit()
conn.close()
f"✅ Đã tạo lại file database: {db_path}"
