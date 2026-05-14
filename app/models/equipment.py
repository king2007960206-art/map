from .db import get_db

class Equipment:
    @staticmethod
    def get_all(category=None):
        conn = get_db()
        cursor = conn.cursor()
        
        # PRD 要求: 標註後過 30 分鐘自動重置 (Lazy Evaluation)
        # 我們在這裡使用 LEFT JOIN 找出每台設備的最新一筆紀錄，如果時間超過 30 分鐘或沒有紀錄，就當作 available
        query = """
            SELECT 
                e.id, 
                e.name, 
                e.category, 
                e.location,
                e.created_at,
                CASE 
                    WHEN s.reported_at IS NULL THEN 'available'
                    WHEN (strftime('%s', 'now') - strftime('%s', s.reported_at)) > 1800 THEN 'available'
                    ELSE s.status
                END as current_status,
                s.reported_at as last_reported_at
            FROM equipment e
            LEFT JOIN (
                SELECT equipment_id, status, reported_at
                FROM status_logs
                WHERE id IN (
                    SELECT MAX(id) FROM status_logs GROUP BY equipment_id
                )
            ) s ON e.id = s.equipment_id
        """
        
        params = []
        if category:
            query += " WHERE e.category = ?"
            params.append(category)
            
        query += " ORDER BY e.id"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    @staticmethod
    def get_by_id(equipment_id):
        conn = get_db()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                e.id, 
                e.name, 
                e.category, 
                e.location,
                e.created_at,
                CASE 
                    WHEN s.reported_at IS NULL THEN 'available'
                    WHEN (strftime('%s', 'now') - strftime('%s', s.reported_at)) > 1800 THEN 'available'
                    ELSE s.status
                END as current_status,
                s.reported_at as last_reported_at
            FROM equipment e
            LEFT JOIN (
                SELECT equipment_id, status, reported_at
                FROM status_logs
                WHERE equipment_id = ?
                ORDER BY reported_at DESC
                LIMIT 1
            ) s ON e.id = s.equipment_id
            WHERE e.id = ?
        """
        
        cursor.execute(query, (equipment_id, equipment_id))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None

    @staticmethod
    def create(name, category, location=None):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO equipment (name, category, location) VALUES (?, ?, ?)",
            (name, category, location)
        )
        
        equipment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return equipment_id

    @staticmethod
    def update(equipment_id, name=None, category=None, location=None):
        conn = get_db()
        cursor = conn.cursor()
        
        # 簡單的 update 邏輯
        fields = []
        params = []
        if name is not None:
            fields.append("name = ?")
            params.append(name)
        if category is not None:
            fields.append("category = ?")
            params.append(category)
        if location is not None:
            fields.append("location = ?")
            params.append(location)
            
        if not fields:
            return False
            
        query = f"UPDATE equipment SET {', '.join(fields)} WHERE id = ?"
        params.append(equipment_id)
        
        cursor.execute(query, params)
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        return rows_affected > 0

    @staticmethod
    def delete(equipment_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM equipment WHERE id = ?", (equipment_id,))
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        return rows_affected > 0
