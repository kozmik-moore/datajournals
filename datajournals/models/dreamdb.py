from datajournals.extensions import db

dream_subjects = db.Table('dream_subjects',
                          db.Column('record_id', db.Integer, db.ForeignKey('dream_record.id')),
                          db.Column('tag_id', db.Integer, db.ForeignKey('dream_subject_tag.id'))
                          )

dream_descriptors = db.Table('dream_descriptors',
                             db.Column('record_id', db.Integer, db.ForeignKey('dream_record.id')),
                             db.Column('tag_id', db.Integer, db.ForeignKey('dream_descriptor_tag.id'))
                             )

dream_emotions = db.Table('dream_emotions',
                          db.Column('record_id', db.Integer, db.ForeignKey('dream_record.id')),
                          db.Column('tag_id', db.Integer, db.ForeignKey('dream_emotion_tag.id'))
                          )


class DreamRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record = db.Column(db.Text)
    record_date = db.Column(db.Date)  # date occurred - input from user
    time_of_day = db.Column(db.Text)
    sleep_type = db.Column(db.Text)
    subjects = db.relationship('DreamSubjectTag', secondary=dream_subjects, backref='records', lazy=True)
    descriptors = db.relationship('DreamDescriptorTag', secondary=dream_descriptors, backref='records', lazy=True)
    emotions = db.relationship('DreamEmotionTag', secondary=dream_emotions, backref='records', lazy=True)
    notes = db.relationship('DreamNote', backref='record', lazy=True, cascade='all, delete')

    def __repr__(self):
        return f'<Dream record date: "{self.record_date}">'


class DreamSubjectTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, unique=True)

    def __repr__(self):
        return f'<Dream subject: "{self.tag}">'


class DreamDescriptorTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, unique=True)

    def __repr__(self):
        return f'<Dream descriptor: "{self.tag}">'


class DreamEmotionTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, unique=True)

    def __repr__(self):
        return f'<Dream emotion: "{self.tag}">'


class DreamNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('dream_record.id'))
    note = db.Column(db.String)
    important = db.Column(db.Boolean, default=False)
    date_added = db.Column(db.DateTime)
    last_edited = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Dream note: "{self.note[:30]}">'
