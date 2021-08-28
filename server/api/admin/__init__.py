from flask import Blueprint

bp = Blueprint('admin', __name__)

from server.api.admin import routes # noqa
