import math
import random
from random import randint, choice

from datajournals import db
from datajournals.dreamdb.init_db import init_dream_tables, init_default_dream_tags
from datajournals.models import DreamSubjectTag, DreamEmotionTag, DreamDescriptorTag, DreamRecord, DreamNote
from datajournals.tests import get_random_datetime, get_random_text


def fill_dream_tables(init: bool = False, set_default_tags: bool = False, num_records: int = 20):
    # Reinitialize tables
    if init:
        init_dream_tables()
    if set_default_tags:
        init_default_dream_tags()

    # Create tags objects. Check if tags already exist in database first
    for tt, tm, tn in (
            ('subjects', DreamSubjectTag, ['dogs', 'family', 'food']),
            ('descriptors', DreamDescriptorTag, ['philosophy', 'relationships', 'education']),
            ('emotions', DreamEmotionTag, ['angry', 'sad', 'anxious']),
    ):
        q = db.session.query(tm).all()
        if not q:
            tl = []
            for s in tn:
                tl.append(tm(tag=s))
            db.session.add_all(tl)

    # Create times of day and sleep types
    todl = ['early morning',
            'late morning',
            'early afternoon',
            'late afternoon',
            'early evening',
            'late evening']
    sltl = ['regular sleep',
            'long nap',
            'short nap',
            'daydream']

    # Create Dream objects with description and tags data and store in list
    rl = []
    for _ in range(num_records):
        d = get_random_datetime()
        dd = d.date()
        rc = get_random_text()
        r = DreamRecord()
        r.record = f'This is the record dated {dd.strftime("%A, %B %d, %Y")}.\n\nIt has some random content:\n{rc}.'
        r.record_date = dd
        r.time_of_day = random.choice(todl)
        r.sleep_type = random.choice(sltl)
        for tt, tm in (
                ('subjects', DreamSubjectTag),
                ('descriptors', DreamDescriptorTag),
                ('emotions', DreamEmotionTag),
        ):
            setattr(r, tt, random.choices(list(db.session.query(tm).all()), k=random.randint(0, 3)))
        if randint(0, 5) > 2:
            for i in range(randint(0, 4)):
                nd = get_random_datetime(d)
                n = DreamNote()
                n.note = f'Note {i + 1} about the record on {r.record_date.strftime("%A, %B %d, %Y")}'
                n.important = choice([True, False])
                r.notes.append(n)
                n.date_added = nd
                n.last_edited = nd
                d = nd
        rl.append(r)

    rnl = []
    for _ in range(math.floor(0.1 * num_records)):
        n = DreamNote()
        n.date_added = get_random_datetime()
        n.note = f'This is a note without a dream record. It is dated {n.date_added.strftime("%A, %B %d, %Y")}.'
        n.important = random.choice([True, False])
        rnl.append(n)

    # Add all Record objects to database
    db.session.add_all(rl)
    db.session.add_all(rnl)
    db.session.commit()


if __name__ == '__main__':
    from datajournals import create_app

    app = create_app()
    with app.app_context():
        fill_dream_tables(True, True, num_records=50)
