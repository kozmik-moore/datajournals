from os import scandir, rename
from os.path import join, dirname
from random import randint
from shutil import copy
from uuid import uuid4

from flask import current_app

from datajournals import db
from datajournals.journaldb.init_db import init_journal_tables, init_journal_attachments_store, \
    init_default_journal_tags
from datajournals.models import JournalSubjectTag, JournalEmotionTag, JournalDescriptorTag, JournalRecord, \
    JournalAttachment
from datajournals.tests import get_random_datetime


def fill_journal_tables(init: bool = False, set_default_tags: bool = False, num_records: int = 20):

    # Reinitialize tables and attachments store
    if init:
        init_journal_tables()
        init_journal_attachments_store(True)
    if set_default_tags:
        init_default_journal_tags()

    # Create tags. Check if tags already exist in database first
    # Subject tags
    subject_query = JournalSubjectTag.query.all()
    if subject_query:
        subjects = subject_query
    else:
        dogs_tag = JournalSubjectTag(tag='dogs')
        family_tag = JournalSubjectTag(tag='family')
        food_tag = JournalSubjectTag(tag='food')
        subjects = [dogs_tag, family_tag, food_tag]

    # Emotion tags
    emotion_query = JournalEmotionTag.query.all()
    if emotion_query:
        emotions = emotion_query
    else:
        angry_tag = JournalEmotionTag(tag='angry')
        sad_tag = JournalEmotionTag(tag='sad')
        anxious_tag = JournalEmotionTag(tag='anxious')
        emotions = [angry_tag, sad_tag, anxious_tag]

    # Descriptor tags
    descriptor_query = JournalDescriptorTag.query.all()
    if descriptor_query:
        descriptors = descriptor_query
    else:
        philosophy_tag = JournalDescriptorTag(tag='philosophy')
        relationships_tag = JournalDescriptorTag(tag='relationships')
        education_tag = JournalDescriptorTag(tag='education')
        descriptors = [philosophy_tag, relationships_tag, education_tag]

    # Create Journal objects with record, tags data, and attachments and store in list
    records = []

    test_attachments = list(scandir(join(dirname(__file__), 'attachments')))

    def _create_journal_obj(parent=None, parent_date=None):
        """
        Create a journal object
        :return: None
        """
        date = get_random_datetime(min_=parent_date)

        # Create journal object
        record = JournalRecord(record=f'This is a journal entry from {date.strftime("%A, %B %d, %Y")}.',
                               record_date=date,
                               date_added=date,
                               )
        records.append(record)
        db.session.add(record)
        db.session.commit()

        # Link to parent record, if necessary
        if parent:
            parent.children.append(record)

        # Create and add tags
        for tags in subjects, emotions, descriptors:
            num_tags = randint(1, len(tags) + 1)
            j = 0
            tmp = tags.copy()
            while j < num_tags:
                tag = tmp.pop(randint(0, len(tmp) - 1)) if tmp else None
                if tag in subjects:
                    record.subjects.append(tag)
                if tag in emotions:
                    record.emotions.append(tag)
                if tag in descriptors:
                    record.descriptors.append(tag)
                j += 1

        # Copy and add attachments
        attachments_path = current_app.config['JOURNAL_ATTACHMENTS_DIR']
        if randint(0, 5) > 2:
            for i in range(randint(0, len(test_attachments))):
                uuid_ = uuid4()
                copy(test_attachments[i].path, attachments_path)
                rename(join(attachments_path, test_attachments[i].name),
                       join(attachments_path, str(uuid_)))
                attachment = JournalAttachment(
                    filename=test_attachments[i].name,
                    uuid=str(uuid_),
                )
                record.attachments.append(attachment)

        # Create linked records
        if randint(0, 3) > 1:
            for i in range(randint(0, 3)):
                _create_journal_obj(parent=record, parent_date=date)

    for _ in range(num_records):
        _create_journal_obj()

    # Add all Journal objects to database
    db.session.add_all(records)
    db.session.commit()


if __name__ == '__main__':
    fill_journal_tables(True, True)
