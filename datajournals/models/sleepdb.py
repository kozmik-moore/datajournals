from datajournals import db

sleep_locations = db.Table('sleep_locations',
                           db.Column('record_id', db.Integer, db.ForeignKey('sleep_record.id')),
                           db.Column('tag_id', db.Integer, db.ForeignKey('sleep_location_tag.id'))
                           )

sleep_emotions = db.Table('sleep_emotions',
                          db.Column('record_id', db.Integer, db.ForeignKey('sleep_record.id')),
                          db.Column('tag_id', db.Integer, db.ForeignKey('sleep_emotion_tag.id'))
                          )

sleep_sensations = db.Table('sleep_sensations',
                            db.Column('record_id', db.Integer, db.ForeignKey('sleep_record.id')),
                            db.Column('tag_id', db.Integer, db.ForeignKey('sleep_sensation_tag.id'))
                            )

sleep_interruptions = db.Table('sleep_interruptions_tags',
                               db.Column('interruption_id',
                                         db.Integer,
                                         db.ForeignKey('sleep_interruption_association.id')),
                               db.Column('tag_id', db.Integer, db.ForeignKey('sleep_interruption_tag.id'))
                               )


class SleepRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_added = db.Column(db.DateTime)  # date added - input from server
    rating = db.Column(db.Integer)  # scale of 0 to 4
    time_retire = db.Column(db.DateTime)  # time retired to bed
    time_start_sleep = db.Column(db.DateTime)
    time_stop_sleep = db.Column(db.DateTime)
    time_rise = db.Column(db.DateTime)  # time rose out of bed
    locations = db.relationship('SleepLocationTag', secondary=sleep_locations, backref='records', lazy=True)
    emotions = db.relationship('SleepEmotionTag', secondary=sleep_emotions, backref='records', lazy=True)
    sensations = db.relationship('SleepSensationTag', secondary=sleep_sensations, backref='records', lazy=True)
    interruptions = db.relationship(
        'SleepInterruptionAssociation', back_populates='record', lazy=True, cascade='all, delete')
    notes = db.relationship('SleepNote', backref='record', lazy=True, cascade='all, delete')


class SleepEmotionTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, unique=True)

    def __repr__(self):
        return f'<Sleep emotion: "{self.tag}">'


class SleepLocationTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, unique=True)

    def __repr__(self):
        return f'<Sleep location: "{self.tag}">'


class SleepSensationTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, unique=True)

    def __repr__(self):
        return f'<Sleep sensation: "{self.tag}">'


class SleepInterruptionTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, unique=True)

    interruptions = db.relationship('SleepInterruptionAssociation',
                                    secondary=sleep_interruptions,
                                    primaryjoin='SleepInterruptionTag.id == sleep_interruptions_tags.c.tag_id',
                                    secondaryjoin='sleep_interruptions_tags.c.interruption_id == '
                                                  'SleepInterruptionAssociation.id',
                                    back_populates='tags')

    def __repr__(self):
        return f'<Sleep interruption tag: "{self.tag}">'


class SleepInterruptionAssociation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('sleep_record.id'))
    start = db.Column(db.DateTime)
    stop = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # in minutes

    record = db.relationship('SleepRecord', back_populates='interruptions')
    tags = db.relationship('SleepInterruptionTag',
                           lazy=True,
                           secondary=sleep_interruptions,
                           primaryjoin='SleepInterruptionAssociation.id == sleep_interruptions_tags.c.interruption_id',
                           secondaryjoin='sleep_interruptions_tags.c.tag_id == SleepInterruptionTag.id',
                           back_populates='interruptions', )

    def __repr__(self):
        return f'<Sleep-interruption: ({self.id}, {self.record_id})>'


class SleepNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('sleep_record.id'))
    note = db.Column(db.String)
    important = db.Column(db.Boolean, default=False)
    date_added = db.Column(db.DateTime)
    last_edited = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Sleep note: "{self.note[:30]}">'
