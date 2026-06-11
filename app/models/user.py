from .db import get_db_connection
import sqlite3

class UserProfile:
    """UserProfile 資料表的 Model 操作，處理用戶積分與等級"""

    @staticmethod
    def get_or_create(session_id):
        """
        根據 session_id 取得用戶檔案。若不存在則建立一個新的。
        """
        if not session_id:
            return None
            
        try:
            conn = get_db_connection()
            user = conn.execute(
                'SELECT * FROM user_profiles WHERE session_id = ?',
                (session_id,)
            ).fetchone()
            
            if user:
                conn.close()
                return dict(user)
                
            # 不存在，建立一個新的匿名暱稱
            short_id = session_id[-4:] if len(session_id) >= 4 else "0000"
            default_nickname = f"匿名守護者-{short_id}"
            
            conn.execute(
                '''INSERT INTO user_profiles (session_id, nickname, points, level_name, reports_count)
                   VALUES (?, ?, 0, '校園初學者', 0)''',
                (session_id, default_nickname)
            )
            conn.commit()
            
            # 重新取得
            user = conn.execute(
                'SELECT * FROM user_profiles WHERE session_id = ?',
                (session_id,)
            ).fetchone()
            conn.close()
            return dict(user) if user else None
            
        except sqlite3.Error as e:
            print(f"UserProfile.get_or_create 發生錯誤: {e}")
            return None

    @staticmethod
    def update_nickname(session_id, nickname):
        """
        更新用戶暱稱
        """
        if not session_id or not nickname:
            return False
            
        try:
            conn = get_db_connection()
            conn.execute(
                'UPDATE user_profiles SET nickname = ? WHERE session_id = ?',
                (nickname.strip(), session_id)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"UserProfile.update_nickname 發生錯誤: {e}")
            return False

    @staticmethod
    def calculate_level(points):
        """
        根據積分計算等級名稱
        0-49: 校園初學者 (Lv. 1)
        50-149: 校園探索者 (Lv. 2)
        150-299: 空間巡邏員 (Lv. 3)
        300+: 校園守護者 (Lv. 4)
        """
        if points < 50:
            return "校園初學者"
        elif points < 150:
            return "校園探索者"
        elif points < 300:
            return "空間巡邏員"
        else:
            return "校園守護者"

    @staticmethod
    def add_points(session_id, amount=10, is_report=True):
        """
        為用戶增加積分並更新回報次數與稱號
        """
        if not session_id:
            return None
            
        try:
            # 確保用戶存在
            UserProfile.get_or_create(session_id)
            
            conn = get_db_connection()
            user = conn.execute(
                'SELECT points, reports_count FROM user_profiles WHERE session_id = ?',
                (session_id,)
            ).fetchone()
            
            if not user:
                conn.close()
                return None
                
            new_points = user['points'] + amount
            new_reports_count = user['reports_count'] + (1 if is_report else 0)
            new_level = UserProfile.calculate_level(new_points)
            
            conn.execute(
                '''UPDATE user_profiles 
                   SET points = ?, level_name = ?, reports_count = ? 
                   WHERE session_id = ?''',
                (new_points, new_level, new_reports_count, session_id)
            )
            conn.commit()
            
            updated_user = conn.execute(
                'SELECT * FROM user_profiles WHERE session_id = ?',
                (session_id,)
            ).fetchone()
            conn.close()
            return dict(updated_user)
            
        except sqlite3.Error as e:
            print(f"UserProfile.add_points 發生錯誤: {e}")
            return None

    @staticmethod
    def deduct_points(session_id, amount=20):
        """
        扣除用戶積分，並重新計算等級稱號
        """
        if not session_id:
            return None
            
        try:
            conn = get_db_connection()
            user = conn.execute(
                'SELECT points FROM user_profiles WHERE session_id = ?',
                (session_id,)
            ).fetchone()
            
            if not user:
                conn.close()
                return None
                
            new_points = max(0, user['points'] - amount)
            new_level = UserProfile.calculate_level(new_points)
            
            conn.execute(
                '''UPDATE user_profiles 
                   SET points = ?, level_name = ? 
                   WHERE session_id = ?''',
                (new_points, new_level, session_id)
            )
            conn.commit()
            
            updated_user = conn.execute(
                'SELECT * FROM user_profiles WHERE session_id = ?',
                (session_id,)
            ).fetchone()
            conn.close()
            return dict(updated_user)
            
        except sqlite3.Error as e:
            print(f"UserProfile.deduct_points 發生錯誤: {e}")
            return None

    @staticmethod
    def get_leaderboard(limit=5):
        """
        取得積分排行榜（排除完全沒有回報紀錄或0分的用戶）
        """
        try:
            conn = get_db_connection()
            rows = conn.execute(
                '''SELECT nickname, points, level_name, reports_count 
                   FROM user_profiles 
                   WHERE points > 0 
                   ORDER BY points DESC, reports_count DESC 
                   LIMIT ?''',
                (limit,)
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except sqlite3.Error as e:
            print(f"UserProfile.get_leaderboard 發生錯誤: {e}")
            return []
