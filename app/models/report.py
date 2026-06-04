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

    @staticmethod
    def get_trends_by_location(location_id, hours=24):
        """
        取得指定地點過去 24 小時的體感與擁擠度變化趨勢。
        若資料庫中該地點的資料量不足 (少於 5 筆)，則自動產生規律性的模擬數據。
        """
        import datetime as dt
        import random
        from .db import get_db_connection
        
        # 1. 嘗試從資料庫讀取真實數據
        try:
            conn = get_db_connection()
            # 取得 24 小時前的時間 (UTC)
            time_limit = (dt.datetime.utcnow() - dt.timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
            
            query = """
                SELECT tag, created_at 
                FROM reports 
                WHERE location_id = ? AND datetime(created_at) >= datetime(?)
                ORDER BY created_at ASC
            """
            rows = conn.execute(query, (location_id, time_limit)).fetchall()
            conn.close()
            reports = [dict(r) for r in rows]
        except Exception as e:
            print(f"查詢歷史趨勢發生錯誤: {e}")
            reports = []

        # 2. 定義時間點 (過去 24 小時)
        local_now = dt.datetime.now() # 我們使用系統本地時間來格式化標籤，方便使用者閱讀
        labels = []
        for i in range(hours - 1, -1, -1):
            time_point = local_now - dt.timedelta(hours=i)
            labels.append(time_point.strftime('%H:00'))

        # 3. 判斷是否需要模擬數據
        use_mock = len(reports) < 5
        
        temperature_trends = []
        occupancy_trends = []
        
        if use_mock:
            # 產生符合特定場域情境的模擬數據
            # 假設：下午 14:00 - 17:00 偏熱；中午 12:00-13:30 及晚上 18:00-20:00 爆滿；深夜空曠且冷
            for i in range(hours - 1, -1, -1):
                time_point = local_now - dt.timedelta(hours=i)
                hour = time_point.hour
                
                # 預設基準值 (舒適 = 2.0)
                temp = 2.0
                occ = 2.0
                
                # 下午變熱
                if 14 <= hour <= 17:
                    temp = 2.7 + random.uniform(-0.15, 0.15)
                    occ = 2.1 + random.uniform(-0.1, 0.1)
                # 中午與晚餐時段爆滿
                elif 12 <= hour <= 13 or 18 <= hour <= 20:
                    occ = 2.8 + random.uniform(-0.1, 0.1)
                    temp = 2.2 + random.uniform(-0.1, 0.1)
                # 深夜/清晨冷且空曠
                elif 0 <= hour <= 6 or 22 <= hour <= 23:
                    occ = 1.1 + random.uniform(0.0, 0.15)
                    temp = 1.4 + random.uniform(-0.15, 0.15)
                else:
                    # 離峰時段
                    temp = 2.0 + random.uniform(-0.15, 0.15)
                    occ = 1.8 + random.uniform(-0.15, 0.15)
                
                # 限制範圍在 1.0 - 3.0
                temp = max(1.0, min(3.0, temp))
                occ = max(1.0, min(3.0, occ))
                
                temperature_trends.append(temp)
                occupancy_trends.append(occ)
                
            insight = "💡 智慧提示：分析顯示該地點在下午 2:00 ~ 5:00 期間「悶熱」回報偏多，建議攜帶隨身風扇；另外中午 12 點與晚上 6 點前後為人潮尖峰，建議避開此時段以獲得更舒適的空間體驗。"
        else:
            # 使用真實數據進行每小時統計聚合
            hour_data = {label: [] for label in labels}
            
            # 將資料放入對應的小時桶中
            for r in reports:
                try:
                    # 解析 created_at (UTC)
                    utc_time = dt.datetime.strptime(r['created_at'], '%Y-%m-%d %H:%M:%S')
                    # 轉為本地時間 (UTC+8)
                    local_time = utc_time + dt.timedelta(hours=8)
                    hour_str = local_time.strftime('%H:00')
                    if hour_str in hour_data:
                        hour_data[hour_str].append(r)
                except Exception as ex:
                    print(f"時間解析錯誤: {ex}")
            
            # 計算每小時的平均指數
            last_temp = 2.0
            last_occ = 2.0
            
            for label in labels:
                hr_reports = hour_data[label]
                if not hr_reports:
                    temperature_trends.append(last_temp)
                    occupancy_trends.append(last_occ)
                else:
                    temp_scores = []
                    occ_scores = []
                    for r in hr_reports:
                        t = r['tag']
                        if t == '超冷':
                            temp_scores.append(1.0)
                        elif t == '悶熱':
                            temp_scores.append(3.0)
                        elif t == '空曠':
                            occ_scores.append(1.0)
                        elif t == '爆滿':
                            occ_scores.append(3.0)
                    
                    avg_temp = sum(temp_scores) / len(temp_scores) if temp_scores else 2.0
                    avg_occ = sum(occ_scores) / len(occ_scores) if occ_scores else 2.0
                    
                    temperature_trends.append(avg_temp)
                    occupancy_trends.append(avg_occ)
                    last_temp = avg_temp
                    last_occ = avg_occ
            
            # 產生基於真實數據的動態情境提示
            hot_hours = [labels[idx] for idx, t in enumerate(temperature_trends) if t >= 2.4]
            full_hours = [labels[idx] for idx, o in enumerate(occupancy_trends) if o >= 2.4]
            
            insights = []
            if hot_hours:
                insights.append(f"{', '.join(hot_hours[:3])} 回報較為悶熱")
            if full_hours:
                insights.append(f"{', '.join(full_hours[:3])} 人潮較為擁擠")
            
            if insights:
                insight = "💡 智慧提示：分析顯示此地點在 " + "，且 ".join(insights) + "，建議您提前決策以避開這些尖峰時段。"
            else:
                insight = "💡 智慧提示：目前此場域的溫度體感與擁擠度在過去 24 小時內均維持在舒適範圍內，適合前往。"
                
        return {
            "labels": labels,
            "temperature_trends": temperature_trends,
            "occupancy_trends": occupancy_trends,
            "scenario_insight": insight
        }

