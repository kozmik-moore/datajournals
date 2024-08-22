from flask import current_app
from sqlalchemy import MetaData, inspect

from datajournals import db
from datajournals.models import SleepRecord, SleepEmotionTag, SleepLocationTag, SleepSensationTag, SleepNote, \
    SleepInterruptionTag, SleepInterruptionAssociation


# TODO Needs testing after creation of SleepInterruptionAssociation
def init_sleep_tables(create_tables: bool = True):
    """
    Remove tables related to Sleep data and create new, empty tables

    :return: None
    """

    # Create metadata and inspection objects
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    inspector = inspect(db.engine)

    # Check for existing intermediary tables
    table_names = ['sleep_locations',
                   'sleep_sensations',
                   'sleep_emotions',
                   'sleep_interruptions_tags',
                   ]
    tmp = table_names.copy()
    for i in range(len(table_names)):
        if not inspector.has_table(table_names[i]):
            tmp.remove(table_names[i])
    meta_tables = [metadata.tables[name] for name in tmp]

    # Check for existing models
    models = [SleepRecord.__table__,
              SleepLocationTag.__table__,
              SleepEmotionTag.__table__,
              SleepSensationTag.__table__,
              SleepInterruptionTag.__table__,
              SleepInterruptionAssociation.__table__,
              SleepNote.__table__, ]
    tmp = models.copy()
    for i in range(len(models)):
        if not inspector.has_table(models[i].name):
            tmp.remove(models[i])

    all_tables = meta_tables + tmp

    db.metadata.drop_all(db.engine, tables=all_tables)
    current_app.logger.warning('Dropped all tables associated with sleepdb.')
    if create_tables:
        db.create_all()
        db.session.commit()
        current_app.logger.info('Created tables for sleepdb.')


def init_default_sleep_tags():
    """
    Adds default tags to the sleep sensation, descriptor, emotion, and interruption tags tables
    :return: None
    """

    # Sensation tags
    sensation_objects = []
    db_sensations = [x.tag for x in SleepSensationTag.query.all()]
    sensations = ['relaxed',
                  'rested',
                  'groggy',
                  'exhausted',
                  ]
    for sensation in sensations:
        if sensation not in db_sensations:
            sensation_objects.append(SleepSensationTag(tag=sensation))

    # Location tags
    location_objects = []
    db_locations = [x.tag for x in SleepLocationTag.query.all()]
    locations = ['bedroom',
                 'office',
                 'spare bedroom',
                 'bed',
                 'floor',
                 'couch',
                 'backyard',
                 'camping',
                 'living room',
                 ]
    for location in locations:
        if location not in db_locations:
            location_objects.append(SleepLocationTag(tag=location))

    # emotion tags
    emotion_objects = []
    db_emotions = [x.tag for x in SleepEmotionTag.query.all()]
    emotions = ['angry',
                'excited',
                'pleased',
                'happy',
                'anxious',
                ]
    for emotion in emotions:
        if emotion not in db_emotions:
            emotion_objects.append(SleepEmotionTag(tag=emotion))

    # Interruption tags
    interruption_objects = []
    db_interruptions = [x.tag for x in SleepInterruptionTag.query.all()]
    interruptions = ['bathroom',
                     'bad dream',
                     'unknown sound',
                     'dog barking',
                     'snoring',
                     'feeling hot',
                     'feeling cold',
                     'pain',
                     'discomfort',
                     'alarm',
                     'people talking',
                     'television noise',
                     'radio noise',
                     'multiple sources',
                     ]
    for interruption in interruptions:
        if interruption not in db_interruptions:
            interruption_objects.append(SleepInterruptionTag(tag=interruption))

    all_tags_objects = sensation_objects + location_objects + emotion_objects + interruption_objects
    db.session.add_all(all_tags_objects)
    db.session.commit()


if __name__ == '__main__':
    init_sleep_tables()
