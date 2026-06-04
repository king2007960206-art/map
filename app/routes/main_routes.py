from flask import Blueprint, render_template
from app.models.location import Location
from app.models.report import Report

sensation_main_bp = Blueprint('sensation_main', __name__)

@sensation_main_bp.route('/', methods=['GET'])
def index():
    """首頁：顯示所有地點與最新狀態"""
    locations = Location.get_all()
    for loc in locations:
        recent = Report.get_recent_by_location(loc['id'], limit=1)
        if recent:
            loc['latest_tag'] = recent[0]['tag']
            loc['latest_time'] = recent[0]['created_at']
        else:
            loc['latest_tag'] = None
            loc['latest_time'] = None
            
    return render_template('index.html', locations=locations)

@sensation_main_bp.route('/admin/dashboard', methods=['GET'])
def dashboard():
    locations = Location.get_all()
    return render_template('dashboard.html', locations=locations)


