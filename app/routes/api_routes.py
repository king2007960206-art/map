from flask import Blueprint, request, jsonify, session
import uuid
import datetime
from app.models.location import Location
from app.models.report import Report
from app.models.prediction import PredictionEngine
from app.models.db import get_db_connection

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/locations', methods=['GET'])
def get_locations_api():
    """取得所有校園熱區位置與其當前預測狀態的 API"""
    try:
        locations = Location.get_all()
        for loc in locations:
            pred_data = PredictionEngine.predict_next_hour(loc['id'])
            loc['current_crowd'] = pred_data['current_crowd']
            loc['current_temp'] = pred_data['current_temp']
            loc['has_alert'] = pred_data['has_alert']
            loc['alert_message'] = pred_data['alert_message']
        return jsonify(locations)
    except Exception as e:
        return jsonify({"status": "error", "message": f"取得地點資料失敗: {e}"}), 500

@api_bp.route('/predictions/<int:location_id>', methods=['GET'])
def get_predictions_api(location_id):
    """
    取得特定地點的趨勢資料 (過去 3 小時的真實歷史紀錄 + 未來 1 小時的預測趨勢)
    """
    try:
        loc = Location.get_by_id(location_id)
        if not loc:
            return jsonify({"status": "error", "message": "找不到該地點"}), 404
            
        pred_data = PredictionEngine.predict_next_hour(location_id)
        
        # 取得過去 3 小時的歷史數據
        conn = get_db_connection()
        three_hours_ago = (datetime.datetime.now() - datetime.timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
        history_rows = conn.execute(
            '''SELECT timestamp, crowd_level, temperature 
               FROM historical_data 
               WHERE location_id = ? AND timestamp >= ? 
               ORDER BY timestamp ASC''',
            (location_id, three_hours_ago)
        ).fetchall()
        conn.close()
        
        history = []
        for r in history_rows:
            # 將 YYYY-MM-DD HH:MM:SS 轉成 HH:MM 格式方便前端圖表呈現
            t_str = r['timestamp']
            try:
                dt = datetime.datetime.strptime(t_str, '%Y-%m-%d %H:%M:%S')
                time_lbl = dt.strftime('%H:%M')
            except:
                time_lbl = t_str
            history.append({
                "time_str": time_lbl,
                "crowd_level": r['crowd_level'],
                "temperature": r['temperature']
            })
            
        return jsonify({
            "location": dict(loc),
            "history": history,
            "predictions": pred_data['predictions'],
            "current_crowd": pred_data['current_crowd'],
            "current_temp": pred_data['current_temp'],
            "has_alert": pred_data['has_alert'],
            "alert_message": pred_data['alert_message']
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"取得預測資料失敗: {e}"}), 500

@api_bp.route('/report', methods=['POST'])
def submit_report_api():
    """處理使用者即時回報的 API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "無效的請求內容"}), 400
            
        location_id = data.get('location_id')
        crowd_level = data.get('crowd_level') # 'low', 'medium', 'high'
        temperature_felt = data.get('temperature_felt') # 'cold', 'comfort', 'hot'
        
        if not location_id:
            return jsonify({"status": "error", "message": "請選擇回報地點"}), 400
            
        if not crowd_level and not temperature_felt:
            return jsonify({"status": "error", "message": "請至少填寫一項回報項目"}), 400
            
        # 驗證輸入合法性
        if crowd_level and crowd_level not in ['low', 'medium', 'high']:
            return jsonify({"status": "error", "message": "不合法的人潮狀態"}), 400
        if temperature_felt and temperature_felt not in ['cold', 'comfort', 'hot']:
            return jsonify({"status": "error", "message": "不合法的溫度體感狀態"}), 400
            
        # 獲取或產生 user session 用以防刷
        if 'user_session' not in session:
            session['user_session'] = str(uuid.uuid4())
        user_session = session['user_session']
        
        # 取得使用者 IP
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        # 防刷機制 (2 分鐘限制)
        is_spam = Report.check_recent_user_report(location_id, user_session, minutes=2)
        if is_spam:
            return jsonify({"status": "error", "message": "您在 2 分鐘內已回報過此地點，請稍後再試。"}), 429
            
        # 儲存回報
        new_id = Report.create(location_id, crowd_level, temperature_felt, user_ip, user_session)
        if new_id:
            from app.models.user import UserProfile
            profile = UserProfile.get_or_create(user_session)
            return jsonify({
                "status": "success", 
                "message": "回報成功！感謝您的即時互助回饋！",
                "profile": profile
            }), 200
        else:
            return jsonify({"status": "error", "message": "系統寫入失敗，請重試。"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"回報處理發生錯誤: {e}"}), 500

@api_bp.route('/geoip', methods=['GET'])
def geoip_api():
    """
    提供定位服務 API。
    如果是 localhost (127.0.0.1/::1) 或未定位，且請求中帶有 simulate=true，
    則模擬回傳在逢甲大學大樓附近的座標。
    """
    simulate = request.args.get('simulate') == 'true'
    
    if simulate:
        # 模擬在圖書館與人言大樓之間
        return jsonify({
            "status": "success",
            "lat": 24.1796,
            "lon": 120.6486,
            "source": "simulated"
        })
        
    # 一般情況下嘗試透過 IP 地理定位 API (使用 keyless API ip-api)
    # 在前端發送請求往往比後端更精準，但在這裡也提供一個代理
    # 若為本機，回傳無定位
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if user_ip in ['127.0.0.1', '::1', 'localhost']:
        return jsonify({
            "status": "fail",
            "message": "Localhost IP Cannot geolocate",
            "source": "local"
        })
        
    return jsonify({
        "status": "success",
        "ip": user_ip,
        "lat": 24.179, # 預設 Taichung
        "lon": 120.647,
        "source": "default"
    })

@api_bp.route('/heatscape', methods=['GET'])
def get_heatscape_api():
    """
    取得所有地點的雙維度體感地景資料。
    回傳：擁擠度 (crowd)、溫度 (temp)、溫度體感 (temp_feel)、
         複合熱度分數 (heat_score)、熱力圖強度 (heat_intensity)
    """
    try:
        locations = Location.get_all()
        result = []
        for loc in locations:
            pred_data = PredictionEngine.predict_next_hour(loc['id'])
            crowd = pred_data['current_crowd']
            temp = pred_data['current_temp']

            # 計算溫度體感分類
            if temp <= 22:
                temp_feel = 'cold'
                temp_label = '偏冷'
            elif temp >= 27:
                temp_feel = 'hot'
                temp_label = '悶熱'
            else:
                temp_feel = 'comfort'
                temp_label = '舒適'

            # 計算複合熱度分數 (0~100)
            # 人潮佔 70%，溫度佔 30%
            # 溫度分數：冷=低，熱=高 (15~35°C 映射到 0~100)
            temp_score = max(0, min(100, (temp - 15) / 20 * 100))
            heat_score = round(crowd * 0.7 + temp_score * 0.3, 1)

            # 熱力圖強度 (0.0~1.0)
            heat_intensity = round(heat_score / 100, 3)

            result.append({
                'id': loc['id'],
                'name': loc['name'],
                'latitude': loc['latitude'],
                'longitude': loc['longitude'],
                'crowd': round(crowd, 1),
                'temp': round(temp, 1),
                'temp_feel': temp_feel,
                'temp_label': temp_label,
                'heat_score': heat_score,
                'heat_intensity': heat_intensity,
                'has_alert': pred_data['has_alert'],
                'alert_message': pred_data['alert_message']
            })

        return jsonify({'status': 'success', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'體感地景資料取得失敗: {e}'}), 500


@api_bp.route('/user/nickname', methods=['POST'])
def update_nickname_api():
    """更新目前用戶暱稱的 API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "無效的請求"}), 400
            
        nickname = data.get('nickname')
        if not nickname or not nickname.strip():
            return jsonify({"status": "error", "message": "暱稱不得為空"}), 400
            
        if len(nickname) > 15:
            return jsonify({"status": "error", "message": "暱稱長度不能超過 15 個字"}), 400
            
        if 'user_session' not in session:
            session['user_session'] = str(uuid.uuid4())
        user_session = session['user_session']
        
        from app.models.user import UserProfile
        success = UserProfile.update_nickname(user_session, nickname)
        
        if success:
            profile = UserProfile.get_or_create(user_session)
            return jsonify({"status": "success", "message": "暱稱更新成功！", "profile": profile}), 200
        else:
            return jsonify({"status": "error", "message": "暱稱更新失敗"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"更新暱稱發生錯誤: {e}"}), 500

@api_bp.route('/admin/reports/<int:report_id>/abnormal', methods=['POST'])
def mark_abnormal_api(report_id):
    """將某一筆回報標記為異常的 API"""
    try:
        success = Report.mark_as_abnormal(report_id)
        if success:
            return jsonify({"status": "success", "message": "已成功將該回報標記為異常，排除計算並扣除該用戶 20 積分。"}), 200
        else:
            return jsonify({"status": "error", "message": "標記異常失敗，或找不到該筆紀錄"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"系統處理錯誤: {e}"}), 500

@api_bp.route('/admin/reports/<int:report_id>/normal', methods=['POST'])
def mark_normal_api(report_id):
    """將某一筆異常回報恢復為正常的 API"""
    try:
        success = Report.mark_as_normal(report_id)
        if success:
            return jsonify({"status": "success", "message": "已成功將該回報恢復為正常，重新納入計算並還原該用戶積分。"}), 200
        else:
            return jsonify({"status": "error", "message": "恢復正常失敗，或找不到該筆紀錄"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"系統處理錯誤: {e}"}), 500
