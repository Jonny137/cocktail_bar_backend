import os


class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT')
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    JWT_ACCESS_TOKEN_EXPIRES = 7200
    CORS_HEADERS = 'Content-Type'
    FRONTEND_URL = os.environ.get('FRONTEND_URL')
    # Mail settings
    MAIL_DEFAULT_SENDER = 'from@example.com'
    MAIL_SERVER = 'smtp.mailtrap.io'
    MAIL_PORT = 2525
    MAIL_USERNAME = '3872c33ec8eaf9'
    MAIL_PASSWORD = 'a700653a58310c'
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_DEBUG = False
