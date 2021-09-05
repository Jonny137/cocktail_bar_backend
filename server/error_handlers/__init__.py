from flask import Blueprint

bp = Blueprint('error_handlers', __name__)

from server.error_handlers import error_handlers
