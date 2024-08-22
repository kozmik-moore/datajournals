from datajournals import db
from datajournals.models.basedb import BaseRecord, BaseTag, BaseNote, BaseAttachment

record_descriptors = db.Table('health_record_descriptors',
                              db.Column('record_id', db.Integer, db.ForeignKey('health_record.id')),
                              db.Column('descriptor_id', db.Integer, db.ForeignKey('health_descriptor_tag.id')))

record_emotions = db.Table('health_record_emotions',
                           db.Column('record_id', db.Integer, db.ForeignKey('health_record.id')),
                           db.Column('emotion_id', db.Integer, db.ForeignKey('health_emotion_tag.id')))


class HealthRecord(BaseRecord):
    _name = 'health'
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('health_record.id'))
    is_tracked = db.Column(db.Boolean, default=False)
    parent = db.relationship('HealthRecord', remote_side=[id], backref='children')
    descriptors = db.relationship('HealthDescriptorTag', secondary=record_descriptors, backref='records', lazy=True)
    emotions = db.relationship('HealthEmotionTag', secondary=record_emotions, backref='records', lazy=True)
    glucose_record = db.relationship('HealthGlucoseRecord', backref='record', lazy=True, cascade='all, delete')
    cardio_record = db.relationship('HealthCardioRecord', backref='record', lazy=True, cascade='all, delete')
    pain_record = db.relationship('HealthPainRecord', backref='record', lazy=True, cascade='all, delete')
    weight_record = db.relationship('HealthWeightRecord', backref='record', lazy=True, cascade='all, delete')
    notes = db.relationship('HealthNote', backref='record', lazy=True, cascade='all, delete')
    attachments = db.relationship('HealthAttachment', backref='record', lazy=True, cascade='all, delete')


class HealthDescriptorTag(BaseTag):
    _name = 'health'


class HealthEmotionTag(BaseTag):
    _name = 'emotion'


class HealthGlucoseRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('health_record.id'))
    measure = db.Column(db.Integer)
    units = db.Column(db.String, default='mg/dL')


class HealthCardioRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('health_record.id'))
    systolic = db.Column(db.Integer)
    diastolic = db.Column(db.Integer)
    heart_rate = db.Column(db.Integer)


class HealthPainRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('health_record.id'))
    level = db.Column(db.Integer)
    description = db.Column(db.Text)


class HealthWeightRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('health_record.id'))
    measure = db.Column(db.Float)
    units = db.Column(db.String, default='lbs')


class HealthNote(BaseNote):
    _name = 'health'
    record_id = db.Column(db.Integer, db.ForeignKey('health_record.id'))


class HealthAttachment(BaseAttachment):
    _name = 'health'
    record_id = db.Column(db.Integer, db.ForeignKey('health_record.id'))
