import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.associationproxy import association_proxy
from werkzeug.security import generate_password_hash, check_password_hash

from server import db


class AdminUser(db.Model):
    __tablename__ = 'admin'

    id = db.Column(UUID(as_uuid=True),
                   primary_key=True,
                   default=uuid.uuid4,
                   unique=True,
                   nullable=False)
    username = db.Column(db.String(255),
                         unique=True,
                         index=True,
                         nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<AdminUser {self.id} {self.username}>'

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password
        }


# Association table for user favorites cocktails
cocktail_favorites = db.Table(
    'cocktail_favorites',
    db.Column('user_id',
              UUID(as_uuid=True),
              db.ForeignKey('user.id'),
              primary_key=True),
    db.Column('cocktail_id',
              UUID(as_uuid=True),
              db.ForeignKey('cocktail.id'),
              primary_key=True)
)


class UserRatings(db.Model):
    __tablename__ = 'user_ratings'

    id = db.Column(UUID(as_uuid=True),
                   primary_key=True,
                   default=uuid.uuid4,
                   unique=True,
                   nullable=False)
    cocktail_id = db.Column(UUID(as_uuid=True),
                            db.ForeignKey('cocktail.id'),
                            primary_key=True)
    cocktail = db.relationship('Cocktail',
                               backref=db.backref('user_ratings',
                                                  cascade='all, delete-orphan')
                               )
    user_id = db.Column(UUID(as_uuid=True),
                        db.ForeignKey('user.id'),
                        primary_key=True)
    user = db.relationship('User',
                           backref=db.backref('user_ratings',
                                              cascade='all, delete-orphan'))
    rating = db.Column(db.Integer())

    def __init__(self,
                 cocktail=None,
                 user=None,
                 rating=None):
        self.cocktail = cocktail
        self.user = user
        self.rating = rating

    def __repr__(self):
        return f'<User_Rating {self.id}>'


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(UUID(as_uuid=True),
                   primary_key=True,
                   default=uuid.uuid4,
                   unique=True,
                   nullable=False)
    username = db.Column(db.String(255),
                         unique=True,
                         index=True,
                         nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    favorites = db.relationship('Cocktail',
                                secondary=cocktail_favorites,
                                backref=db.backref('users', uselist=False))
    rated_cocktails = association_proxy('user_ratings',
                                        'cocktail',
                                        creator=lambda c: CocktailIngredients(
                                            cocktail=c))

    def __repr__(self):
        return f'<User id:{self.id} name:{self.username}>'

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }


class CocktailIngredients(db.Model):
    __tablename__ = 'cocktail_ingredients'

    id = db.Column(UUID(as_uuid=True),
                   primary_key=True,
                   default=uuid.uuid4,
                   unique=True,
                   nullable=False)
    cocktail_id = db.Column(UUID(as_uuid=True),
                            db.ForeignKey('cocktail.id'),
                            primary_key=True)
    cocktail = db.relationship('Cocktail',
                               backref=db.backref('cocktail_ingredients',
                                                  cascade='all, delete-orphan')
                               )
    ingredient_id = db.Column(UUID(as_uuid=True),
                              db.ForeignKey('ingredient.id'), primary_key=True)
    ingredient = db.relationship('Ingredient',
                                 backref=db.backref('cocktail_ingredients',
                                                    cascade='all, '
                                                            'delete-orphan'))
    amount = db.Column(db.String(255))
    main = db.Column(db.Boolean, default=False)

    def __init__(self,
                 cocktail=None,
                 ingredient=None,
                 amount=None,
                 main=False):
        self.cocktail = cocktail
        self.ingredient = ingredient
        self.amount = amount
        self.main = main

    def __repr__(self):
        return f'<Cocktail_Ingredients {self.id}>'


class Cocktail(db.Model):
    __tablename__ = 'cocktail'

    id = db.Column(UUID(as_uuid=True),
                   primary_key=True,
                   default=uuid.uuid4,
                   unique=True,
                   nullable=False)
    name = db.Column(db.String(255), nullable=False)
    preparation = db.Column(db.String())
    garnish = db.Column(db.String(255))
    glassware_id = db.Column(UUID(as_uuid=True), db.ForeignKey('glassware.id'))
    method_id = db.Column(UUID(as_uuid=True), db.ForeignKey('method.id'))
    img_url = db.Column(db.String(), default='')
    total_rating = db.Column(db.Float(), default=0)
    num_of_ratings = db.Column(db.Integer(), default=0)
    ingredients = association_proxy('cocktail_ingredients',
                                    'ingredient',
                                    creator=lambda i: CocktailIngredients(
                                        ingredient=i))
    rating = association_proxy('user_ratings',
                               'user',
                               creator=lambda u: UserRatings(user=u))

    def __repr__(self):
        return f'<Cocktail {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'preparation': self.preparation,
            'garnish': self.garnish,
            'method': self.method.name,
            'glassware': self.glassware.name,
            'img_url': self.img_url,
            'ingredients': [{
                'name': ing.ingredient.name,
                'amount': ing.amount,
                'main': ing.main
            } for ing in self.cocktail_ingredients]
        }


class Ingredient(db.Model):
    __tablename__ = 'ingredient'

    id = db.Column(UUID(as_uuid=True),
                   primary_key=True,
                   default=uuid.uuid4,
                   unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False, unique=True)
    type = db.Column(db.String(255), nullable=False)
    cocktails = association_proxy('cocktail_ingredients', 'cocktail',
                                  creator=lambda c: CocktailIngredients(
                                      cocktail=c))

    def __repr__(self):
        return f'<Ingredient {self.name}>'


class Method(db.Model):
    __tablename__ = 'method'

    id = db.Column(UUID(as_uuid=True),
                   primary_key=True,
                   default=uuid.uuid4,
                   unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False, unique=True)
    cocktails = db.relationship('Cocktail',
                                backref='method',
                                lazy='dynamic')

    def __repr__(self):
        return f'<Method {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Glassware(db.Model):
    __tablename__ = 'glassware'

    id = db.Column(UUID(as_uuid=True),
                   primary_key=True,
                   default=uuid.uuid4,
                   unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False, unique=True)
    cocktails = db.relationship('Cocktail',
                                backref='glassware',
                                lazy='dynamic')

    def __repr__(self):
        return f'<Glassware {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }


# Token helper model
class TokenBlacklist(db.Model):
    id = db.Column(UUID(as_uuid=True),
                   primary_key=True,
                   default=uuid.uuid4,
                   unique=True,
                   nullable=False)
    jti = db.Column(db.String(36), nullable=False)
    token_type = db.Column(db.String(10), nullable=False)
    user_identity = db.Column(db.String(50), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False)
    expires = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            'token_id': self.id,
            'jti': self.jti,
            'token_type': self.token_type,
            'user_identity': self.user_identity,
            'revoked': self.revoked,
            'expires': self.expires
        }
