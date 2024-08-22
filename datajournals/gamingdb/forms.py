from flask_wtf import FlaskForm
from wtforms import IntegerField, DateTimeLocalField, BooleanField, SubmitField, Form, FieldList, FormField, \
    HiddenField, StringField
from wtforms.validators import Optional, InputRequired, NumberRange

from datajournals.base_methods import BaseNoteForm, UnvalidatedParamField, UnvalidatedParamMultipleField


class NoteForm(BaseNoteForm):
    game = UnvalidatedParamField(label='Game', validators=[Optional()])


class InterruptionSubform(Form):
    interruption = UnvalidatedParamMultipleField(label='Interruption', validators=[InputRequired()])
    start_time = DateTimeLocalField(label='Started', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    stop_time = DateTimeLocalField(label='Stopped', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    duration = IntegerField(label='Duration of interruption', validators=[Optional()])
    delete_interruption = BooleanField(label='Delete?')
    interruption_id = HiddenField()


class InterruptionForm(FlaskForm):
    interruption = UnvalidatedParamMultipleField(label='Sources', validators=[InputRequired()])
    start_time = DateTimeLocalField(label='Started', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    stop_time = DateTimeLocalField(label='Stopped', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    duration = IntegerField(label='Duration', validators=[Optional()])
    add_interruption = BooleanField(label='Add another interruption')
    add_note = BooleanField('Add a note')
    record_id = HiddenField()
    submit = SubmitField(label='Save')


class TagForm(FlaskForm):
    tag = StringField(label='Tag', validators=[InputRequired()])
    submit = SubmitField(label='Save')


class RatingForm(FlaskForm):
    rating = IntegerField(label='Rating', validators=[NumberRange(min=0, max=4)])
    emotions = UnvalidatedParamMultipleField(label='Emotions', validators=[Optional()])
    add_note = BooleanField('Add a note')
    submit = SubmitField(label='Save')


class RecordForm(FlaskForm):
    start_time = DateTimeLocalField(label='Time started', format='%Y-%m-%dT%H:%M', validators=[InputRequired()])
    stop_time = DateTimeLocalField(label='Time stopped', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    session_rating = IntegerField(label='Session rating', validators=[Optional(), NumberRange(max=4, min=0)])
    game = UnvalidatedParamField(label='Game', validators=[InputRequired()])
    emotions = UnvalidatedParamMultipleField(label='Emotions', validators=[Optional()])
    interruptions = FieldList(label='Interruptions', unbound_field=FormField(InterruptionSubform))
    add_note = BooleanField(label='Add note')
    add_interruption = BooleanField(label='Add interruption')
    submit = SubmitField(label='Save')
