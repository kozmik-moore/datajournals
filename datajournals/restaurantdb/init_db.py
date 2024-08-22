from flask import current_app
from sqlalchemy import MetaData, inspect

from datajournals import db
from datajournals.models.restaurantdb import RestaurantRecord, RestaurantTag, RestaurantVisit, RestaurantNote


def init_restaurant_tables(create_tables: bool = True):
    """
    Remove tables related to Restaurant data and creates new, empty tables

    :param create_tables: create new tables, if True
    :return: None
    """

    # Create metadata and inspection objects
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    inspector = inspect(db.engine)

    # Check for existing intermediary tables
    table_names = ['restaurant_tags',
                   ]
    tmp = table_names.copy()
    for i in range(len(table_names)):
        if not inspector.has_table(table_names[i]):
            tmp.remove(table_names[i])
    meta_tables = [metadata.tables[name] for name in tmp]

    # Check for existing models
    models = [RestaurantRecord.__table__,
              RestaurantTag.__table__,
              RestaurantVisit.__table__,
              RestaurantNote.__table__,
              ]
    tmp = models.copy()
    for i in range(len(models)):
        if not inspector.has_table(models[i].name):
            tmp.remove(models[i])

    all_tables = meta_tables + tmp

    db.metadata.drop_all(db.engine, tables=all_tables)
    current_app.logger.warning('Dropped all tables associated with restaurantdb.')
    if create_tables:
        db.create_all()
        db.session.commit()
        current_app.logger.info('Created tables for restaurantdb.')


def init_default_restaurant_tags():
    """
    Adds default tags to the restaurant tags table
    :return: None
    """

    # Subject tags
    tag_objects = []
    db_tags = [x.tag for x in RestaurantTag.query.all()]
    tags = ['tacos',
            'burritos',
            'burgers',
            'chinese',
            'pizza',
            'sandwiches',
            'vegetarian',
            'vegan',
            'japanese',
            'sushi',
            'ice cream',
            'yogurt',
            'tea',
            'coffee',
            'korean',
            'mexican',
            'poke',
            'fast-food',
            'dine-in',
            'takeout',
            'buffet',
            'asian buffet',
            'drive-through'
            ]
    for tag in tags:
        if tag not in db_tags:
            tag_objects.append(RestaurantTag(tag=tag))

    all_tags_objects = tag_objects
    db.session.add_all(all_tags_objects)
    db.session.commit()


if __name__ == '__main__':
    init_restaurant_tables()
