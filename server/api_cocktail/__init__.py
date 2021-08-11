from flask import Blueprint

bp = Blueprint('api_cocktail', __name__)

from server.api_cocktail import routes
