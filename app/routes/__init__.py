# 體感地圖的 Blueprints
from .main_routes import sensation_main_bp
from .api_routes import sensation_api_bp

# 設備狀態的 Blueprints
from .main import equipment_main_bp
from .api import equipment_api_bp
from .admin import equipment_admin_bp

def register_blueprints(app):
    """
    將所有 Blueprint 註冊到 Flask app 實例，避免命名空間衝突
    """
    # 1. 校園設施體感地圖 (Sensation Map)
    app.register_blueprint(sensation_main_bp)
    app.register_blueprint(sensation_api_bp)
    
    # 2. 設備狀態回報 (Equipment Status)
    app.register_blueprint(equipment_main_bp, url_prefix='/equipment')
    app.register_blueprint(equipment_api_bp)
    app.register_blueprint(equipment_admin_bp)

