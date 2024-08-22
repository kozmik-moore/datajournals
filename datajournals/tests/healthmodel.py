from os import scandir, rename
from os.path import abspath, join, dirname
from random import choice, randint, uniform
from shutil import copy
from uuid import uuid4

from flask import current_app

from datajournals import db
from datajournals.healthdb.init_db import init_health_tables, init_default_health_tags, init_health_attachments_store
from datajournals.models.healthdb import (HealthDescriptorTag, HealthEmotionTag, HealthRecord, HealthGlucoseRecord,
                                          HealthCardioRecord, HealthPainRecord, HealthWeightRecord, HealthNote,
                                          HealthAttachment)
from datajournals.tests import get_random_datetime, BaseModelTest


def fill_health_tables(num_records=20):

    # Create tags objects
    descriptor_tags = HealthDescriptorTag.query.all()
    emotion_tags = HealthEmotionTag.query.all()

    # Record types
    record_types = [
        'glucose',
        'cardio',
        'pain',
        'weight',
        'general'
    ]

    # (Possibly recursive) function to create a record and its components
    def create_record(parent=None):

        # Create record object with some data
        date = get_random_datetime(min_=parent.record_date if parent else None)
        record = HealthRecord()
        record.record_date = record.date_added = date
        record.is_tracked = randint(0, 10) > 7

        # Determine record type
        if parent:
            record.parent_id = parent.id
            type_ = 'general'
        else:
            type_ = choice(record_types)
        if type_ == 'glucose':
            subrecord = HealthGlucoseRecord()
            subrecord.measure = randint(60, 200)
            record.glucose_record.append(subrecord)
        elif type_ == 'cardio':
            subrecord = HealthCardioRecord()
            subrecord.systolic = randint(110, 160)
            subrecord.diastolic = randint(60, 100)
            subrecord.heart_rate = randint(60, 120)
            record.cardio_record.append(subrecord)
        elif type_ == 'pain':
            subrecord = HealthPainRecord()
            subrecord.level = randint(5, 10)
            subrecord.description = (f'This is the description for the pain record on '
                                     f'{date.strftime("%A, %B %d, %Y")}.'
                                     )
            record.pain_record.append(subrecord)
        elif type_ == 'weight':
            subrecord = HealthWeightRecord()
            subrecord.measure = uniform(305.0, 315.0)
            record.weight_record.append(subrecord)
        elif type_ == 'general':
            pass

        # Create record note(s).
        notes = []
        for i in range(0, randint(0, 2)):
            note = HealthNote()
            note.note = f'This is the note from {date.strftime("%A, %B %d, %Y")} concerning the {type_} record.'
            note.important = randint(0, 3) == 3
            note.date_added = note.last_edited = date
            notes.append(note)
        record.notes = notes
        record.record = (f'This is the record from {date.strftime("%A, %B %d, %Y")}. '
                         f'It is a {type_} record. {"It has notes." if notes else ""}')

        # Add record tags.
        tmp = []
        tags = descriptor_tags.copy()
        num_tags = randint(0, len(tags))
        while len(tags) > num_tags:
            tmp.append(tags.pop(randint(0, len(tags) - 1)))
        record.descriptors = tmp
        tmp = []
        tags = emotion_tags.copy()
        num_tags = randint(0, len(tags))
        while len(tags) > num_tags:
            tmp.append(tags.pop(randint(0, len(tags) - 1)))
        record.emotions = tmp

        # Add attachments
        tmp = []
        test_attachments_path = abspath(join(dirname(__file__), 'attachments'))
        attachments = list(scandir(test_attachments_path))
        for attachment in attachments:
            if randint(0, 5) > 3:
                uuid = str(uuid4())
                new_path = abspath(join(current_app.config['HEALTH_ATTACHMENTS_DIR'], attachment.name))
                uuid_path = abspath(join(current_app.config['HEALTH_ATTACHMENTS_DIR'], uuid))
                copy(attachment.path, new_path)
                rename(new_path, uuid_path)
                att_obj = HealthAttachment()
                att_obj.filename = attachment.name
                att_obj.uuid = uuid
                tmp.append(att_obj)
        record.attachments = tmp

        db.session.add(record)
        db.session.commit()

        # Create child record (possibly)
        if randint(0, 5) > 3:
            create_record(record)

    for _ in range(num_records):
        create_record()


def init_folder(delete_files=False):
    """
    Create directory for health attachments, if it doesn't exist; empty it, if it does.
    USE WITH CAUTION.
    :return: None
    """
    init_health_attachments_store(delete_files)


healthmodel = BaseModelTest()
healthmodel.fill_tables_func = fill_health_tables
healthmodel.init_tables_func = init_health_tables
healthmodel.set_tags_func = init_default_health_tags
setattr(healthmodel, 'init_folder', init_folder)

if __name__ == '__main__':
    healthmodel.fill_tables(init_tables=True, set_tags=True)
