from flask import Blueprint, render_template, request, jsonify
from app.models.status_log import StatusLog

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
def admin_dashboard():
    """
    管理員儀表板
    - 呼叫 StatusLog.get_stats() 取得系統統計資料
    - 呼叫 StatusLog.get_recent_logs() 取得最近回報日誌以利審查
    - 渲染 admin.html
    """
    stats = StatusLog.get_stats()
    recent_logs = StatusLog.get_recent_logs(limit=50)
    
    return render_template('admin.html', stats=stats, recent_logs=recent_logs)

@admin_bp.route('/invalidate-log/<int:log_id>', methods=['POST'])
def invalidate_log(log_id):
    """
    管理員標記狀態紀錄為異常
    """
    if StatusLog.invalidate(log_id):
        return jsonify({'success': True, 'message': '已將該筆回報標記為異常並扣除回報者積分'}), 200
    else:
        return jsonify({'success': False, 'error': '操作失敗，請確認該回報是否存在'}), 400

@admin_bp.route('/validate-log/<int:log_id>', methods=['POST'])
def validate_log(log_id):
    """
    管理員還原/標記狀態紀錄為正常
    """
    if StatusLog.validate(log_id):
        return jsonify({'success': True, 'message': '已將該筆回報標記為正常並還原回報者積分'}), 200
    else:
        return jsonify({'success': False, 'error': '操作失敗，請確認該回報是否存在'}), 400

