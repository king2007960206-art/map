from flask import session, g
import uuid
from app.models.user import User
from .main import main_bp
from .api import api_bp
from .admin import admin_bp

def register_blueprints(app):
    """
    將所有 Blueprint 註冊到 Flask app 實例，並處理全域用戶 Session 追蹤與注入。
    """
    # 註冊 Blueprint 路由
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)

    @app.before_request
    def ensure_user_session():
        # 確保 session 中存在唯一的 user_session ID
        if 'user_session' not in session:
            session['user_session'] = str(uuid.uuid4())
            
        # 獲取或建立使用者資料，並附帶等級稱號資訊，儲存到 Flask g 中
        user_data = User.get_or_create(session['user_session'])
        if user_data:
            user_data['level_info'] = User.get_level_info(user_data['points'])
        g.current_user = user_data

    @app.context_processor
    def inject_user():
        # 注入 current_user 變數，讓所有 Jinja2 模板皆可以直接調用
        return dict(current_user=getattr(g, 'current_user', None))

