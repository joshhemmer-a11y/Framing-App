import sqlite3
import os
import sys
import shutil
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MadeToMeasure")

DB_NAME = "made_to_measure.db"

IS_BUNDLED = hasattr(sys, '_MEIPASS')
BASE_DIR = sys._MEIPASS if IS_BUNDLED else os.path.abspath(".")

APP_DATA_DIR = os.path.join(os.environ.get('LOCALAPPDATA', '.'), 'MadeToMeasure')
os.makedirs(APP_DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(APP_DATA_DIR, DB_NAME)

def resource_path(relative_path):

    return os.path.join(BASE_DIR, relative_path) if IS_BUNDLED else os.path.abspath(relative_path)

def get_db_path():
    
    if not os.path.exists(DB_PATH) and IS_BUNDLED:
        bundled_db_path = os.path.join(BASE_DIR, DB_NAME)
        if os.path.exists(bundled_db_path):
            shutil.copy(bundled_db_path, DB_PATH)
    return DB_PATH

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()



def setup_pricing_table():
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mount_pricing (
                id INTEGER PRIMARY KEY,
                tier_name TEXT,
                max_dim_1 REAL,
                max_dim_2 REAL,
                base_price REAL,
                extra_ap_fee REAL
            )
        """)

        cursor.execute("SELECT 1 FROM mount_pricing LIMIT 1")
        if not cursor.fetchone():
            initial_data = [
                ('Small', 300, 300, 15.00, 2.00),
                ('Medium', 600, 600, 20.00, 2.00),
                ('Large', 1200, 800, 24.00, 2.00)
            ]
            cursor.executemany("""
                INSERT INTO mount_pricing (tier_name, max_dim_1, max_dim_2, base_price, extra_ap_fee)
                VALUES (?, ?, ?, ?, ?)
            """, initial_data)
            conn.commit()

def get_tiered_price(w: float, h: float, aps: int) -> float:
    long_side, short_side = max(w, h), min(w, h)

    query = """
        SELECT base_price, extra_ap_fee
        FROM mount_pricing
        WHERE max_dim_1 >= ? AND max_dim_2 >= ?
        ORDER BY max_dim_1 ASC
        LIMIT 1
    """

    try:
        with sqlite3.connect(get_db_path()) as conn:
            res = conn.execute(query, (long_side, short_side)).fetchone()
        if res:
            return res[0] + ((aps -1) * res[1])
    except Exception as e:
        logger.error(f"Error occurred while fetching tiered pricing: {e}")

    return 20.00

def sync_database():

    if os.path.exists(DB_PATH):
        
        try:
            shutil.copy(DB_PATH, DB_PATH + ".bak")
            logger.info(f"Database backup created at {DB_PATH}.bak")
        except IOError as e:
            logger.error(f"Failed to create database backup: {e}")
        return
    
    logger.info("Database not found. Creating a new database.")

    source = os.path.join(BASE_DIR, DB_NAME) if IS_BUNDLED else os.path.abspath(DB_NAME)

    if os.path.exists(source):
        try:
            shutil.copy(source, DB_PATH)
            logger.info(f"Database copied from {source} to {DB_PATH}")
        except IOError as e:
            logger.error(f"Failed to copy database: {e}")
    else:
        logger.error(f"Database file not found at {source}. Please ensure the database is present.")
        raise FileNotFoundError(f"Database file not found at {source}. Please ensure the database is present.")


def run_migrations():

    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(users)")
        existing_user_cols = {col[1] for col in cursor.fetchall()}
        
        if "privilege_level" not in existing_user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN privilege_level INTEGER DEFAULT 1")
        if "last_login" not in existing_user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        cursor.execute("PRAGMA table_info(orders)")
        existing_order_cols = {col[1] for col in cursor.fetchall()}

        if "mount_data" not in existing_order_cols:
            cursor.execute("ALTER TABLE orders ADD COLUMN mount_data TEXT")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                action_performed TEXT NOT NULL,
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
    except sqlite3.Error as e:
        print(f"Failed to write log action: {e}")


