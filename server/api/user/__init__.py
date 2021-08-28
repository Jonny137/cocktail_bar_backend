from flask import Blueprint

bp = Blueprint('user', __name__)

from server.api.user import routes # noqa