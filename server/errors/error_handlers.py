from flask import jsonify, make_response
from server import db
from server.errors import bp


def get_error_response(error, code):
    response = make_response(jsonify(
        {'message': error.description, 'status': code, }), code)
    return response


@bp.app_errorhandler(400)
def user_input_error(error):
    db.session.rollback()
    return get_error_response(error, 400)


@bp.app_errorhandler(401)
def unauthorized_error(error):
    return get_error_response(error, 401)


@bp.app_errorhandler(404)
def not_found_error(error):
    db.session.rollback()
    return get_error_response(error, 404)


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return get_error_response(error, 500)
