from flask import request
from flask_jwt_extended import jwt_required, decode_token
from server.api.user import bp
from server.api.user.handlers import (register_user,
                                      login,
                                      logout,
                                      get_admin_panel_data)
from server.jwt.jwt_util import is_token_revoked
from server.extensions import jwt


@jwt.token_in_blacklist_loader
def check_if_token_revoked(decoded_token):
    return is_token_revoked(decoded_token)


@bp.route('/admin/token')
@jwt_required
def check_if_token_valid():
    token = request.headers.get('Authorization')
    token_id = token.split(' ', 1)[1]
    decoded_token = decode_token(token_id)
    result = is_token_revoked(decoded_token)

    return {'message': not result}


@bp.route('/admin/register', methods=['POST'])
def add_new_user():
    if request.is_json:
        data = request.get_json()
        result = register_user(data)

        return {'message': result.to_dict}


@bp.route('/admin/login', methods=['POST'])
def user_login():
    if request.is_json:
        data = request.get_json()
        token = login(data)

        return {'message': token}


@bp.route('/admin/logout', methods=['PUT'])
@jwt_required
def user_logout():
    encoded_token = request.headers.get('Authorization')
    result = logout(encoded_token)

    return {'message': result}


@bp.route('/admin/data')
@jwt_required
def get_admin_data():
    result = get_admin_panel_data()

    return {'message': result}
