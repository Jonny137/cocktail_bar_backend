from sqlalchemy import exc
from flask import current_app
from sqlalchemy.orm.exc import NoResultFound, FlushError
from flask_jwt_extended import (create_access_token,
                                create_refresh_token,
                                get_jwt_identity,
                                decode_token)

from server.jwt.jwt_util import add_token_to_database, revoke_token
from server import db
from server.models import User, Cocktail, UserRatings
from server.error_handlers.error_handlers import (throw_exception,
                                                  INTERNAL_SERVER_ERROR,
                                                  BAD_REQUEST, UNAUTHORIZED,
                                                  FORBIDDEN, NOT_FOUND)


def register_user(user_info):
    keys = list(user_info.keys())

    if 'username' not in keys or 'password' not in keys or 'email' not in keys:
        throw_exception(BAD_REQUEST, 'Invalid request.')

    if db.session.query(User).filter(User.email == user_info['email']).first():
        throw_exception(BAD_REQUEST, 'Email is already in use.')

    new_user = User(username=user_info['username'], email=user_info['email'])
    new_user.set_password(user_info['password'])

    try:
        db.session.add(new_user)
        db.session.commit()
    except exc.IntegrityError:
        throw_exception(BAD_REQUEST, 'User already exists.', True)
    except exc.SQLAlchemyError:
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)

    return new_user.to_dict()


def user_login(user_info):
    keys = list(user_info.keys())

    if 'username' not in keys or 'password' not in keys:
        throw_exception(BAD_REQUEST, 'Invalid request.')

    user = User.query.filter_by(username=user_info['username']).first()

    if not user:
        throw_exception(UNAUTHORIZED, 'User does not exist.')

    if not user.check_password(user_info['password']):
        throw_exception(FORBIDDEN, 'Invalid credentials.')

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
        throw_exception(UNAUTHORIZED, 'No token.', True)
    except exc.SQLAlchemyError:
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)


def remove_account():
    user_identity = None

    try:
        user_identity = get_jwt_identity()
        user = db.session.query(User).filter(User.id == user_identity).first()
        db.session.delete(user)
        db.session.commit()
    except exc.DataError:
        throw_exception(BAD_REQUEST, 'Invalid user.', True)
    except exc.SQLAlchemyError:
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)

    return user_identity


def add_favorite(data, user):
    if not user:
        throw_exception(NOT_FOUND, 'User does not exist.')

    cocktail = db.session \
        .query(Cocktail) \
        .filter(Cocktail.name == data['name']) \
        .first()

    try:
        user.favorites.append(cocktail)
        db.session.commit()
    except FlushError:
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)

    return {'user': user.to_dict(), 'cocktail': cocktail.to_dict()}


def get_favorite_cocktails(user):
    if not user:
        throw_exception(NOT_FOUND, 'User does not exist.')

    return [cocktail.to_dict() for cocktail in user.favorites]


def remove_favorite_cocktail(data, user):
    if not user:
        throw_exception(NOT_FOUND, 'User does not exist.')

    cocktail = None

    try:
        cocktail = db.session \
            .query(Cocktail) \
            .filter(Cocktail.name == data['name']) \
            .first()

        user.favorites.remove(cocktail)
        db.session.commit()
    except exc.DataError:
        throw_exception(BAD_REQUEST, 'Cocktail not found.', True)
    except exc.SQLAlchemyError:
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)

    return cocktail.to_dict()


def rate_cocktail(data, user):
    if not user:
        throw_exception(NOT_FOUND, 'User does not exist.')

    cocktail = None

    try:
        cocktail = db.session \
            .query(Cocktail) \
            .filter(Cocktail.name == data['name']) \
            .first()
    except exc.DataError:
        throw_exception(BAD_REQUEST, 'Cocktail not found.', True)

    if int(data['old_rating']) == 0:
        cocktail.total_rating = (
                (cocktail.total_rating * cocktail.num_of_ratings +
                 data['new_rating']) / (cocktail.num_of_ratings + 1))
        cocktail.num_of_ratings += 1
        db.session.add(UserRatings(cocktail, user, data['new_rating']))
    else:
        cocktail.total_rating = (
                (cocktail.total_rating * cocktail.num_of_ratings +
                 data['new_rating'] - data['old_rating']) /
                cocktail.num_of_ratings)

        new_user_rating = db.session.query(UserRatings).filter(
            user.to_dict()['id'] == UserRatings.user_id).first()
        new_user_rating.user_rating = data['new_rating']

    db.session.commit()

    return cocktail.to_dict()
