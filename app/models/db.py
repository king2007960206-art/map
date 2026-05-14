import sqlite3
import os

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
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 讓回傳的 row 可以用欄位名稱存取 (例如 row['id'])
    
    # 開啟 SQLite 的 Foreign Key 支援
    conn.execute('PRAGMA foreign_keys = ON')
    
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
