from flask import Blueprint, render_template
from app.models.location import Location
from app.models.prediction import PredictionEngine

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def index():
    """首頁：校園人潮與溫度即時熱區預測看板"""
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
            
    return render_template('index.html', locations=locations, active_alerts=active_alerts)

@main_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """歷史數據分析與長期趨勢看版"""
    locations = Location.get_all()
    return render_template('dashboard.html', locations=locations)
