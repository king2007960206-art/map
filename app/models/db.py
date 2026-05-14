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
