import re
from functools import wraps
from flask import request

from server.error_handlers.error_handlers import (
    throw_exception,
    BAD_REQUEST,
    UNAUTHORIZED
)


def user_required(f):
    @wraps(f)
    def check_user_header(*args, **kwargs):
        user = request.headers.get('X-Username')

        if not user:
            throw_exception(UNAUTHORIZED, 110)

        valid_user = re.match('^[a-zA-Z0-9_]{4,32}$', user)

        if not valid_user:
            throw_exception(BAD_REQUEST, 100)

        kwargs['user'] = user
        return f(*args, **kwargs)

    return check_user_header
