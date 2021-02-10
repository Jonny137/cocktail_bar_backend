from flask import Flask
from flask_cors import CORS

from config import Config
from server.extensions import jwt, db, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, 
         resources={r'/*': {'origins': app.config.get('FRONTEND_URL')}},
         supports_credentials=True
    )

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from server.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from server.api_cocktail import bp as api_cocktail_bp
    app.register_blueprint(api_cocktail_bp)

    from server.api_user import bp as api_user_bp
    app.register_blueprint(api_user_bp)

    return app


from server import models
