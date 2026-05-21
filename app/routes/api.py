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
    log_data = {
        'equipment_id': equipment_id,
        'status': status
    }
    result = StatusLog.create(log_data)
    
    if result:
        return jsonify({'success': True, 'status': status}), 200
    else:
        return jsonify({'success': False, 'error': 'Internal server error while saving data'}), 500
