from datajournals.extensions import db

journal_subjects = db.Table('journal_subjects',
                            db.Column('journal_id', db.Integer, db.ForeignKey('journal_record.id')),
                            db.Column('tag_id', db.Integer, db.ForeignKey('journal_subject_tag.id'))
                            )

journal_descriptors = db.Table('journal_descriptors',
                               db.Column('journal_id', db.Integer, db.ForeignKey('journal_record.id')),
                               db.Column('tag_id', db.Integer, db.ForeignKey('journal_descriptor_tag.id'))
                               )

journal_emotions = db.Table('journal_emotions',
                            db.Column('journal_id', db.Integer, db.ForeignKey('journal_record.id')),
                            db.Column('tag_id', db.Integer, db.ForeignKey('journal_emotion_tag.id'))
                            )


class JournalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record = db.Column(db.Text)
    record_date = db.Column(db.DateTime)  # date occurred - input from user
    date_added = db.Column(db.DateTime)  # date added - input from server
    unfinished = db.Column(db.Boolean)
    watched = db.Column(db.Boolean)
    parent_id = db.Column(db.Integer, db.ForeignKey('journal_record.id'))
    subjects = db.relationship('JournalSubjectTag', secondary=journal_subjects, backref='records', lazy=True)
    descriptors = db.relationship('JournalDescriptorTag', secondary=journal_descriptors, backref='records', lazy=True)
    emotions = db.relationship('JournalEmotionTag', secondary=journal_emotions, backref='records', lazy=True)
    parent = db.relationship('JournalRecord', remote_side=[id], backref='children')
    attachments = db.relationship('JournalAttachment', backref='record', lazy=True, cascade='all, delete')

    def __repr__(self):
        return f'<Journal record date: "{self.record_date}">'


class JournalSubjectTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, unique=True)

    def __repr__(self):
        return f'<Journal subject: "{self.tag}">'


class JournalDescriptorTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, unique=True)

    def __repr__(self):
        return f'<Journal descriptor: "{self.tag}">'


class JournalEmotionTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, unique=True)

    def __repr__(self):
        return f'<Journal emotion: "{self.tag}">'


class JournalAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    journal_id = db.Column(db.Integer, db.ForeignKey('journal_record.id'))
    filename = db.Column(db.String)
    uuid = db.Column(db.String)

    def __repr__(self):
        return f'<Journal attachment: "{self.filename}">'
