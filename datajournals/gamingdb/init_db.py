from flask import current_app
from sqlalchemy import MetaData, inspect
from datajournals import db
from datajournals.models import (GamingSessionRecord, Game, GamingEmotionTag, GamingInterruptionTag,
                                 GamingSessionInterruption, GamingNote)


def init_gaming_tables(create_tables: bool = True):
    """
    Remove tables related to Restaurant data and creates new, empty tables

    :param create_tables: create new tables, if True
    :return: None
    """

    # Create metadata and inspection objects
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    inspector = inspect(db.engine)

    # Check for existing secondary tables
    table_names = [
        'gaming_session_emotions',
        'gaming_interruptions_tags'
    ]
    tmp = table_names.copy()
    for i in range(len(table_names)):
        if not inspector.has_table(table_names[i]):
            tmp.remove(table_names[i])
    meta_tables = [metadata.tables[name] for name in tmp]

    # Check for existing models
    models = [GamingSessionRecord.__table__,
              Game.__table__,
              GamingEmotionTag.__table__,
              GamingInterruptionTag.__table__,
              GamingSessionInterruption.__table__,
              GamingNote.__table__,
              ]
    tmp = models.copy()
    for i in range(len(models)):
        if not inspector.has_table(models[i].name):
            tmp.remove(models[i])

    all_tables = meta_tables + tmp

    db.metadata.drop_all(db.engine, tables=all_tables)
    current_app.logger.warning('Dropped all tables associated with gamingdb.')
    if create_tables:
        db.create_all()
        db.session.commit()
        current_app.logger.info('Created tables for gamingdb.')


def init_default_emotion_tags():
    """
    Adds default tags to the emotion tags table
    :return: None
    """

    tag_objects = []
    db_tags = [x.tag for x in GamingEmotionTag.query.all()]
    tags = ['angry',
            'disappointed',
            'excited',
            'pleased',
            'amused',
            'happy',
            'frightened',
            'anxious',
            'restless',
            'inspired',
            ]
    for tag in tags:
        if tag not in db_tags:
            tag_objects.append(GamingEmotionTag(tag=tag))

    all_tags_objects = tag_objects
    db.session.add_all(all_tags_objects)
    db.session.commit()


def init_default_interruption_tags():
    """
    Adds default tags to the interruption tags table
    :return: None
    """

    tag_objects = []
    db_tags = [x.tag for x in GamingInterruptionTag.query.all()]
    tags = ['bathroom',
            'food',
            'drink',
            'phone call',
            'nap',
            'research',
            'visitor',
            'read',
            'watch tv',
            'cleaning'
            ]
    for tag in tags:
        if tag not in db_tags:
            tag_objects.append(GamingInterruptionTag(tag=tag))

    all_tags_objects = tag_objects
    db.session.add_all(all_tags_objects)
    db.session.commit()


def init_default_tags():
    init_default_emotion_tags()
    init_default_interruption_tags()
