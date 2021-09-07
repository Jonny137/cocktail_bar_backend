from flask import Flask
from flask_cors import CORS
import logging.config

from config import Config
from server.extensions import jwt, db, migrate
from server.logger.log_config import LOG_CONFIG

logging.config.dictConfig(LOG_CONFIG)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app,
         resources={r'/*': {'origins': app.config.get('FRONTEND_URL')}},
         supports_credentials=True)

    db.init_app(app)
    migrate.init_app(app, db, compare_type=True)
    jwt.init_app(app)

    from server.error_handlers import bp as error_handlers_bp
    app.register_blueprint(error_handlers_bp)

    from server.api.cocktail import bp as api_cocktail_bp
    app.register_blueprint(api_cocktail_bp, url_prefix='/cocktail')

    from server.api.admin import bp as api_admin_bp
    app.register_blueprint(api_admin_bp, url_prefix='/admin')

    from server.api.user import bp as api_user_bp
    app.register_blueprint(api_user_bp, url_prefix='/user')

    return app


from server import models # noqa
