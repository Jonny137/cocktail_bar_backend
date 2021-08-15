from flask import Blueprint

bp = Blueprint('cocktail', __name__)

from server.api.cocktail import routes # noqa
