import sqlite3

db_path = 'instance/products.db'  # Đảm bảo đúng đường dẫn

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Kiểm tra xem đã có cột 'unit_price' chưa
cursor.execute("PRAGMA table_info(order_details)")
columns = [col[1] for col in cursor.fetchall()]

if 'unit_price' not in columns:
    cursor.execute("ALTER TABLE order_details ADD COLUMN unit_price REAL")
    print("✅ Đã thêm cột unit_price vào bảng order_details.")
else:
    print("✅ Cột unit_price đã tồn tại.")

conn.commit()
conn.close()
