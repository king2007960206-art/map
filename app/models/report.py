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
                '''INSERT INTO reports (location_id, crowd_level, temperature_felt, user_ip, user_session, is_abnormal)
                   VALUES (?, ?, ?, ?, ?, 0)''',
                (location_id, crowd_level, temperature_felt, user_ip, user_session)
            )
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            
            # 用戶獲得 10 積分
            if new_id and user_session:
                try:
                    from .user import UserProfile
                    UserProfile.add_points(user_session, amount=10, is_report=True)
                except Exception as ex:
                    print(f"增加用戶積分失敗: {ex}")
                    
            return new_id
        except sqlite3.Error as e:
            print(f"Report.create 發生錯誤: {e}")
            return None

    @staticmethod
    def get_recent_by_location(location_id, limit=30):
        """
        取得特定地點最近的正常回報資料（排除已標記為異常的回報）。
        """
        try:
            conn = get_db_connection()
            reports = conn.execute(
                '''SELECT * FROM reports 
                   WHERE location_id = ? AND is_abnormal = 0
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
        檢查同一個 session 是否在近期內對同一地點重複回報（防刷機制，檢查所有回報包括異常的）。
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
        取得最近 X 分鐘內，該地點的群眾回報平均/統計值，已自動過濾標記為異常的數據。
        """
        try:
            conn = get_db_connection()
            time_modifier = f"-{minutes} minutes"
            rows = conn.execute(
                '''SELECT crowd_level, temperature_felt FROM reports 
                   WHERE location_id = ? AND is_abnormal = 0
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

    @staticmethod
    def get_all_recent(limit=50):
        """
        取得最近的全部回報紀錄（包含地點名稱，供管理員審查用）
        """
        try:
            conn = get_db_connection()
            rows = conn.execute(
                '''SELECT r.*, l.name as location_name 
                   FROM reports r
                   JOIN locations l ON r.location_id = l.id
                   ORDER BY r.created_at DESC LIMIT ?''',
                (limit,)
            ).fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Report.get_all_recent 發生錯誤: {e}")
            return []

    @staticmethod
    def mark_as_abnormal(report_id):
        """
        將某一筆回報標記為異常，扣除該用戶 20 積分。
        """
        try:
            conn = get_db_connection()
            row = conn.execute('SELECT user_session, is_abnormal FROM reports WHERE id = ?', (report_id,)).fetchone()
            if not row:
                conn.close()
                return False
                
            if row['is_abnormal'] == 1:
                conn.close()
                return True
                
            conn.execute('UPDATE reports SET is_abnormal = 1 WHERE id = ?', (report_id,))
            conn.commit()
            conn.close()
            
            # 扣除用戶積分
            if row['user_session']:
                try:
                    from .user import UserProfile
                    UserProfile.deduct_points(row['user_session'], amount=20)
                except Exception as ex:
                    print(f"扣除用戶積分失敗: {ex}")
                    
            return True
        except sqlite3.Error as e:
            print(f"Report.mark_as_abnormal 發生錯誤: {e}")
            return False

    @staticmethod
    def mark_as_normal(report_id):
        """
        取消標記某一筆回報的異常狀態，恢復該用戶的 20 積分。
        """
        try:
            conn = get_db_connection()
            row = conn.execute('SELECT user_session, is_abnormal FROM reports WHERE id = ?', (report_id,)).fetchone()
            if not row:
                conn.close()
                return False
                
            if row['is_abnormal'] == 0:
                conn.close()
                return True
                
            conn.execute('UPDATE reports SET is_abnormal = 0 WHERE id = ?', (report_id,))
            conn.commit()
            conn.close()
            
            # 補回用戶積分
            if row['user_session']:
                try:
                    from .user import UserProfile
                    UserProfile.add_points(row['user_session'], amount=20, is_report=False)
                except Exception as ex:
                    print(f"加回用戶積分失敗: {ex}")
                    
            return True
        except sqlite3.Error as e:
            print(f"Report.mark_as_normal 發生錯誤: {e}")
            return False
