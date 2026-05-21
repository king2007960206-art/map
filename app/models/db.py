import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'instance', 'database.db')

def get_db_connection():
    """
    建立並回傳 SQLite 資料庫連線。
    將 row_factory 設為 sqlite3.Row，讓查詢結果可以用欄位名稱取值。
    """
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"資料庫連線失敗: {e}")
        raise

def init_db():
    """
    初始化資料庫。
    讀取 schema.sql 並且執行建表語法。
    """
    try:
        schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            conn = get_db_connection()
            conn.executescript(schema_sql)
            conn.commit()
            conn.close()
            print("資料庫初始化成功。")
        else:
            print(f"找不到建表檔案: {schema_path}")
    except sqlite3.Error as e:
        print(f"資料庫初始化發生錯誤: {e}")
        raise
# 設定資料庫檔案路徑 (對應到 instance/database.db)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
DB_PATH = os.path.join(INSTANCE_DIR, 'database.db')

def get_db():
    """
    取得資料庫連線
    回傳連線物件，並設定 row_factory 使查詢結果可以像字典一樣操作
    """
    # 確保 instance 資料夾存在
    if not os.path.exists(INSTANCE_DIR):
        os.makedirs(INSTANCE_DIR)
        
    is_new = not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 讓回傳的 row 可以用欄位名稱存取 (例如 row['id'])
    
    # 開啟 SQLite 的 Foreign Key 支援
    conn.execute('PRAGMA foreign_keys = ON')
    
    # 如果資料庫是新建立的（或被清空），自動執行 schema.sql 建立資料表
    if is_new:
        schema_path = os.path.join(BASE_DIR, 'database', 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            conn.commit()
    
    return conn

def init_db():
    """
    初始化資料庫，執行 schema.sql 建立資料表
    """
    schema_path = os.path.join(BASE_DIR, 'database', 'schema.sql')
    if os.path.exists(schema_path):
        conn = get_db()
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
