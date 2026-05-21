from .main_routes import main_bp
from .api_routes import api_bp

def register_routes(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
from .main import main_bp
from .api import api_bp
from .admin import admin_bp

def register_blueprints(app):
    """
    將所有 Blueprint 註冊到 Flask app 實例
    """
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
