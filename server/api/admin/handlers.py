from sqlalchemy import exc
from flask import abort, current_app
from sqlalchemy.orm.exc import NoResultFound
from flask_jwt_extended import (create_access_token,
                                create_refresh_token,
                                get_jwt_identity,
                                decode_token)

from server.jwt.jwt_util import add_token_to_database, revoke_token
from server import db
from server.models import Cocktail, Ingredient, Glassware, Method, AdminUser


def register_admin(user_info):
    keys = list(user_info.keys())

    if 'username' not in keys or 'password' not in keys:
        abort(400, 'Invalid request')

    new_user = AdminUser(username=user_info['username'])
    new_user.set_password(user_info['password'])

    try:
        db.session.add(new_user)
        db.session.commit()
    except exc.IntegrityError:
        abort(400, 'Admin user already exists')
    except exc.SQLAlchemyError:
        abort(500, 'Internal server error')

    return new_user


def admin_login(user_info):
    keys = list(user_info.keys())

    if 'username' not in keys or 'password' not in keys:
        abort(400, 'Invalid request')

    user = AdminUser.query.filter_by(username=user_info['username']).first()

    if not user:
        abort(401, 'Admin user does not exist')

    if not user.check_password(user_info['password']):
        abort(403, 'Invalid credentials')

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    add_token_to_database(
        access_token, current_app.config['JWT_IDENTITY_CLAIM'])
    add_token_to_database(
        refresh_token, current_app.config['JWT_IDENTITY_CLAIM'])

    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }


def admin_logout(token_id):
    user_identity = get_jwt_identity()
    token_id = token_id.split(' ', 1)[1]
    jti = decode_token(token_id)['jti']

    try:
        revoke_token(jti, user_identity)
        return 'Logout successful'
    except NoResultFound:
        abort(401, 'Logout unsuccessful, no token.')
    except exc.SQLAlchemyError:
        abort(500, 'Logout unsuccessful, internal error.')


def get_admin_panel_data():
    data = {}

    try:
        cocktails = db.session.query(Cocktail.name).order_by(
            Cocktail.name).all()
        glassware = db.session.query(Glassware.name).order_by(
            Glassware.name).all()
        method = db.session.query(Method.name).order_by(Method.name).all()
        garnish = db.session.query(Cocktail.garnish).distinct(
            Cocktail.garnish).all()
        ingredients = db.session.query(Ingredient.name).order_by(
            Ingredient.name).all()

        data = {
            'name': [c for (c, ) in cocktails],
            'glassware': [gl for (gl, ) in glassware],
            'method': [m for (m, ) in method],
            'garnish': [ga for (ga, ) in garnish],
            'ingredients': [i for (i, ) in ingredients],
        }
    except exc.SQLAlchemyError:
        abort(500, 'Internal server error')

    return data