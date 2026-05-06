"""AHAA — Flask application factory."""
from flask import Flask
from config import get_settings
from routes.main import main_bp
from routes.api import api_bp


def create_app() -> Flask:
    cfg = get_settings()
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = cfg.FLASK_SECRET_KEY

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    return app


if __name__ == "__main__":
    cfg = get_settings()
    app = create_app()
    app.run(debug=cfg.FLASK_DEBUG, port=5000, threaded=True)
