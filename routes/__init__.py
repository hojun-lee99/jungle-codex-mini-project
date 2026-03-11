from .auth import auth_bp
from .main import main_bp
from .profile import profile_bp
from .recommendations import recommendation_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(recommendation_bp)
