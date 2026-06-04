from flask import Blueprint, request, jsonify
from app.models.equipment import Equipment
from app.models.status_log import StatusLog

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/equipment/<int:equipment_id>/status', methods=['POST'])
def update_equipment_status(equipment_id):
    """
    非同步狀態回報 API
    - 接收前端 AJAX 傳來的 JSON 資料 (包含 status)
    - 驗證設備是否存在以及 status 是否為 available, queuing, maintenance 之一
    - 新增 StatusLog 紀錄
    - 回傳 JSON 格式的成功或失敗訊息
    """
    # 取得 AJAX 傳送的 JSON 資料
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'success': False, 'error': 'Missing status data'}), 400
        
    status = data['status'].strip().lower()
    valid_statuses = ['available', 'queuing', 'maintenance']
    
    # 輸入驗證
    if status not in valid_statuses:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
        
    # 檢查該設備是否存在
    equipment = Equipment.get_by_id(equipment_id)
    if not equipment:
        return jsonify({'success': False, 'error': 'Equipment not found'}), 404
        
    # 將回報寫入資料庫
    from flask import session
    log_data = {
        'equipment_id': equipment_id,
        'status': status,
        'reporter_session': session.get('user_session')
    }
    result = StatusLog.create(log_data)
    
    if result:
        return jsonify({'success': True, 'status': status}), 200
    else:
        return jsonify({'success': False, 'error': 'Internal server error while saving data'}), 500

@api_bp.route('/user/nickname', methods=['POST'])
def update_user_nickname():
    """
    修改使用者暱稱的 API
    """
    from flask import session
    data = request.get_json()
    if not data or 'nickname' not in data:
        return jsonify({'success': False, 'error': 'Missing nickname data'}), 400
        
    nickname = data['nickname'].strip()
    if not nickname:
        return jsonify({'success': False, 'error': 'Nickname cannot be empty'}), 400
        
    if len(nickname) > 15:
        return jsonify({'success': False, 'error': 'Nickname too long (max 15 chars)'}), 400
        
    session_id = session.get('user_session')
    from app.models.user import User
    if User.update_nickname(session_id, nickname):
        return jsonify({'success': True, 'nickname': nickname}), 200
    else:
        return jsonify({'success': False, 'error': 'Failed to update nickname'}), 500

@api_bp.route('/status_log/<int:log_id>/verify', methods=['POST'])
def verify_status_log(log_id):
    """
    點擊「同感/確認真實」API
    """
    from flask import session
    session_id = session.get('user_session')
    if not session_id:
        return jsonify({'success': False, 'error': 'Session not found'}), 400
        
    success, message = StatusLog.verify(log_id, session_id)
    
    if success:
        # 查詢更新後的驗證人數
        from app.models.db import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM verifications WHERE status_log_id = ?", (log_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return jsonify({'success': True, 'message': message, 'count': count}), 200
    else:
        return jsonify({'success': False, 'error': message}), 400

