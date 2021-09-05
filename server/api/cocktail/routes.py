from flask import request
from flask_jwt_extended import jwt_required, jwt_optional
from server.api.cocktail import bp
from server.api.cocktail.handlers import (add_cocktail, get_cocktail,
                                          find_cocktails, get_filters,
                                          delete_cocktail, edit_cocktail)


@bp.route('', methods=['POST'])
@jwt_required
def add_new_cocktail():
    if request.is_json:
        data = request.get_json()

        return {'message': add_cocktail(data)}


@bp.route('/<cocktail_id>')
@jwt_optional
def get_single_cocktail(cocktail_id):
    return {'message': get_cocktail(cocktail_id)}


@bp.route('/<cocktail_id>', methods=['DELETE'])
@jwt_required
def delete_single_cocktail(cocktail_id):
    return {'message': f'Deleted cocktail id: {delete_cocktail(cocktail_id)}'}


@bp.route('/<cocktail_id>', methods=['PUT'])
@jwt_required
def edit_single_cocktail(cocktail_id):
    if request.is_json:
        data = request.get_json()

        return {'message': edit_cocktail(cocktail_id, data)}


@bp.route('/retrieve')
def filter_cocktails():
    cocktails, total = find_cocktails(request.args)

    return {
        'message': {
            'cocktails': cocktails,
            'total': total
        }
    }


@bp.route('/filters')
def filters():
    return {'message': get_filters()}
