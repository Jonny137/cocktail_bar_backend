from flask import request
from flask_jwt_extended import jwt_required, decode_token
from server.api.admin import bp
from server.api.admin.handlers import (register_admin,
                                       admin_login,
                                       admin_logout,
                                       get_admin_panel_data)
from server.jwt.jwt_util import is_token_revoked
from server.extensions import jwt


@jwt.token_in_blacklist_loader
def check_if_token_revoked(decoded_token):
    return is_token_revoked(decoded_token)


@bp.route('/token')
@jwt_required
def check_if_token_valid():
    token = request.headers.get('Authorization')
    token_id = token.split(' ', 1)[1]
    decoded_token = decode_token(token_id)
    result = is_token_revoked(decoded_token)

    return {'message': not result}


@bp.route('/register', methods=['POST'])
def register():
    if request.is_json:
        data = request.get_json()
        result = register_admin(data)

        return {'message': result.to_dict()}


@bp.route('/login', methods=['POST'])
def login():
    if request.is_json:
        data = request.get_json()
        token = admin_login(data)

        return {'message': token}


@bp.route('/logout', methods=['PUT'])
@jwt_required
def logout():
    encoded_token = request.headers.get('Authorization')
    result = admin_logout(encoded_token)

    return {'message': result}


@bp.route('/data')
@jwt_required
def get_admin_data():
    result = get_admin_panel_data()

    return {'message': result}
