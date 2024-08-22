from datajournals import db

session_emotions = db.Table('gaming_session_emotions',
                            db.Column('session_id', db.Integer, db.ForeignKey('gaming_session_records.id')),
                            db.Column('emotion_id', db.Integer, db.ForeignKey('gaming_emotion_tags.id')),
                            )

interruptions_tags = db.Table('gaming_interruptions_tags',
                              db.Column('interruption_id',
                                        db.Integer,
                                        db.ForeignKey('gaming_session_interruptions.id')
                                        ),
                              db.Column('tag_id', db.Integer, db.ForeignKey('gaming_interruption_tags.id')),
                              )


class GamingSessionRecord(db.Model):
    __tablename__ = 'gaming_session_records'
    id = db.Column(db.Integer, primary_key=True)
    date_added = db.Column(db.DateTime)  # server time
    start_time = db.Column(db.DateTime)  # local time
    stop_time = db.Column(db.DateTime)  # local time
    session_rating = db.Column(db.Integer)  # 0 - 4
    game_id = db.Column(db.Integer, db.ForeignKey('gaming_games.id'))
    game = db.relationship('Game', back_populates='records', lazy=True)
    emotions = db.relationship('GamingEmotionTag', secondary=session_emotions, back_populates='records', lazy=True)
    session_interruptions = db.relationship(
        'GamingSessionInterruption', back_populates='record', lazy=True, cascade='all, delete')
    notes = db.relationship('GamingNote', back_populates='record', lazy=True, cascade='all, delete')

    def __repr__(self):
        return f'<Gaming session record {self.id}>'


class Game(db.Model):
    __tablename__ = 'gaming_games'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)

    records = db.relationship('GamingSessionRecord', back_populates='game')
    notes = db.relationship('GamingNote', back_populates='game')

    def __repr__(self):
        return f'<Game name: {self.name}>'


class GamingEmotionTag(db.Model):
    __tablename__ = 'gaming_emotion_tags'
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, unique=True)

    records = db.relationship('GamingSessionRecord', secondary=session_emotions, back_populates='emotions')

    def __repr__(self):
        return f'<Gaming emotion tag: {self.tag}>'


class GamingInterruptionTag(db.Model):
    __tablename__ = 'gaming_interruption_tags'
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, unique=True)

    session_interruptions = db.relationship('GamingSessionInterruption',
                                            secondary=interruptions_tags,
                                            primaryjoin='GamingInterruptionTag.id == '
                                                        'gaming_interruptions_tags.c.tag_id',
                                            secondaryjoin='gaming_interruptions_tags.c.interruption_id == '
                                                          'GamingSessionInterruption.id',
                                            back_populates='tags')

    def __repr__(self):
        return f'<Gaming interruption tag: {self.tag}>'


class GamingSessionInterruption(db.Model):
    __tablename__ = 'gaming_session_interruptions'
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('gaming_session_records.id'))
    tag_id = db.Column(db.Integer, db.ForeignKey('gaming_interruption_tags.id'))
    start_time = db.Column(db.DateTime)  # local time
    stop_time = db.Column(db.DateTime)  # local time
    duration = db.Column(db.Integer)

    tags = db.relationship('GamingInterruptionTag',
                           secondary=interruptions_tags,
                           primaryjoin='GamingSessionInterruption.id == gaming_interruptions_tags.c.interruption_id',
                           secondaryjoin='gaming_interruptions_tags.c.tag_id == GamingInterruptionTag.id',
                           back_populates='session_interruptions')
    record = db.relationship('GamingSessionRecord', back_populates='session_interruptions')

    def __repr__(self):
        return f'<Gaming session {self.record_id}, interruption {self.tag_id}>'


class GamingNote(db.Model):
    __tablename__ = 'gaming_notes'
    id = db.Column(db.Integer, primary_key=True)
    date_added = db.Column(db.DateTime)  # server time
    record_id = db.Column(db.Integer, db.ForeignKey('gaming_session_records.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('gaming_games.id'))
    note = db.Column(db.String)
    important = db.Column(db.Boolean, default=False)

    record = db.relationship('GamingSessionRecord', back_populates='notes')
    game = db.relationship('Game', back_populates='notes')

    def __repr__(self):
        return f'<Gaming note {self.id}>'
