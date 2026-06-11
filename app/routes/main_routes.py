from flask import Blueprint, render_template, session
import uuid
from app.models.location import Location
from app.models.prediction import PredictionEngine
from app.models.user import UserProfile

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def index():
    """首頁：校園人潮與溫度即時熱區預測看板"""
    if 'user_session' not in session:
        session['user_session'] = str(uuid.uuid4())
    user_session = session['user_session']
    
    # 獲取或建立使用者資料
    user_profile = UserProfile.get_or_create(user_session)
    
    # 獲取互助排行榜 (前5名)
    leaderboard = UserProfile.get_leaderboard(limit=5)
    
    locations = Location.get_all()
    
    # 獲取每個地點當前的預測數據與警報狀態
    active_alerts = []
    for loc in locations:
        pred_data = PredictionEngine.predict_next_hour(loc['id'])
        loc['current_crowd'] = pred_data['current_crowd']
        loc['current_temp'] = pred_data['current_temp']
        loc['has_alert'] = pred_data['has_alert']
        loc['alert_message'] = pred_data['alert_message']
        
        if pred_data['has_alert']:
            active_alerts.append({
                "location_id": loc['id'],
                "location_name": loc['name'],
                "message": pred_data['alert_message']
            })
            
    return render_template(
        'index.html', 
        locations=locations, 
        active_alerts=active_alerts, 
        user_profile=user_profile,
        leaderboard=leaderboard
    )

@main_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """歷史數據分析與長期趨勢看版"""
    locations = Location.get_all()
    return render_template('dashboard.html', locations=locations)

@main_bp.route('/admin/reports', methods=['GET'])
def admin_reports():
    """管理員：即時體感回報數據審查面版"""
    from app.models.report import Report
    reports = Report.get_all_recent(limit=50)
    return render_template('admin_reports.html', reports=reports)

