from flask import Flask
import os
from .models.db import init_db
from .routes import register_blueprints

def create_app():
    app = Flask(__name__)
    
    # 基本設定 (優先從環境變數讀取，預設為 dev_secret_key)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
    
    # 確保應用啟動時初始化資料庫
    init_db()
    
    # 註冊所有路由 Blueprint
    register_blueprints(app)
    
    return app

