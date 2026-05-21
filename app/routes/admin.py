from flask import Blueprint, render_template
from app.models.status_log import StatusLog

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
def admin_dashboard():
    """
    管理員儀表板
    - 呼叫 StatusLog.get_stats() 取得系統統計資料
    - 渲染 admin.html 顯示設備歷史故障/排隊數據
    """
    # 取得系統所有狀態的統計次數 (哪些設備最常壞、最常排隊)
    stats = StatusLog.get_stats()
    
    # 渲染管理員統計畫面
    return render_template('admin.html', stats=stats)
