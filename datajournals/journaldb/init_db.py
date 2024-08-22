from os import scandir, remove, mkdir, makedirs
from os.path import exists

from flask import current_app
from sqlalchemy import MetaData, inspect

from datajournals import db
from datajournals.models.journaldb import JournalRecord, JournalSubjectTag, JournalAttachment, JournalEmotionTag, \
    JournalDescriptorTag


def init_journal_attachments_store(delete_files=False):
    """
    Create directory for journal attachments, if it doesn't exist; empty it, if it does.
    USE WITH CAUTION.
    :return: None
    """
    if exists(current_app.config['JOURNAL_ATTACHMENTS_DIR']):
        if delete_files or \
                input('Delete files from journal attachments folder? ').strip() in ['y', 'Y', 'yes', 'Yes', 'YES', '1']:
            files = scandir(current_app.config['JOURNAL_ATTACHMENTS_DIR'])
            for file in files:
                remove(file)
    else:
        message = f'Creating journal attachments directory at {current_app.config["JOURNAL_ATTACHMENTS_DIR"]}'
        current_app.logger.warning(message)
        makedirs(current_app.config['JOURNAL_ATTACHMENTS_DIR'])


def init_journal_tables(create_tables: bool = True):
    """
    Remove tables related to Journal data and create new, empty tables.
    USE WITH CAUTION.
    :return: None
    """

    # Create metadata and inspection objects
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    inspector = inspect(db.engine)

    # Check for existing intermediary tables
    table_names = ['journal_subjects',
                   'journal_descriptors',
                   'journal_emotions',
                   'journal_links', ]
    tmp = table_names.copy()
    for i in range(len(table_names)):
        if not inspector.has_table(table_names[i]):
            tmp.remove(table_names[i])
    meta_tables = [metadata.tables[name] for name in tmp]

    # Check for existing models
    models = [JournalRecord.__table__,
              JournalSubjectTag.__table__,
              JournalDescriptorTag.__table__,
              JournalEmotionTag.__table__,
              JournalAttachment.__table__, ]
    tmp = models.copy()
    for i in range(len(models)):
        if not inspector.has_table(models[i].name):
            tmp.remove(models[i])

    all_tables = meta_tables + tmp

    db.metadata.drop_all(db.engine, tables=all_tables)
    current_app.logger.warning('Dropped all tables associated with journaldb.')
    if create_tables:
        db.create_all()
        db.session.commit()
        current_app.logger.info('Created tables for journaldb.')


def init_default_journal_tags():
    """
    Adds default tags to the journal subject, descriptor, and emotion tags tables
    :return: None
    """

    # Subject tags
    subject_objects = []
    db_subjects = [x.tag for x in JournalSubjectTag.query.all()]
    subjects = ['politics',
                'family',
                'friends',
                'relationships',
                'dogs',
                'technology',
                'writing',
                'programming',
                'movies',
                'television',
                'music',
                ]
    for subject in subjects:
        if subject not in db_subjects:
            subject_objects.append(JournalSubjectTag(tag=subject))

    # Descriptor tags
    descriptor_objects = []
    db_descriptors = [x.tag for x in JournalDescriptorTag.query.all()]
    descriptors = ['philosophy',
                   'rant',
                   'insight',
                   'observation',
                   'musing',
                   'recollection',
                   'memory',
                   'unfinished',
                   ]
    for descriptor in descriptors:
        if descriptor not in db_descriptors:
            descriptor_objects.append(JournalDescriptorTag(tag=descriptor))

    # Emotion tags
    emotion_objects = []
    db_emotions = [x.tag for x in JournalEmotionTag.query.all()]
    emotions = ['angry',
                'disappointed',
                'excited',
                'pleased',
                'amused',
                'happy',
                'anxious',
                ]
    for emotion in emotions:
        if emotion not in db_emotions:
            emotion_objects.append(JournalEmotionTag(tag=emotion))

    all_tags_objects = subject_objects + descriptor_objects + emotion_objects
    db.session.add_all(all_tags_objects)
    db.session.commit()


if __name__ == '__main__':
    init_journal_attachments_store()
    init_journal_tables()
