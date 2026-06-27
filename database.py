import sqlite3
import os
import sys
import shutil
import hashlib

DB_NAME = "made_to_measure.db"

def resource_path(relative_path):

    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_db_path():
    app_data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'MadeToMeasure')
    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)
    target_db_path = os.path.join(app_data_dir, DB_NAME)
    if not os.path.exists(target_db_path):
        if hasattr(sys, '_MEIPASS'):
            bundled_db_path = os.path.join(sys._MEIPASS, DB_NAME)
            if os.path.exists(bundled_db_path):
                shutil.copy(bundled_db_path, target_db_path)
    return target_db_path

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def setup_pricing_table():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS mount_pricing (
                id INTEGER PRIMARY KEY, tier_name TEXT, max_dim_1 REAL, max_dim_2 REAL, base_price REAL, extra_ap_fee REAL)""")
    cursor.execute("SELECT COUNT(*) FROM mount_pricing")
    if cursor.fetchone()[0] == 0:
        initial_data = [('Small', 300, 300, 15.00, 2.00), ('Medium', 600, 600, 20.00, 2.00), ('Large', 1200, 800, 24.00, 2.00)]
        cursor.executemany("INSERT INTO mount_pricing (tier_name, max_dim_1, max_dim_2, base_price, extra_ap_fee) VALUES (?,?,?,?,?)", initial_data)
    conn.commit()

def get_tiered_price(w,h,aps):
    long_side, short_side = max(w,h), min(w,h)
    try:
        with sqlite3.connect(get_db_path()) as conn:
            res = conn.execute("SELECT base_price, extra_ap_fee FROM mount_pricing WHERE max_dim_1 >= ? AND max_dim_2 >= ? ORDER BY max_dim_1 ASC LIMIT 1", (long_side, short_side)).fetchone()
        if res:
            return res[0][0] + (aps * res[0][1])
    except: pass
    return 20.00

def sync_database():
    app_data = os.path.join( os.environ['LOCALAPPDATA'], 'MadeToMeasure')
    if not os.path.exists(app_data):
        os.makedirs(app_data)

    db_path = os.path.join(app_data, DB_NAME)

    if not os.path.exists(db_path):
        if os.path.exists(DB_NAME):
            shutil.copy(DB_NAME, db_path)
        else:
            shutil.copy(resource_path(DB_NAME), db_path)
    else:
        backup_before_update()

def backup_before_update():
    db_path = get_db_path()
    backup_path = db_path + ".bak"
    shutil.copy(db_path, backup_path)

def run_migrations():
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN privilege_level INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN mount_data TEXT")
        except sqlite3.OperationalError:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                action_performed TEXT,
                change_details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

def log_action(user, action, details):
    try:
        with sqlite3.connect(get_db_path()) as conn:
            conn.execute("INSERT INTO audit_logs (user_name, action_performed, change_details) VALUES (?, ?, ?)", (user, action, details))
            conn.commit()
    except Exception as e:
        print(f"Error logging action: {e}")


