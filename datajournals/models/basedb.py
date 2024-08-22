from datajournals import db


class BaseRecord(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    record = db.Column(db.Text)
    record_date = db.Column(db.DateTime)
    date_added = db.Column(db.DateTime)

    def __repr__(self):
        return f'{self.__tablename__.replace("_", " ").title()} date: {self.record_date}'


class BaseTag(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, unique=True)

    def __repr__(self):
        return f'{self.__tablename__.replace("_", " ").title()} tag: "{self.tag}"'


class BaseNote(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    record_id = None
    note = db.Column(db.Text)
    important = db.Column(db.Boolean, default=False)
    date_added = db.Column(db.DateTime)
    last_edited = db.Column(db.DateTime)

    def __repr__(self):
        return f'<{self.__tablename__.replace("_", " ").title()} note: "{self.note[:30]}">'


class BaseAttachment(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    record_id = None
    filename = db.Column(db.String)
    uuid = db.Column(db.String)

    def __repr__(self):
        return f'<{self.__tablename__.replace("_", " ").title()} filename: "{self.filename}">'
