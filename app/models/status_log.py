from .db import get_db

class StatusLog:
    @staticmethod
    def create(equipment_id, status):
        """
        新增一筆狀態紀錄
        status 必須是 'available', 'queuing', 或 'maintenance'
        """
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO status_logs (equipment_id, status) VALUES (?, ?)",
            (equipment_id, status)
        )
        
        log_id = cursor.lastrowid
        
        # 取回新增的紀錄以便回傳
        cursor.execute("SELECT * FROM status_logs WHERE id = ?", (log_id,))
        new_record = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        return dict(new_record) if new_record else None

    @staticmethod
    def get_history_by_equipment(equipment_id, limit=10):
        """
        取得特定設備的歷史狀態紀錄
        """
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM status_logs WHERE equipment_id = ? ORDER BY reported_at DESC LIMIT ?",
            (equipment_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
        
    @staticmethod
    def get_stats():
        """
        後台統計用：計算各個狀態的總發生次數等
        """
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT e.name, e.category, s.status, COUNT(*) as count
            FROM status_logs s
            JOIN equipment e ON s.equipment_id = e.id
            GROUP BY s.equipment_id, s.status
            ORDER BY count DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
