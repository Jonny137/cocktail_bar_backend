from flask import request
from flask_jwt_extended import jwt_required

from server.api.user import bp
from server.api.user.handlers import (register_user, user_login, user_logout,
                                      add_favorite, get_favorite_cocktails,
                                      remove_favorite_cocktail)


@bp.route('/register', methods=['POST'])
def register():
    if request.is_json:
        data = request.get_json()
        result = register_user(data)

        return {'message': result.to_dict()}


@bp.route('/login', methods=['POST'])
def login():
    if request.is_json:
        data = request.get_json()
        token = user_login(data)

        return {'message': token}


@bp.route('/logout', methods=['PUT'])
@jwt_required
def logout():
    encoded_token = request.headers.get('Authorization')
    result = user_logout(encoded_token)

    return {'message': result}


# Remove account and it's connected data
# @bp.route('/revoke', methods=['DELETE'])
# @jwt_required
# def revoke():
#     pass


@bp.route('/favorite', methods=['POST'])
@jwt_required
def set_favorite():
    if request.is_json:
        data = request.get_json()

        return {'message': add_favorite(data)}


@bp.route('/favorite')
@jwt_required
def get_favorite():
    return {
        'message': get_favorite_cocktails()
    }


@bp.route('/favorite', methods=['DELETE'])
@jwt_required
def remove_favorite():
    if request.is_json:
        data = request.get_json()

        return {
            'message': remove_favorite_cocktail(data)
        }
