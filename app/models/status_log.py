from .db import get_db
import logging

class StatusLog:
    @staticmethod
    def create(data):
        """
        新增一筆狀態紀錄
        data 為字典，需包含 equipment_id 與 status
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO status_logs (equipment_id, status) VALUES (?, ?)",
                (data.get('equipment_id'), data.get('status'))
            )
            
            log_id = cursor.lastrowid
            
            # 取回新增的紀錄以便回傳
            cursor.execute("SELECT * FROM status_logs WHERE id = ?", (log_id,))
            new_record = cursor.fetchone()
            
            conn.commit()
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
        取得單筆狀態紀錄
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM status_logs WHERE id = ?", (log_id,))
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
        後台統計用：計算各個狀態的總發生次數等
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT e.name, e.category, s.status, COUNT(*) as count
                FROM status_logs s
                JOIN equipment e ON s.equipment_id = e.id
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
