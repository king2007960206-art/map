from .db import get_db
import logging

class User:
    @staticmethod
    def get_or_create(session_id):
        """
        獲取或建立使用者。若不存在，則自動建立一筆預設資料。
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE session_id = ?", (session_id,))
            user = cursor.fetchone()
            
            if not user:
                # 預設暱稱使用 session_id 的後 6 碼
                short_id = session_id[-6:] if len(session_id) >= 6 else session_id
                default_nickname = f"匿名守護者_{short_id}"
                
                cursor.execute(
                    "INSERT INTO users (session_id, nickname, points) VALUES (?, ?, 0)",
                    (session_id, default_nickname)
                )
                conn.commit()
                
                cursor.execute("SELECT * FROM users WHERE session_id = ?", (session_id,))
                user = cursor.fetchone()
                
            return dict(user)
        except Exception as e:
            logging.error(f"Error in User.get_or_create: {e}")
            return None
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def update_nickname(session_id, nickname):
        """
        更新使用者的暱稱。
        """
        if not nickname or not nickname.strip():
            return False
            
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET nickname = ? WHERE session_id = ?",
                (nickname.strip(), session_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error in User.update_nickname: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def add_points(session_id, points):
        """
        增加或扣除使用者的積分。分數最低為 0。
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # 先確認用戶存在
            User.get_or_create(session_id)
            
            cursor.execute(
                "UPDATE users SET points = MAX(0, points + ?) WHERE session_id = ?",
                (points, session_id)
            )
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error in User.add_points: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def get_leaderboard(limit=10):
        """
        獲取積分前 N 名的使用者排行榜。
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users ORDER BY points DESC, created_at ASC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            leaderboard = []
            for row in rows:
                user_dict = dict(row)
                # 附加等級資訊
                user_dict['level_info'] = User.get_level_info(user_dict['points'])
                leaderboard.append(user_dict)
            return leaderboard
        except Exception as e:
            logging.error(f"Error in User.get_leaderboard: {e}")
            return []
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def get_level_info(points):
        """
        根據積分計算等級資訊（名稱、進度條比例、級距、下一個等級所需積分）。
        """
        if points < 50:
            level_name = "校園新人 🎓"
            level_class = "level-rookie"
            min_pts = 0
            max_pts = 50
            progress = int((points / 50) * 100)
            next_level_desc = f"還差 {50 - points} 分升級至 熱心同學"
        elif points < 150:
            level_name = "熱心同學 🌟"
            level_class = "level-helper"
            min_pts = 50
            max_pts = 150
            progress = int(((points - 50) / 100) * 100)
            next_level_desc = f"還差 {150 - points} 分升級至 校園巡邏員"
        elif points < 300:
            level_name = "校園巡邏員 🔍"
            level_class = "level-patrol"
            min_pts = 150
            max_pts = 300
            progress = int(((points - 150) / 150) * 100)
            next_level_desc = f"還差 {300 - points} 分升級至 校園守護者"
        else:
            level_name = "校園守護者 👑"
            level_class = "level-guardian"
            min_pts = 300
            max_pts = 300
            progress = 100
            next_level_desc = "已達最高榮譽等級！"

        return {
            'level_name': level_name,
            'level_class': level_class,
            'progress': progress,
            'current_points': points,
            'min_pts': min_pts,
            'max_pts': max_pts,
            'next_level_desc': next_level_desc,
            'is_max': points >= 300
        }
