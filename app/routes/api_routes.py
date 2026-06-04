from flask import Blueprint, request, jsonify, session
import uuid
from app.models.report import Report
from app.models.location import Location

sensation_api_bp = Blueprint('sensation_api', __name__, url_prefix='/api')

@sensation_api_bp.route('/locations', methods=['GET'])
def get_locations():
    """
    提供前端非同步獲取所有地點與最新狀態的 API。
    """
    locations = Location.get_all()
    
    # 針對每個 location，取得最新的回報狀態
    for loc in locations:
        recent = Report.get_recent_by_location(loc['id'], limit=1)
        if recent:
            loc['latest_tag'] = recent[0]['tag']
            loc['latest_time'] = recent[0]['created_at']
        else:
            loc['latest_tag'] = None
            loc['latest_time'] = None
            
    return jsonify(locations)

@sensation_api_bp.route('/report', methods=['POST'])
def submit_report():
    """
    處理前端送出的體感回報。
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "無效的請求資料"}), 400
        
    location_id = data.get('location_id')
    tag = data.get('tag')
    
    if not location_id or not tag:
        return jsonify({"status": "error", "message": "缺少必要的參數 (location_id, tag)"}), 400
        
    # 獲取或產生使用者的 session 識別碼
    if 'user_session' not in session:
        session['user_session'] = str(uuid.uuid4())
    user_session = session['user_session']
    
    # 檢查防刷機制（同一地點 5 分鐘內只能回報一次）
    is_spam = Report.check_recent_user_report(location_id, user_session, minutes=5)
    if is_spam:
        return jsonify({"status": "error", "message": "您已在近期回報過此地點，請稍後再試"}), 429
        
    # 儲存回報進資料庫
    new_id = Report.create(location_id, tag, user_session)
    if new_id:
        return jsonify({"status": "success", "message": "回報成功！感謝您的提供"}), 200
    else:
        return jsonify({"status": "error", "message": "伺服器發生錯誤，寫入失敗"}), 500

@sensation_api_bp.route('/locations/<int:location_id>/trends', methods=['GET'])
def get_location_trends(location_id):
    """
    提供前端非同步獲取特定地點的 24 小時歷史體感趨勢資料。
    """
    loc = Location.get_by_id(location_id)
    if not loc:
        return jsonify({"status": "error", "message": "找不到該地點"}), 404
        
    trends = Report.get_trends_by_location(location_id)
    return jsonify(trends), 200

