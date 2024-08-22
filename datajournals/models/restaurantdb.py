from datajournals.extensions import db

restaurant_tags = db.Table('restaurant_tags',
                           db.Column('restaurant_id', db.Integer, db.ForeignKey('restaurant_record.id')),
                           db.Column('tag_id', db.Integer, db.ForeignKey('restaurant_tag.id'))
                           )


class RestaurantRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    date_added = db.Column(db.DateTime)
    description = db.Column(db.Text)
    avoid = db.Column(db.Boolean, default=False)
    tags = db.relationship('RestaurantTag', secondary=restaurant_tags, backref='records', lazy=True)
    visits = db.relationship('RestaurantVisit', cascade='all, delete', backref='record', lazy=True)
    notes = db.relationship('RestaurantNote', cascade='all, delete', backref='record', lazy=True)

    def __repr__(self):
        return f'<Restaurant "{self.name}">'


class RestaurantVisit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant_record.id'))
    date = db.Column(db.DateTime)
    meal = db.Column(db.Text)
    visit_rating = db.Column(db.String)
    price_rating = db.Column(db.String)
    comments = db.Column(db.Text)

    def __repr__(self):
        return f'<Restaurant History "{self.restaurant_id, self.date}">'


class RestaurantTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, unique=True)

    def __repr__(self):
        return f'<Restaurant Tag "{self.tag}">'


class RestaurantNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant_record.id'))
    note = db.Column(db.String)
    important = db.Column(db.Boolean, default=False)
    date_added = db.Column(db.DateTime)
    last_edited = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Restaurant Note "{self.note[:30]}">'
