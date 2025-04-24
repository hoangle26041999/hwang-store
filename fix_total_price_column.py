import sqlite3

db_path = 'instance/products.db'  # Đảm bảo đúng đường dẫn của anh

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Kiểm tra xem đã có cột 'total_price' chưa
cursor.execute("PRAGMA table_info(orders)")
columns = [col[1] for col in cursor.fetchall()]

if 'total_price' not in columns:
    cursor.execute("ALTER TABLE orders ADD COLUMN total_price REAL")
    print("✅ Đã thêm cột total_price vào bảng orders.")
else:
    print("✅ Cột total_price đã tồn tại.")

conn.commit()
conn.close()
