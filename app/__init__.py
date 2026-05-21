from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    
    # 基本設定
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # 註冊路由 Blueprints
    from .routes import register_routes
    register_routes(app)
from .routes import register_blueprints
from .models.db import init_db

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev_secret_key'  # 開發用的 SECRET_KEY，上線應從環境變數讀取
    
    # 確保應用啟動時初始化資料庫
    init_db()
    
    # 註冊所有路由 Blueprint
    register_blueprints(app)
    
    return app
