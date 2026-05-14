from .db import get_db_connection
import sqlite3

class Report:
    """Report 資料表的 Model 操作"""

    @staticmethod
    def create(location_id, tag, user_session):
        """
        新增一筆體感回報紀錄。
        參數:
            location_id (int): 對應的 location_id
            tag (str): 體感標籤 (超冷、悶熱等)
            user_session (str): 用於防刷的識別碼
        回傳: 新增的資料 ID (int) 或 None
        """
        try:
            conn = get_db_connection()
            cursor = conn.execute(
                'INSERT INTO reports (location_id, tag, user_session) VALUES (?, ?, ?)',
                (location_id, tag, user_session)
            )
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            return new_id
        except sqlite3.Error as e:
            print(f"Report.create 發生錯誤: {e}")
            return None

    @staticmethod
    def get_all():
        """
        取得所有的回報資料 (依時間新到舊排序)。
        回傳: list of dict
        """
        try:
            conn = get_db_connection()
            reports = conn.execute('SELECT * FROM reports ORDER BY created_at DESC').fetchall()
            conn.close()
            return [dict(r) for r in reports]
        except sqlite3.Error as e:
            print(f"Report.get_all 發生錯誤: {e}")
            return []

    @staticmethod
    def get_by_id(report_id):
        """
        根據 ID 取得單筆回報資料。
        參數: report_id (int)
        回傳: dict 或 None
        """
        try:
            conn = get_db_connection()
            report = conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone()
            conn.close()
            return dict(report) if report else None
        except sqlite3.Error as e:
            print(f"Report.get_by_id 發生錯誤: {e}")
            return None

    @staticmethod
    def delete(report_id):
        """
        刪除指定的單筆回報資料。
        參數: report_id (int)
        回傳: boolean 表示是否成功
        """
        try:
            conn = get_db_connection()
            conn.execute('DELETE FROM reports WHERE id = ?', (report_id,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Report.delete 發生錯誤: {e}")
            return False

    @staticmethod
    def get_recent_by_location(location_id, limit=50):
        """
        取得指定地點近期的回報資料。
        參數: 
            location_id (int)
            limit (int): 限制筆數，預設 50
        回傳: list of dict
        """
        try:
            conn = get_db_connection()
            reports = conn.execute(
                'SELECT * FROM reports WHERE location_id = ? ORDER BY created_at DESC LIMIT ?',
                (location_id, limit)
            ).fetchall()
            conn.close()
            return [dict(r) for r in reports]
        except sqlite3.Error as e:
            print(f"Report.get_recent_by_location 發生錯誤: {e}")
            return []
        
    @staticmethod
    def check_recent_user_report(location_id, user_session, minutes=5):
        """
        檢查同一個 user_session 是否在指定分鐘內對同一個地點回報過。
        參數:
            location_id (int)
            user_session (str)
            minutes (int): 防刷時間限制，預設 5 分鐘
        回傳: boolean (True 表示有回報過，不可再刷)
        """
        try:
            conn = get_db_connection()
            time_modifier = f"-{minutes} minutes"
            count = conn.execute(
                '''SELECT COUNT(*) FROM reports 
                   WHERE location_id = ? AND user_session = ? 
                   AND created_at >= datetime("now", ?)''',
                (location_id, user_session, time_modifier)
            ).fetchone()[0]
            conn.close()
            return count > 0
        except sqlite3.Error as e:
            print(f"Report.check_recent_user_report 發生錯誤: {e}")
            return False
