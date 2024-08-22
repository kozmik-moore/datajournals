from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, BooleanField, DateTimeLocalField, SelectField
from wtforms.validators import InputRequired

from datajournals.base_methods import UnvalidatedParamMultipleField, ParamField, UnvalidatedParamField


class RestaurantForm(FlaskForm):
    name = StringField(label='Name', validators=[InputRequired()])
    description = TextAreaField(label='Description')
    add_visit = BooleanField(label='Add a visit')
    avoid = BooleanField(label='Avoid')
    add_tag = SubmitField(label="Add Tag")
    tags = UnvalidatedParamMultipleField(label='Tags')
    submit = SubmitField(label='Save')


class VisitForm(FlaskForm):
    name = ParamField(label='Restaurant name')
    date = DateTimeLocalField('Date', format='%Y-%m-%dT%H:%M', validators=[InputRequired()])
    meal = SelectField(label='Meal',
                       choices=(('', ''),
                                ('breakfast', 'breakfast'),
                                ('lunch', 'lunch'),
                                ('dinner', 'dinner'),
                                ('snack', 'snack'),
                                ('brunch', 'brunch'),
                                ('drinks', 'drinks'),
                                )
                       )
    price_rating = SelectField(label='Price Rating',
                               choices=[('', ''), ('$', '$'), ('$$', '$$'), ('$$$', '$$$'), ('$$$$', '$$$$')
                                        ]
                               )
    visit_rating = SelectField(label='Visit Rating',
                               choices=[('', ''),
                                        ('Loved it!', 'Loved it!'),
                                        ('Liked it', 'Liked it'),
                                        ('It was okay', 'It was okay'),
                                        ('Did not like it', 'Did not like it')]
                               )
    comments = TextAreaField(label='Comments')
    submit = SubmitField('Save')


class NoteForm(FlaskForm):
    name = UnvalidatedParamField(label='Name')
    note = TextAreaField(label='Note')
    important = BooleanField(label='Important')
    submit = SubmitField('Save')


class TagForm(FlaskForm):
    tag = StringField(label='Tag', validators=[InputRequired()])
    submit = SubmitField(label='Save')
