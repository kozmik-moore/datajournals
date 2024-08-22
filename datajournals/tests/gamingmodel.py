import datetime
import random

import numpy as np

from datajournals import db
from datajournals.gamingdb.init_db import init_default_tags, init_gaming_tables
from datajournals.models import (GamingEmotionTag, GamingInterruptionTag, GamingSessionRecord,
                                 GamingSessionInterruption, GamingNote, Game)
from datajournals.tests import get_random_datetime, BaseModelTest


def fill_tables(num_records: int = 20):
    # Game names

    game_names = [
        'Cyberpunk 2077',
        'Skyrim',
        'Final Fantasy VII',
        'Elder Scrolls Online',
        'Starfield',
        'Call of Duty',
        'Goldeneye',
        'Sonic the Hedgehog',
        'Super Mario Bros',
        'Fallout 4'
    ]

    def create_record():
        record_ = GamingSessionRecord()
        record_.date_added = get_random_datetime(max_=datetime.datetime.now() - datetime.timedelta(minutes=120))
        record_.start_time = record_.date_added + datetime.timedelta(minutes=random.randint(-60, 60))
        record_.stop_time = record_.start_time + datetime.timedelta(minutes=random.randint(10, 60))

        # Add emotions tags
        emotion_tags = list(GamingEmotionTag.query.all())
        emotions_tags = []
        num_tags = random.randint(0, len(emotion_tags) // 3)
        tmp_tags = emotion_tags.copy()
        while num_tags > 0:
            emotions_tags.append(tmp_tags.pop(random.randint(0, len(tmp_tags) - 1)))
            num_tags -= 1
        record_.emotions = emotions_tags

        # Add session interruptions
        interruption_tags = list(GamingInterruptionTag.query.all())
        session_interruptions = []
        num_interruptions = random.randint(0, 4)
        durations = [None] + list(range(1, 6))
        while num_interruptions > 0:
            interruption = GamingSessionInterruption()
            duration = random.choice(durations)
            if duration is not None and random.randint(0, 1) == 1:
                if duration == 0:
                    duration = 1
                interruption.start_time = get_random_datetime(
                    min_=record_.start_time,
                    max_=record_.stop_time - datetime.timedelta(minutes=10)
                )
                max_duration = ((record_.stop_time - datetime.timedelta(minutes=10) - interruption.start_time)
                                .total_seconds() // 60)
                final_duration = min(duration, max_duration) if max_duration > 0 else duration
                interruption.stop_time = interruption.start_time + datetime.timedelta(minutes=final_duration)
                interruption.duration = final_duration
            elif duration is not None:
                interruption.duration = duration
            interruption.tags = random.choices(population=interruption_tags, k=random.randint(1, 3))
            session_interruptions.append(interruption)
            num_interruptions -= 1
        record_.session_interruptions = session_interruptions

        # Add session game
        name = random.choice(game_names)
        record_game = Game.query.filter_by(name=name).first()
        if not record_game:
            record_game = Game(name=name)
        record_.game = record_game

        db.session.add(record_)
        db.session.commit()

        # Add session rating
        record_.session_rating = np.random.binomial(5, 0.6)

    def create_note(note_record: GamingSessionRecord = None, note_game: Game = None):
        note = GamingNote()
        desc = 'This note has no associated record or game.'
        if note_record:
            note.record = note_record
            note.game = note_record.game
            desc = f'This is a note for record {note_record.id}, during which *{note.game.name}* was played.'
        if note_game:
            note.game = note_game
            desc = f'This is a note for *{note_game.name}*.'
        note.note = desc
        note.date_added = get_random_datetime(min_=note_record.date_added) if note_record else get_random_datetime()
        note.important = random.randint(0, 1) == 0
        db.session.add(note)
        db.session.commit()

    for _ in range(num_records):
        create_record()

    records = GamingSessionRecord.query.all()
    games = Game.query.all()
    num_notes = num_records * 1.5
    while num_notes > 0:
        record_note = random.randint(0, 1) == 1
        if record_note and records:
            record = records.pop(random.randint(0, len(records) - 1))
            create_note(note_record=record)
        elif random.randint(0, 2) > 0:
            game = games[(random.randint(0, len(games) - 1))]
            create_note(note_game=game)
        else:
            create_note()
        num_notes -= 1


gamingmodel = BaseModelTest()
gamingmodel.set_tags_func = init_default_tags
gamingmodel.fill_tables_func = fill_tables
gamingmodel.init_tables_func = init_gaming_tables

if __name__ == '__main__':
    from datajournals import create_app

    app = create_app()
    with app.app_context():
        gamingmodel.fill_tables(25, init_tables=True, set_tags=True)
