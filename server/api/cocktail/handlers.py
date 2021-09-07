import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from sqlalchemy import func, exc, or_, and_

from server import db
from server.models import (Cocktail, Ingredient, Glassware, Method,
                           UserRatings)
from server.error_handlers.error_handlers import (throw_exception,
                                                  INTERNAL_SERVER_ERROR,
                                                  BAD_REQUEST, NOT_FOUND)

cloudinary.config(
    cloud_name=os.environ.get('CLD_NAME'),
    api_key=os.environ.get('CLD_API_KEY'),
    api_secret=os.environ.get('CLD_API_SECRET')
)


def add_ingredient(data):
    new_ingredient = Ingredient(name=data['name'], type=data['type'])

    try:
        db.session.add(new_ingredient)
        db.session.commit()
    except exc.SQLAlchemyError:
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)

    return new_ingredient


def add_glassware(name):
    new_glassware = Glassware(name=name)

    try:
        db.session.add(new_glassware)
        db.session.commit()
    except exc.SQLAlchemyError:
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)

    return new_glassware


def add_method(name):
    new_method = Method(name=name)

    try:
        db.session.add(new_method)
        db.session.commit()
    except exc.SQLAlchemyError:
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)

    return new_method


def add_cocktail(data):
    new_cocktail = None
    ingredient_list = []
    glassware = None
    method = None
    new_img_url = ''

    duplicate = db.session.query(Cocktail).filter(
        Cocktail.name == data['name']).first()

    if duplicate:
        throw_exception(INTERNAL_SERVER_ERROR, 'Duplicated cocktail.')

    if 'ingredients' in list(data.keys()):
        for ing in data['ingredients']:
            instance = db.session.query(Ingredient).filter(
                Ingredient.name == ing['name']).first()
            if instance:
                ingredient_list.append(instance)
            else:
                ingredient_list.append(add_ingredient(ing))
    if 'glassware' in list(data.keys()):
        glassware = db.session.query(Glassware).filter(
            Glassware.name == data['glassware']).first()
        if not glassware:
            glassware = add_glassware(data['glassware'])

    if 'method' in list(data.keys()):
        method = db.session.query(Method).filter(
            Method.name == data['method']).first()
        if not method:
            method = add_method(data['method'])

    if 'image' in list(data.keys()):
        try:
            cocktail_img = cloudinary.uploader.upload(
                data['image']['url'],
                folder='cocktails/',
                public_id=data['image']['name']
            )
            new_img_url = cocktail_img['url']
        except cloudinary.exceptions.Error:
            throw_exception(INTERNAL_SERVER_ERROR)

    try:
        new_cocktail = Cocktail(
            name=data['name'],
            preparation=data['preparation'],
            garnish=data['garnish'],
            ingredients=ingredient_list,
            glassware_id=glassware.id,
            method_id=method.id
        )

        if new_img_url != '':
            new_cocktail.img_url = new_img_url

        for cocktail_ingredient in new_cocktail.cocktail_ingredients:
            ing = [i for i in data['ingredients']
                   if i['name'] == cocktail_ingredient.ingredient.name][0]
            cocktail_ingredient.amount = ing.get('amount')
            cocktail_ingredient.main = ing.get('main')

        db.session.add(new_cocktail)
        db.session.commit()

    except exc.DataError:
        throw_exception(BAD_REQUEST, 'Invalid admin user.')
    except exc.SQLAlchemyError:
        throw_exception(INTERNAL_SERVER_ERROR)

    return new_cocktail.to_dict()


def delete_cocktail(cocktail_id):
    try:
        cocktail = db.session.query(Cocktail).filter(
            Cocktail.id == cocktail_id).first()
        db.session.delete(cocktail)
        db.session.commit()

    except exc.DataError:
        throw_exception(BAD_REQUEST, 'Invalid cocktail name.')
    except exc.SQLAlchemyError:
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)

    return cocktail_id


def edit_cocktail(cocktail_id, data):
    cocktail = None
    ingredient_list = []
    cocktail_ings = []

    try:
        cocktail = db.session.query(Cocktail).filter(
            Cocktail.id == cocktail_id).first()

        if not cocktail:
            throw_exception(INTERNAL_SERVER_ERROR)

        if 'glassware' in list(data.keys()):
            glassware = db.session.query(Glassware).filter(
                Glassware.name == data['glassware']).first()
            if not glassware:
                glassware = add_glassware(data['glassware'])
            cocktail.glassware = glassware

        if 'method' in list(data.keys()):
            method = db.session.query(Method).filter(
                Method.name == data['method']).first()
            if not method:
                method = add_glassware(data['method'])
            cocktail.method = method

        if 'ingredients' in list(data.keys()):
            for ing in data['ingredients']:
                ingredient = db.session.query(Ingredient).filter(
                    Ingredient.name == ing['name']).first()
                if not ingredient:
                    ingredient = add_ingredient(ing)
                ingredient_list.append(ingredient)
            cocktail.ingredients = ingredient_list

        for cocktail_ingredient in cocktail.cocktail_ingredients:
            ing = [i for i in data['ingredients']
                   if i['name'] == cocktail_ingredient.ingredient.name][0]
            cocktail_ingredient.amount = ing.get('amount')
            cocktail_ingredient.main = ing.get('main')
            cocktail_ings.append(cocktail_ingredient)
        cocktail.cocktail_ingredients = cocktail_ings

        cocktail.name = data['name']
        cocktail.preparation = data['preparation']
        cocktail.garnish = data['garnish']

        db.session.commit()

    except exc.DataError:
        throw_exception(BAD_REQUEST, rollback=True)
    except exc.SQLAlchemyError:
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)
    return cocktail.to_dict()


def get_cocktail(cocktail_id, user):
    cocktail = None

    try:
        cocktail = db.session.query(Cocktail).filter(
            Cocktail.id == cocktail_id).first()
    except exc.DataError:
        throw_exception(BAD_REQUEST, 'Invalid cocktail name.')
    except exc.SQLAlchemyError:
        throw_exception(INTERNAL_SERVER_ERROR)

    if not cocktail:
        throw_exception(NOT_FOUND)
    else:
        data = cocktail.to_dict()
        if user:
            data['user_rating'] = db.session.query(UserRatings).filter(
                and_(user.to_dict()['id'] == UserRatings.user_id),
                (cocktail.to_dict()['id'] == UserRatings.cocktail_id)
                ).first().to_dict()['user_rating']

        return data


def find_cocktails(args, user):
    filtered = []
    total = 0
    num_of_cocktails = 20
    search_list = []
    filter_list = []
    curr_page = 1
    keys = list(args.keys())

    if 'page' in keys:
        curr_page = int(args['page'])

    if 'search' in keys:
        search_value = func.lower(args['search'])
        search_list.append(
            func.lower(Cocktail.name).contains(search_value))
        search_list.append(
            func.lower(Cocktail.preparation).contains(search_value))
        search_list.append(
            func.lower(Cocktail.garnish).contains(search_value))
        search_list.append(
            func.lower(Ingredient.name).contains(search_value))

    ingredients = [args.get(ing).split(',') for ing in keys
                   if ing in ['mixer', 'spirit', 'wine', 'liqueur'] and
                   args.get(ing) is not None]
    ingredients = [ing for sublist in ingredients for ing in sublist]

    for ing in ingredients:
        filter_list.append(Cocktail.ingredients.any(name=ing))

    try:
        cocktails = (
            db.session.query(Cocktail, func.count(Cocktail.id).over())
              .order_by(Cocktail.name)
              .join(*Cocktail.ingredients.attr)
              .filter(and_(or_(*search_list), *filter_list))
              .distinct()
              .paginate(curr_page, num_of_cocktails)
        )

        total = cocktails.total
        cocktails = cocktails.items

        for cocktail in cocktails:
            cocktail = cocktail[0].to_dict()
            # If user is logged in, try to get his rating if it exists
            # otherwise gracefully continue
            if user:
                try:
                    cocktail['user_rating'] = db.session.query(
                        UserRatings).filter(
                        and_(user.to_dict()['id'] == UserRatings.user_id),
                        (cocktail['id'] == UserRatings.cocktail_id)
                    ).first().to_dict()['user_rating']
                except AttributeError:
                    pass
            filtered.append(cocktail)

    except exc.SQLAlchemyError:
        throw_exception(INTERNAL_SERVER_ERROR, rollback=True)

    return filtered, total


def get_filters():
    filters = [
        {
            'name': 'Spirit',
            'label': 'spirit',
            'value': []
        },
        {
            'name': 'Liqueur',
            'label': 'liqueur',
            'value': []
        },
        {
            'name': 'Wine/Vermouth',
            'label': 'wine',
            'value': []
        },
        {
            'name': 'Mixer',
            'label': 'mixer',
            'value': []
        }
    ]

    result = db.session\
        .query(Ingredient.name, Ingredient.type)\
        .order_by(Ingredient.name)\
        .all()

    ingredients = [
        {
            'name': ingredient.name,
            'type': ingredient.type
        } for ingredient in result]

    for ing in ingredients:
        if ing['type'] == 'Spirit':
            filters[0]['value'].append(ing['name'])
        elif ing['type'] == 'Liqueur':
            filters[1]['value'].append(ing['name'])
        elif ing['type'] == 'Mixer':
            filters[3]['value'].append(ing['name'])
        else:
            filters[2]['value'].append(ing['name'])

    return filters
