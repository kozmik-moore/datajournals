from flask import current_app
from sqlalchemy import MetaData, inspect

from datajournals import db
from datajournals.models.authorization import User, Role


def init_authorization_tables(create_tables: bool = True):
    """
    Drop authorization tables and create new ones

    :return: None
    """

    # Create metadata and inspection objects
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    inspector = inspect(db.engine)

    # Check for existing models
    models = [User.__table__,
              Role.__table__,
              ]
    tmp = models.copy()
    for i in range(len(models)):
        if not inspector.has_table(models[i].name):
            tmp.remove(models[i])

    all_tables = tmp

    db.metadata.drop_all(db.engine, tables=all_tables)
    if create_tables:
        db.create_all()
        db.session.commit()
        current_app.logger.info('Created tables for authorization.')


def init_default_roles():
    role_objects = []
    db_rolenames = [x.rolename for x in Role.query.all()]
    rolenames = ['admin', 'editor', 'visitor']
    for role in rolenames:
        if role not in db_rolenames:
            role_objects.append(Role(rolename=role))
    db.session.add_all(role_objects)
    db.session.commit()


if __name__ == '__main__':
    init_authorization_tables()
