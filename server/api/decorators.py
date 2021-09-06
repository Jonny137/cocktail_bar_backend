from functools import wraps
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import exc

from server import db
from server.error_handlers.error_handlers import (throw_exception,
                                                  INTERNAL_SERVER_ERROR)
from server.models import User


def find_user(f):
    @wraps(f)
    def find_user_in_db(*args, **kwargs):
        user = None

        try:
            user_identity = get_jwt_identity()
            user = db.session\
                .query(User)\
                .filter(User.id == user_identity)\
                .first()
        except exc.SQLAlchemyError:
            throw_exception(INTERNAL_SERVER_ERROR)

        kwargs['user'] = user
        return f(*args, **kwargs)

    return find_user_in_db
