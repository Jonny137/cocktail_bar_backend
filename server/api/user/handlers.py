from sqlalchemy import exc
from flask import abort, current_app
from sqlalchemy.orm.exc import NoResultFound, FlushError
from flask_jwt_extended import (create_access_token,
                                create_refresh_token,
                                get_jwt_identity,
                                decode_token)

from server.jwt.jwt_util import add_token_to_database, revoke_token
from server import db
from server.models import User, Cocktail


def register_user(user_info):
    keys = list(user_info.keys())

    if 'username' not in keys or 'password' not in keys or 'email' not in keys:
        abort(400, 'Invalid request')

    if db.session.query(User).filter(User.email == user_info['email']).first():
        abort(400, 'Email is already in use')

    new_user = User(username=user_info['username'], email=user_info['email'])
    new_user.set_password(user_info['password'])

    try:
        db.session.add(new_user)
        db.session.commit()
    except exc.IntegrityError:
        abort(400, 'User already exists')
    except exc.SQLAlchemyError:
        abort(500, 'Internal server error')

    return new_user


def user_login(user_info):
    keys = list(user_info.keys())

    if 'username' not in keys or 'password' not in keys:
        abort(400, 'Invalid request')

    user = User.query.filter_by(username=user_info['username']).first()

    if not user:
        abort(401, 'User does not exist')

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


def user_logout(token_id):
    user_identity = get_jwt_identity()
    token_id = token_id.split(' ', 1)[1]
    jti = decode_token(token_id)['jti']

    try:
        revoke_token(jti, user_identity)
        return 'Logout successful'
    except NoResultFound:
        abort(401, 'Logout unsuccessful, no token')
    except exc.SQLAlchemyError:
        abort(500, 'Logout unsuccessful, internal error')


def add_favorite(data):
    user_identity = get_jwt_identity()
    user = db.session.query(User).filter(User.id == user_identity).first()

    cocktail = db.session \
        .query(Cocktail) \
        .filter(Cocktail.name == data['name']) \
        .first()

    try:
        user.favorites.append(cocktail)
        db.session.commit()
    except FlushError:
        abort(500, 'Internal server error')

    return {'user': user.to_dict(), 'cocktail': cocktail.to_dict()}


def get_favorite_cocktails():
    user_identity = get_jwt_identity()
    user = db.session.query(User).filter(User.id == user_identity).first()

    return [cocktail.to_dict() for cocktail in user.favorites]


def remove_favorite_cocktail(data):
    user_identity = get_jwt_identity()
    user = db.session.query(User).filter(User.id == user_identity).first()

    cocktail = db.session \
        .query(Cocktail) \
        .filter(Cocktail.name == data['name']) \
        .first()

    user.favorites.remove(cocktail)
    db.session.commit()

    return cocktail.to_dict()
