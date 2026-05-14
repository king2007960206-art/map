from flask import Blueprint, request, jsonify
from app.models import Equipment, StatusLog

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
    pass
