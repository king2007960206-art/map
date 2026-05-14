from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    
    # 基本設定
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # 註冊路由 Blueprints
    from .routes import register_routes
    register_routes(app)
    
    return app
