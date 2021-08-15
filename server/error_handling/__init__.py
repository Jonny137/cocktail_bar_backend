from flask import Blueprint

bp = Blueprint('error_handling', __name__)

from server.error_handling import error_handlers
