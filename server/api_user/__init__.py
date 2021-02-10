from flask import Blueprint

bp = Blueprint('api_user', __name__)

from server.api_user import routes