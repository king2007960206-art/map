from .main_routes import main_bp
from .api_routes import api_bp

def register_routes(app):
    """
    Register Blueprints for the Flask application.
    """
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

