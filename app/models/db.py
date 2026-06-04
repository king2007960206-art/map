import sqlite3
import os

# 設定資料庫檔案路徑 (對應到 instance/database.db)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
DB_PATH = os.path.join(INSTANCE_DIR, 'database.db')

def get_db():
    """
    取得資料庫連線。
    回傳連線物件，並設定 row_factory 使查詢結果可以像字典一樣操作。
    """
    # 確保 instance 資料夾存在
    if not os.path.exists(INSTANCE_DIR):
        os.makedirs(INSTANCE_DIR)
        
    is_new = not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 讓回傳的 row 可以用欄位名稱存取
    
    # 開啟 SQLite 的 Foreign Key 支援
    conn.execute('PRAGMA foreign_keys = ON')
    
    # 如果資料庫是新建立的，自動執行 schema.sql 建立資料表
    if is_new:
        schema_path = os.path.join(BASE_DIR, 'database', 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            conn.commit()
    
    return conn

def get_db_connection():
    """相容性別名：回傳與 get_db 相同的連線"""
    return get_db()

def init_db():
    """
    手動初始化資料庫，執行 schema.sql 建立或重置資料表
    """
    schema_path = os.path.join(BASE_DIR, 'database', 'schema.sql')
    if os.path.exists(schema_path):
        conn = get_db()
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

