import logging
import datetime
from sqlalchemy import exc
from flask import current_app, url_for, render_template
from sqlalchemy.orm.exc import NoResultFound, FlushError
from flask_jwt_extended import (create_access_token,
                                create_refresh_token,
                                get_jwt_identity,
                                decode_token)

from server.api.user.email import send_email
from server.api.user.verify_token import generate_confirmation_token, \
    confirm_token
from server.jwt.jwt_util import add_token_to_database, revoke_token
from server import db
from server.models import User, Cocktail, UserRatings
from server.error_handlers.error_handlers import (throw_exception,
                                                  INTERNAL_SERVER_ERROR,
                                                  BAD_REQUEST, UNAUTHORIZED,
                                                  FORBIDDEN, NOT_FOUND)

VERIFY_MAIL_SUBJECT = '[Den of Thieves] Please confirm your email'
logger = logging.getLogger(__name__)


def register_user(user_info):
    keys = list(user_info.keys())

    logger.info('Registering new user.')

    if 'username' not in keys or 'password' not in keys or 'email' not in keys:
        logger.debug('Missing parameters for registration.')
        throw_exception(BAD_REQUEST, 'Invalid request.')

    if db.session.query(User).filter(User.email == user_info['email']).first():
        throw_exception(BAD_REQUEST, 'Email is already in use.')

    new_user = User(username=user_info['username'], email=user_info['email'])
    new_user.set_password(user_info['password'])

    try:
        db.session.add(new_user)
        db.session.commit()
    except exc.IntegrityError as err:
        logger.debug('Duplicated user.', err)
        throw_exception(BAD_REQUEST, 'User already exists.', True)
    except exc.SQLAlchemyError as err:
        logger.debug(f'SQL error during user {user_info} registration', err)
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)

    logger.info('New user successfully registered.')

    token = generate_confirmation_token(new_user.email)
    logger.info('New user verification token generated.')
    confirm_url = url_for('user.confirm_email', token=token, _external=True)
    html = render_template('user/activate.html', confirm_url=confirm_url)
    send_email(new_user.email, VERIFY_MAIL_SUBJECT, html)
    logger.info('Verification email sent.')

    return new_user.to_dict()


def confirm_user_email(token):
    email = None

    try:
        logger.info('Trying to confirm verification token.')
        email = confirm_token(token)
    except Exception as err:
        logger.debug('Error during token confirmation', err)
        throw_exception(BAD_REQUEST,
                        'The confirmation link is invalid or has expired.')

    user = User.query.filter_by(email=email).first()

    if not user:
        throw_exception(INTERNAL_SERVER_ERROR, 'User not found.')

    if user.confirmed:
        logger.info('User already confirmed.')
        return 'Account already confirmed. Please login.'
    else:
        user.confirmed = True
        user.confirmed_on = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()

    logger.info('User successfully confirmed.')
    return 'Account successfully confirmed.'


def resend_confirmation_email(user):
    token = generate_confirmation_token(user.email)
    confirm_url = url_for('user.confirm_email', token=token, _external=True)
    html = render_template('user/activate.html', confirm_url=confirm_url)
    send_email(user.email, VERIFY_MAIL_SUBJECT, html)
    logger.info('A new confirmation email has been sent.')

    return 'New confirmation email sent.'


def user_login(user_info):
    keys = list(user_info.keys())
    logger.info('Logging in user.')

    if 'username' not in keys or 'password' not in keys:
        throw_exception(BAD_REQUEST, 'Invalid request.')

    user = User.query.filter_by(username=user_info['username']).first()

    if not user:
        throw_exception(UNAUTHORIZED, 'User does not exist.')

    if not user.check_password(user_info['password']):
        logger.debug('Password is not correct.')
        throw_exception(FORBIDDEN, 'Invalid credentials.')

    if not user.confirmed:
        throw_exception(FORBIDDEN, 'User not verified.')

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    add_token_to_database(
        access_token, current_app.config['JWT_IDENTITY_CLAIM'])
    add_token_to_database(
        refresh_token, current_app.config['JWT_IDENTITY_CLAIM'])

    logger.info('User successfully logged in.')
    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }


def user_logout(token_id):
    user_identity = get_jwt_identity()
    token_id = token_id.split(' ', 1)[1]
    jti = decode_token(token_id)['jti']
    logger.info('Logging out user.')

    try:
        revoke_token(jti, user_identity)
        logger.info('User successfully logged out.')
        return 'Logout successful'
    except NoResultFound as err:
        logger.debug('User token non existent', err)
        throw_exception(UNAUTHORIZED, 'No token.', True)
    except exc.SQLAlchemyError as err:
        logger.debug('SQL error during logout.', err)
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)


def remove_account(user):
    logger.info('Revoking user account.')
    try:
        db.session.delete(user)
        db.session.commit()
    except exc.DataError as err:
        logger.debug('Error during account revoking.', err)
        throw_exception(BAD_REQUEST, 'Invalid user.', True)
    except exc.SQLAlchemyError as err:
        logger.debug('SQL Error during account revoking.', err)
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)

    logger.info('User account successfully revoked.')

    return 'User account revoked.'


def add_favorite(data, user):
    if not user:
        throw_exception(NOT_FOUND, 'User does not exist.')

    logger.info(f'Adding new favorite cocktail {data} for user {user}')

    cocktail = db.session \
        .query(Cocktail) \
        .filter(Cocktail.name == data['name']) \
        .first()

    try:
        user.favorites.append(cocktail)
        db.session.commit()
    except FlushError:
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)

    logger.info(
        f'New favorite cocktail {data} for user {user} successfully added.')

    return {'user': user.to_dict(), 'cocktail': cocktail.to_dict()}


def get_favorite_cocktails(user):
    logger.info(f'Fetching favorite cocktails for user: {user}')

    if not user:
        throw_exception(NOT_FOUND, 'User does not exist.')

    logger.info(f'Favorite cocktails for user {user} successfully fetched.')

    return [cocktail.to_dict() for cocktail in user.favorites]


def remove_favorite_cocktail(data, user):
    if not user:
        throw_exception(NOT_FOUND, 'User does not exist.')

    logger.info(f'Removing favorite cocktail {data} for user: {user}')
    cocktail = None

    try:
        cocktail = db.session \
            .query(Cocktail) \
            .filter(Cocktail.name == data['name']) \
            .first()

        user.favorites.remove(cocktail)
        db.session.commit()
    except exc.DataError as err:
        logger.debug('Error during favorite cocktail removal.', err)
        throw_exception(BAD_REQUEST, 'Cocktail not found.', True)
    except exc.SQLAlchemyError as err:
        logger.debug('SQL Error during favorite cocktail removal.', err)
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)

    logger.info(
        f'Favorite cocktail {data} for user {user} successfully removed.')

    return cocktail.to_dict()


def rate_cocktail(data, user):
    if not user:
        throw_exception(NOT_FOUND, 'User does not exist.')

    cocktail = None
    logger.info(f'Rating new cocktail {data} for user {user}.')

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
    logger.info(f'Cocktail {data} successfully rated for user {user}.')

    return cocktail.to_dict()
