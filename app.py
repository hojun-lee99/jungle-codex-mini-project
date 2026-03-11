from flask import Flask, g, render_template, session

from config import Config
from db.mongo import mongo
from routes import register_blueprints
from services.account import get_user_by_id
from services.trends import ensure_runtime_seed


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mongo.init_app(app)

    with app.app_context():
        ensure_runtime_seed()

    register_blueprints(app)

    @app.before_request
    def load_current_user():
        user_id = session.get("user_id")
        g.user = get_user_by_id(user_id) if user_id else None

    @app.context_processor
    def inject_globals():
        return {
            "current_user": g.get("user"),
            "app_name": app.config["APP_NAME"],
        }

    @app.errorhandler(404)
    def page_not_found(_error):
        return render_template("404.html"), 404

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
