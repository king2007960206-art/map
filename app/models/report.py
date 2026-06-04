from .db import get_db_connection
import sqlite3

class Report:
    """Report 資料表的 Model 操作，處理使用者即時回報"""

    @staticmethod
    def create(location_id, crowd_level, temperature_felt, user_ip, user_session):
        """
        新增一筆體感回報紀錄。
        """
        try:
            conn = get_db_connection()
            cursor = conn.execute(
                '''INSERT INTO reports (location_id, crowd_level, temperature_felt, user_ip, user_session)
                   VALUES (?, ?, ?, ?, ?)''',
                (location_id, crowd_level, temperature_felt, user_ip, user_session)
            )
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            return new_id
        except sqlite3.Error as e:
            print(f"Report.create 發生錯誤: {e}")
            return None

    @staticmethod
    def get_recent_by_location(location_id, limit=30):
        """
        取得特定地點最近的回報資料。
        """
        try:
            conn = get_db_connection()
            reports = conn.execute(
                '''SELECT * FROM reports 
                   WHERE location_id = ? 
                   ORDER BY created_at DESC LIMIT ?''',
                (location_id, limit)
            ).fetchall()
            conn.close()
            return [dict(r) for r in reports]
        except sqlite3.Error as e:
            print(f"Report.get_recent_by_location 發生錯誤: {e}")
            return []

    @staticmethod
    def check_recent_user_report(location_id, user_session, minutes=2):
        """
        檢查同一個 session 是否在近期內對同一地點重複回報（防刷機制）。
        """
        try:
            conn = get_db_connection()
            time_modifier = f"-{minutes} minutes"
            count = conn.execute(
                '''SELECT COUNT(*) FROM reports 
                   WHERE location_id = ? AND user_session = ? 
                   AND created_at >= datetime("now", "localtime", ?)''',
                (location_id, user_session, time_modifier)
            ).fetchone()[0]
            conn.close()
            return count > 0
        except sqlite3.Error as e:
            print(f"Report.check_recent_user_report 發生錯誤: {e}")
            return False

    @staticmethod
    def get_latest_aggregated_status(location_id, minutes=30):
        """
        取得最近 X 分鐘內，該地點的群眾回報平均/統計值，用以動態修正當前人潮與溫度。
        """
        try:
            conn = get_db_connection()
            time_modifier = f"-{minutes} minutes"
            rows = conn.execute(
                '''SELECT crowd_level, temperature_felt FROM reports 
                   WHERE location_id = ? 
                   AND created_at >= datetime("now", "localtime", ?)''',
                (location_id, time_modifier)
            ).fetchall()
            conn.close()

            if not rows:
                return None

            # 統計眾數或加權值
            crowds = [r['crowd_level'] for r in rows if r['crowd_level']]
            temps = [r['temperature_felt'] for r in rows if r['temperature_felt']]

            def get_mode(lst):
                if not lst: return None
                return max(set(lst), key=lst.count)

            return {
                "crowd_level": get_mode(crowds),
                "temperature_felt": get_mode(temps),
                "count": len(rows)
            }
        except sqlite3.Error as e:
            print(f"Report.get_latest_aggregated_status 發生錯誤: {e}")
            return None
