from flask import request
from flask_jwt_extended import jwt_required

from server.api.decorators import find_user
from server.api.user import bp
from server.api.user.handlers import (register_user, user_login, user_logout,
                                      add_favorite, get_favorite_cocktails,
                                      remove_favorite_cocktail, rate_cocktail,
                                      remove_account)


@bp.route('/register', methods=['POST'])
def register():
    if request.is_json:
        data = request.get_json()
        result = register_user(data)

        return {'message': result}


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


@bp.route('/remove_account', methods=['DELETE'])
@jwt_required
@find_user
def revoke(user):
    return {'message': remove_account(user)}


@bp.route('/favorite', methods=['POST'])
@jwt_required
@find_user
def set_favorite(user):
    if request.is_json:
        data = request.get_json()

        return {'message': add_favorite(data, user)}


@bp.route('/favorite')
@jwt_required
@find_user
def get_favorite(user):
    return {
        'message': get_favorite_cocktails(user)
    }


@bp.route('/favorite', methods=['DELETE'])
@jwt_required
@find_user
def remove_favorite(user):
    if request.is_json:
        data = request.get_json()

        return {
            'message': remove_favorite_cocktail(data, user)
        }


@bp.route('/rate', methods=['PATCH'])
@jwt_required
@find_user
def set_cocktail_rating(user):
    if request.is_json:
        data = request.get_json()

        result = rate_cocktail(data, user)

        return {'message': result}
