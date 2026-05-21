from .db import get_db_connection
import sqlite3

class Location:
    """Location 資料表的 Model 操作"""

    @staticmethod
    def get_all():
        """
        取得所有的地點資料。
        回傳: list of dict
        """
        try:
            conn = get_db_connection()
            locations = conn.execute('SELECT * FROM locations').fetchall()
            conn.close()
            return [dict(loc) for loc in locations]
        except sqlite3.Error as e:
            print(f"Location.get_all 發生錯誤: {e}")
            return []

    @staticmethod
    def get_by_id(location_id):
        """
        根據 ID 取得單筆地點資料。
        參數: location_id (int)
        回傳: dict 或 None
        """
        try:
            conn = get_db_connection()
            location = conn.execute('SELECT * FROM locations WHERE id = ?', (location_id,)).fetchone()
            conn.close()
            return dict(location) if location else None
        except sqlite3.Error as e:
            print(f"Location.get_by_id 發生錯誤: {e}")
            return None

    @staticmethod
    def create(name, latitude=None, longitude=None):
        """
        新增一筆地點資料。
        參數: 
            name (str): 地點名稱
            latitude (float): 緯度 (可選)
            longitude (float): 經度 (可選)
        回傳: 新增的資料 ID (int) 或 None
        """
        try:
            conn = get_db_connection()
            cursor = conn.execute(
                'INSERT INTO locations (name, latitude, longitude) VALUES (?, ?, ?)',
                (name, latitude, longitude)
            )
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            return new_id
        except sqlite3.Error as e:
            print(f"Location.create 發生錯誤: {e}")
            return None
    
    @staticmethod
    def update(location_id, name, latitude=None, longitude=None):
        """
        更新指定的單筆地點資料。
        參數:
            location_id (int): 地點 ID
            name (str): 地點名稱
            latitude (float): 緯度 (可選)
            longitude (float): 經度 (可選)
        回傳: boolean 表示是否成功
        """
        try:
            conn = get_db_connection()
            conn.execute(
                'UPDATE locations SET name = ?, latitude = ?, longitude = ? WHERE id = ?',
                (name, latitude, longitude, location_id)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Location.update 發生錯誤: {e}")
            return False

    @staticmethod
    def delete(location_id):
        """
        刪除指定的單筆地點資料。
        參數: location_id (int)
        回傳: boolean 表示是否成功
        """
        try:
            conn = get_db_connection()
            conn.execute('DELETE FROM locations WHERE id = ?', (location_id,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Location.delete 發生錯誤: {e}")
            return False
