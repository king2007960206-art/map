from .db import get_db
import logging

class Equipment:
    @staticmethod
    def get_all(category=None):
        """
        取得所有設備記錄，可依據 category 過濾。
        支援 30 分鐘自動失效機制 (過期視為 available)。
        """
        try:
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
            return [dict(row) for row in rows]
        except Exception as e:
            logging.error(f"Error in Equipment.get_all: {e}")
            return []
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def get_by_id(equipment_id):
        """
        取得單筆設備記錄，包含最新狀態。
        """
        try:
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
            return dict(row) if row else None
        except Exception as e:
            logging.error(f"Error in Equipment.get_by_id: {e}")
            return None
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def create(data):
        """
        新增一筆設備記錄。
        參數 data 為字典，需包含 name, category，可選 location。
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO equipment (name, category, location) VALUES (?, ?, ?)",
                (data.get('name'), data.get('category'), data.get('location'))
            )
            
            equipment_id = cursor.lastrowid
            conn.commit()
            return equipment_id
        except Exception as e:
            logging.error(f"Error in Equipment.create: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
            return None
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def update(equipment_id, data):
        """
        更新特定設備記錄。
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            fields = []
            params = []
            for key in ['name', 'category', 'location']:
                if key in data:
                    fields.append(f"{key} = ?")
                    params.append(data[key])
                    
            if not fields:
                return False
                
            query = f"UPDATE equipment SET {', '.join(fields)} WHERE id = ?"
            params.append(equipment_id)
            
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error in Equipment.update: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def delete(equipment_id):
        """
        刪除特定設備記錄。
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM equipment WHERE id = ?", (equipment_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error in Equipment.delete: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()
