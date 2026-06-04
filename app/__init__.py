from flask import Flask
import os
from .models.db import init_db
from .routes import register_routes

def create_app():
    app = Flask(__name__)
    
    # Set secret key
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-smart-prediction')
    
    # Ensure database is initialized
    with app.app_context():
        init_db()
    
    # Register blueprints
    register_routes(app)
    
    return app

