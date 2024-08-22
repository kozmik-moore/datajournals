from flask import current_app
from sqlalchemy import MetaData, inspect

from datajournals import db
from datajournals.models.dreamdb import DreamRecord, DreamSubjectTag, DreamNote, DreamEmotionTag, DreamDescriptorTag


def init_dream_tables(create_tables: bool = True):
    """
    Drop tables related to Dream data and create new, empty tables

    :return: None
    """

    # Create metadata and inspection objects
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    inspector = inspect(db.engine)

    # Check for existing intermediary tables
    table_names = ['dream_subjects',
                   'dream_descriptors',
                   'dream_emotions',
                   'dream_notes',
                   ]
    tmp = table_names.copy()
    for i in range(len(table_names)):
        if not inspector.has_table(table_names[i]):
            tmp.remove(table_names[i])
    meta_tables = [metadata.tables[name] for name in tmp]

    # Check for existing models
    models = [DreamRecord.__table__,
              DreamSubjectTag.__table__,
              DreamDescriptorTag.__table__,
              DreamEmotionTag.__table__,
              DreamNote.__table__, ]
    tmp = models.copy()
    for i in range(len(models)):
        if not inspector.has_table(models[i].name):
            tmp.remove(models[i])

    all_tables = meta_tables + tmp

    db.metadata.drop_all(db.engine, tables=all_tables)
    current_app.logger.warning('Dropped all tables associated with dreamdb.')
    if create_tables:
        db.create_all()
        db.session.commit()
        current_app.logger.info('Created tables for dreamdb.')


def init_default_dream_tags():
    """
    Adds default tags to the dream subject, descriptor, and emotion tags tables
    :return: None
    """

    # Subject tags
    subject_objects = []
    db_subjects = [x.tag for x in DreamSubjectTag.query.all()]
    subjects = ['family',
                'friends',
                'acquaintances',
                'coworkers',
                'dogs',
                'school',
                'work',
                'monsters',
                ]
    for subject in subjects:
        if subject not in db_subjects:
            subject_objects.append(DreamSubjectTag(tag=subject))

    # Descriptor tags
    descriptor_objects = []
    db_descriptors = [x.tag for x in DreamDescriptorTag.query.all()]
    descriptors = ['scary',
                   'mundane',
                   'psychadelic',
                   'disjointed',
                   'confusing',
                   'pleasant',
                   'erotic',
                   ]
    for descriptor in descriptors:
        if descriptor not in db_descriptors:
            descriptor_objects.append(DreamDescriptorTag(tag=descriptor))

    # Emotion tags
    emotion_objects = []
    db_emotions = [x.tag for x in DreamEmotionTag.query.all()]
    emotions = ['angry',
                'anxious',
                'disappointed',
                'excited',
                'pleased',
                'amused',
                'happy',
                'frightened',
                'restless',
                'neutral',
                'annoyed',
                'motivated',
                ]
    for emotion in sorted(emotions):
        if emotion not in db_emotions:
            emotion_objects.append(DreamEmotionTag(tag=emotion))

    all_tags_objects = subject_objects + descriptor_objects + emotion_objects
    db.session.add_all(all_tags_objects)
    db.session.commit()


if __name__ == '__main__':
    init_dream_tables()
    init_default_dream_tags()
