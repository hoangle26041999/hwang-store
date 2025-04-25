import sqlite3
import os

# Tạo lại đường dẫn sau khi reset kernel
db_path = "/hwang1/instance/products.db"

# Kết nối đến SQLite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()





# Tạo lại bảng order_details
cursor.execute("""
UPDATE product_media SET media_type = 'main' WHERE media_type = 'image';


""")

# Lưu và đóng kết nối
conn.commit()
conn.close()
f"✅ Đã tạo lại file database: {db_path}"
