import datetime
import random

from datajournals import db
from datajournals.models import SleepLocationTag, SleepEmotionTag, SleepSensationTag, SleepRecord, SleepNote, \
    SleepInterruptionTag, SleepInterruptionAssociation
from datajournals.sleepdb.init_db import init_sleep_tables, init_default_sleep_tags
from datajournals.tests import get_random_datetime


def fill_sleep_tables(init: bool = False, set_default_tags: bool = False, num_records: int = 20):
    # Reinitialize tables
    if init:
        init_sleep_tables()
    if set_default_tags:
        init_default_sleep_tags()

    # Create tag objects
    # Location tags
    locations_query = SleepLocationTag.query.all()
    if locations_query:
        locations = locations_query
    else:
        bedroom_tag = SleepLocationTag(tag='bedroom')
        office_tag = SleepLocationTag(tag='office')
        livingroom_tag = SleepLocationTag(tag='living room')
        locations = [bedroom_tag, office_tag, livingroom_tag]

    # Emotion tags
    emotions_query = SleepEmotionTag.query.all()
    if emotions_query:
        emotions = emotions_query
    else:
        angry_tag = SleepEmotionTag(tag='angry')
        sad_tag = SleepEmotionTag(tag='sad')
        anxious_tag = SleepEmotionTag(tag='anxious')
        emotions = [angry_tag, sad_tag, anxious_tag]

    # Sensation tags
    sensations_query = SleepSensationTag.query.all()
    if sensations_query:
        sensations = sensations_query
    else:
        relaxed_tag = SleepSensationTag(tag='relaxed')
        groggy_tag = SleepSensationTag(tag='groggy')
        rested_tag = SleepSensationTag(tag='rested')
        sensations = [relaxed_tag, groggy_tag, rested_tag]

    # Interruption tags
    interruptions_query = SleepInterruptionTag.query.all()
    if interruptions_query:
        interruptions = interruptions_query
    else:
        dream_tag = SleepInterruptionTag(tag='dream')
        dog_barking_tag = SleepInterruptionTag(tag='dog barking')
        bathroom_tag = SleepInterruptionTag(tag='bathroom')
        interruptions = [dream_tag, dog_barking_tag, bathroom_tag]

    def _create_record():

        # Create SleepRecord objects with description and tags data and store in list
        sleepdurations = [15, 30, 60, 120, 300, 360, 420, 480]
        for _ in range(num_records):
            sr = SleepRecord()
            sr.date_added = get_random_datetime(max_=datetime.datetime.today() - datetime.timedelta(days=1))
            sr.time_retire = sr.date_added
            if random.randint(0, 11) > 0:
                sr.time_start_sleep = (sr.time_retire +
                                       datetime.timedelta(minutes=random.randint(0, 31)))
            if random.randint(0, 11) > 0 and sr.time_start_sleep:
                sr.time_stop_sleep = (sr.time_start_sleep +
                                      datetime.timedelta(minutes=random.choice(sleepdurations)))
            c = random.randint(0, 11) > 0
            if c and sr.time_stop_sleep:
                tr = (sr.time_stop_sleep +
                      datetime.timedelta(minutes=random.randint(0, 30)))

            elif c and sr.time_start_sleep:
                tr = (sr.time_start_sleep +
                      datetime.timedelta(minutes=random.choice(sleepdurations)))
            elif c:
                tr = (sr.time_retire +
                      datetime.timedelta(minutes=random.choice(sleepdurations)))
            else:
                tr = None
            sr.time_rise = tr
            if sr.time_rise:
                sr.rating = random.choice(range(1, 5))
            else:
                sr.rating = 0
            sr.emotions = (random.choices(emotions, k=random.randint(0, 2)))
            sr.locations.append(random.choice(locations))
            sr.sensations.append(random.choice(sensations))
            for _ in range(random.randint(0, 3)):
                tags = random.choices(interruptions,
                                      k=random.choice(range(1, len(interruptions) // 3)))
                interruption = SleepInterruptionAssociation()
                if sr.time_stop_sleep:
                    interruption.start = get_random_datetime(sr.time_start_sleep,
                                                             sr.time_stop_sleep)
                    interruption.stop = get_random_datetime(interruption.start,
                                                            max(sr.time_start_sleep + datetime.timedelta(minutes=30),
                                                                sr.time_stop_sleep))
                if interruption.stop:
                    interruption.duration = (interruption.stop - interruption.start).total_seconds() // 60
                else:
                    interruption.duration = random.choices(
                        [None, random.choice(range(1, 21))], weights=[1, 30])[0]
                interruption.tags = tags
                sr.interruptions.append(interruption)

            return sr

    def _create_note(record: SleepRecord = None):
        note = SleepNote()
        if record:
            note.record_id = record.id
        note.date_added = get_random_datetime(min_=record.date_added if record else None)
        note.last_edited = note.date_added
        note_ = f'This is a note.{f" It is for record {record.id}." if record else ""}'
        note.note = note_
        note.important = random.randint(0, 1) > 0
        return note

    for _ in range(0, num_records):
        r = _create_record()
        db.session.add(r)
        db.session.commit()
        if random.randint(0, 2) > 0:
            for _ in range(random.randint(0, 2)):
                db.session.add(_create_note(r))
        else:
            db.session.add(_create_note())
        db.session.commit()


if __name__ == '__main__':
    from datajournals import create_app

    app = create_app()
    with app.app_context():
        fill_sleep_tables(True, True, num_records=50)
