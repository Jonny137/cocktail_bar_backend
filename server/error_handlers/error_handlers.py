from flask import abort, jsonify, make_response
from server import db
from server.error_handlers import bp


BAD_REQUEST = 400
UNAUTHORIZED = 401
FORBIDDEN = 403
NOT_FOUND = 404
INTERNAL_SERVER_ERROR = 500

ERROR_MESSAGES = {
    BAD_REQUEST: 'Bad Request',
    UNAUTHORIZED: 'Unauthorized',
    FORBIDDEN: 'Forbidden',
    NOT_FOUND: 'Not Found',
    INTERNAL_SERVER_ERROR: 'Internal Server Error',
}


def get_error_response(error, http_code):
        response = make_response(
            jsonify({
                'message': error.description['message'] or 'message',
                'status': error.description['status'] or 'status',
                'status_code': http_code or 404
            }),
            http_code
        )
        return response


@bp.app_errorhandler(BAD_REQUEST)
def bad_request_error(error):
    return get_error_response(error, BAD_REQUEST)


@bp.app_errorhandler(UNAUTHORIZED)
def unauthorized_error(error):
    return get_error_response(error, UNAUTHORIZED)


@bp.app_errorhandler(FORBIDDEN)
def forbidden_error(error):
    return get_error_response(error, FORBIDDEN)


@bp.app_errorhandler(NOT_FOUND)
def not_found_error(error):
    return get_error_response(error, NOT_FOUND)


@bp.app_errorhandler(INTERNAL_SERVER_ERROR)
def internal_error(error):
    return get_error_response(error, INTERNAL_SERVER_ERROR)


def throw_exception(http_code, message='', rollback=False):
    if rollback:
        db.session.rollback()

    abort(
        http_code,
        description={
            'status': ERROR_MESSAGES[http_code],
            'message': message
        }
    )
