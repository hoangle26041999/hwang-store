import sqlite3
import os

# Đường dẫn tới file DB và file SQL
db_path = 'instance/products.db'  # sửa nếu DB nằm chỗ khác
sql_path = 'add_sale_price_column.sql'  # file SQL để thêm cột sale_price

# Kiểm tra tồn tại
if not os.path.exists(db_path):
    print(f"❌ Không tìm thấy database tại {db_path}")
elif not os.path.exists(sql_path):
    print(f"❌ Không tìm thấy file SQL tại {sql_path}")
else:
    try:
        conn = sqlite3.connect(db_path)
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        conn.executescript(sql_script)
        conn.commit()
        conn.close()
        print("✅ Đã chạy file SQL thành công!")
    except sqlite3.OperationalError as e:
        print(f"⚠️ SQLite lỗi: {e}")


