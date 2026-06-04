from .db import get_db
from .user import User
import logging

class StatusLog:
    @staticmethod
    def create(data):
        """
        新增一筆狀態紀錄。
        data 為字典，需包含 equipment_id, status 以及 reporter_session。
        每次新增回報時，會為回報者加上 10 分積分。
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            reporter_session = data.get('reporter_session')
            
            cursor.execute(
                "INSERT INTO status_logs (equipment_id, status, reporter_session, is_valid) VALUES (?, ?, ?, 1)",
                (data.get('equipment_id'), data.get('status'), reporter_session)
            )
            
            log_id = cursor.lastrowid
            
            # 取回新增的紀錄以便回傳
            cursor.execute("SELECT * FROM status_logs WHERE id = ?", (log_id,))
            new_record = cursor.fetchone()
            
            conn.commit()
            
            # 回報成功，幫用戶加上 10 分
            if reporter_session:
                User.add_points(reporter_session, 10)
                
            return dict(new_record) if new_record else None
        except Exception as e:
            logging.error(f"Error in StatusLog.create: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
            return None
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def get_all():
        """
        取得所有狀態紀錄
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM status_logs ORDER BY reported_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logging.error(f"Error in StatusLog.get_all: {e}")
            return []
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def get_by_id(log_id):
        """
        取得單筆狀態紀錄，包含回報者資訊。
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, u.nickname as reporter_nickname, u.points as reporter_points
                FROM status_logs s
                LEFT JOIN users u ON s.reporter_session = u.session_id
                WHERE s.id = ?
            """, (log_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logging.error(f"Error in StatusLog.get_by_id: {e}")
            return None
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def update(log_id, data):
        """
        更新特定狀態紀錄 (較少用到，但依技能要求實作)
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            if 'status' not in data:
                return False
                
            cursor.execute(
                "UPDATE status_logs SET status = ? WHERE id = ?",
                (data['status'], log_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error in StatusLog.update: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def delete(log_id):
        """
        刪除特定狀態紀錄
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM status_logs WHERE id = ?", (log_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error in StatusLog.delete: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def get_history_by_equipment(equipment_id, limit=10):
        """
        取得特定設備的歷史狀態紀錄
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM status_logs WHERE equipment_id = ? ORDER BY reported_at DESC LIMIT ?",
                (equipment_id, limit)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logging.error(f"Error in StatusLog.get_history_by_equipment: {e}")
            return []
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def get_stats():
        """
        後台統計用：計算各個狀態的總發生次數等 (排除已過濾的異常數據)
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT e.name, e.category, s.status, COUNT(*) as count
                FROM status_logs s
                JOIN equipment e ON s.equipment_id = e.id
                WHERE s.is_valid = 1
                GROUP BY s.equipment_id, s.status
                ORDER BY count DESC
            ''')
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logging.error(f"Error in StatusLog.get_stats: {e}")
            return []
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def get_recent_logs(limit=50):
        """
        獲取最近的所有狀態回報，供管理員儀表板審查。
        會標記 suspicious = True 如果同一個用戶在短時間（60秒內）重複回報。
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, e.name as equipment_name, u.nickname as reporter_nickname, u.points as reporter_points,
                       (SELECT COUNT(*) FROM verifications v WHERE v.status_log_id = s.id) as verification_count
                FROM status_logs s
                JOIN equipment e ON s.equipment_id = e.id
                LEFT JOIN users u ON s.reporter_session = u.session_id
                ORDER BY s.reported_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            logs = [dict(row) for row in rows]
            
            # 分析異常回報：同個 reporter_session 在 60 秒內回報多個紀錄，標記為 suspicious
            for i, log in enumerate(logs):
                log['suspicious'] = False
                # 附加等級稱號資訊
                if log['reporter_points'] is not None:
                    log['reporter_level_info'] = User.get_level_info(log['reporter_points'])
                else:
                    log['reporter_level_info'] = {'level_name': '未知'}
                
                if not log['reporter_session']:
                    continue
                    
                # 比較與前後日誌的時間差
                from datetime import datetime
                # SQLite 回傳格式通常是 'YYYY-MM-DD HH:MM:SS' 或類似
                try:
                    t1 = datetime.strptime(log['reported_at'].split('.')[0], "%Y-%m-%d %H:%M:%S")
                    
                    # 尋找其他同 session 的日誌
                    for other in logs:
                        if other['id'] == log['id'] or other['reporter_session'] != log['reporter_session']:
                            continue
                        t2 = datetime.strptime(other['reported_at'].split('.')[0], "%Y-%m-%d %H:%M:%S")
                        diff_seconds = abs((t1 - t2).total_seconds())
                        if diff_seconds <= 60:
                            log['suspicious'] = True
                            break
                except Exception as parse_err:
                    logging.error(f"Error parsing date {log['reported_at']}: {parse_err}")
            
            return logs
        except Exception as e:
            logging.error(f"Error in StatusLog.get_recent_logs: {e}")
            return []
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def invalidate(log_id):
        """
        將指定回報標記為異常 (is_valid = 0)。
        並對回報者扣除 20 分積分作為處罰。
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # 取得該日誌資訊
            cursor.execute("SELECT reporter_session, is_valid FROM status_logs WHERE id = ?", (log_id,))
            row = cursor.fetchone()
            if not row:
                return False
                
            log = dict(row)
            if log['is_valid'] == 0:
                return True # 已經是異常了
                
            # 標記為異常
            cursor.execute("UPDATE status_logs SET is_valid = 0 WHERE id = ?", (log_id,))
            conn.commit()
            
            # 懲罰扣分
            reporter_session = log['reporter_session']
            if reporter_session:
                User.add_points(reporter_session, -20)
                
            return True
        except Exception as e:
            logging.error(f"Error in StatusLog.invalidate: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def validate(log_id):
        """
        重新將指定回報恢復為正常 (is_valid = 1)。
        並恢復回報者的積分 (+20)。
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # 取得該日誌資訊
            cursor.execute("SELECT reporter_session, is_valid FROM status_logs WHERE id = ?", (log_id,))
            row = cursor.fetchone()
            if not row:
                return False
                
            log = dict(row)
            if log['is_valid'] == 1:
                return True # 已經是正常了
                
            # 標記為正常
            cursor.execute("UPDATE status_logs SET is_valid = 1 WHERE id = ?", (log_id,))
            conn.commit()
            
            # 恢復加分
            reporter_session = log['reporter_session']
            if reporter_session:
                User.add_points(reporter_session, 20)
                
            return True
        except Exception as e:
            logging.error(f"Error in StatusLog.validate: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def verify(log_id, verifier_session):
        """
        針對某一筆狀態回報點擊「同感/確認真實」。
        規則：
        - 不能驗證自己的回報
        - 一個用戶對同一筆回報只能驗證一次
        - 驗證成功後，原回報者加 5 分，驗證者加 2 分
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # 1. 取得狀態日誌以取得回報者 session
            cursor.execute("SELECT reporter_session, is_valid FROM status_logs WHERE id = ?", (log_id,))
            row = cursor.fetchone()
            if not row:
                return False, "找不到該回報紀錄"
                
            log = dict(row)
            if not log['is_valid']:
                return False, "該回報已被標記為異常，無法驗證"
                
            reporter_session = log['reporter_session']
            
            # 2. 檢查是否是回報者本人
            if reporter_session == verifier_session:
                return False, "您不能對自己的回報點擊同感"
                
            # 3. 檢查是否已驗證過
            cursor.execute(
                "SELECT COUNT(*) FROM verifications WHERE status_log_id = ? AND verifier_session = ?",
                (log_id, verifier_session)
            )
            if cursor.fetchone()[0] > 0:
                return False, "您已經對此回報點擊過同感了"
                
            # 4. 寫入驗證紀錄
            cursor.execute(
                "INSERT INTO verifications (status_log_id, verifier_session) VALUES (?, ?)",
                (log_id, verifier_session)
            )
            conn.commit()
            
            # 5. 發放積分
            if reporter_session:
                User.add_points(reporter_session, 5) # 原回報者 +5 分
            User.add_points(verifier_session, 2)     # 驗證者 +2 分
            
            return True, "同感確認成功！"
        except Exception as e:
            logging.error(f"Error in StatusLog.verify: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
            return False, "資料庫處理錯誤"
        finally:
            if 'conn' in locals() and conn:
                conn.close()

