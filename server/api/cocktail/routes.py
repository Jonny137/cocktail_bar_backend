from flask import request
from flask_jwt_extended import jwt_required
from server.api.cocktail import bp
from server.api.cocktail.handlers import (add_cocktail, get_cocktail,
                                          find_cocktails, get_filters,
                                          delete_cocktail, edit_cocktail,
                                          rate_cocktail)


@bp.route('/', methods=['POST'])
@jwt_required
def add_new_cocktail():
    if request.is_json:
        data = request.get_json()
        result = add_cocktail(data)

        return {'message': result.to_dict()}


@bp.route('/<cocktail_id>')
def get_single_cocktail(cocktail_id):
    result = get_cocktail(cocktail_id)
    return {'message': result.to_dict()}


@bp.route('/<cocktail_id>', methods=['DELETE'])
@jwt_required
def delete_single_cocktail(cocktail_id):
    result = delete_cocktail(cocktail_id)

    return {'message': 'Deleted cocktail id: {}'.format(result)}


@bp.route('/<cocktail_id>', methods=['PUT'])
@jwt_required
def edit_single_cocktail(cocktail_id):
    if request.is_json:
        data = request.get_json()
        result = edit_cocktail(cocktail_id, data)

        return {'message': result.to_dict()}


@bp.route('/retrieve')
def filter_cocktails():
    cocktails, total = find_cocktails(request.args)

    result = [cocktail[0].to_dict() for cocktail in cocktails]

    return {
        'message': {
            'cocktails': result,
            'total': total
        }
    }


@bp.route('/filters')
def filters():
    result = get_filters()

    return {'message': result}


@bp.route('/rate', methods=['PATCH'])
@jwt_required
def set_cocktail_rating():
    if request.is_json:
        data = request.get_json()

        result = rate_cocktail(data)

        return {'message': result}
