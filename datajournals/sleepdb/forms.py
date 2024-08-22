from flask_wtf import FlaskForm
from wtforms import (DateTimeLocalField, IntegerField, BooleanField, SubmitField, TextAreaField, HiddenField,
                     Form, FieldList, FormField, StringField)
from wtforms.validators import InputRequired, Optional, NumberRange

from datajournals.base_methods import UnvalidatedParamMultipleField, UnvalidatedParamField


class SleepInterruptionSubform(Form):
    interruption = UnvalidatedParamMultipleField(label='Interruption', validators=[InputRequired()])
    start = DateTimeLocalField(label='Start time', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    stop = DateTimeLocalField(label='Stop time', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    duration = IntegerField(label='Duration of interruption', validators=[Optional()])
    delete_interruption = BooleanField(label='Delete?')
    interruption_id = HiddenField()


class SleepRecordForm(FlaskForm):
    time_retire = DateTimeLocalField(label='Time retired to bed', format='%Y-%m-%dT%H:%M', validators=[InputRequired()])
    time_start = DateTimeLocalField(label='Time started sleep', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    time_stop = DateTimeLocalField(label='Time stopped sleep', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    time_rise = DateTimeLocalField(label='Time rose from bed', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    rating = IntegerField(label='Rating', validators=[NumberRange(max=4, min=0), Optional()])
    emotions = UnvalidatedParamMultipleField(label='Emotions')
    locations = UnvalidatedParamMultipleField(label='Locations')
    sensations = UnvalidatedParamMultipleField(label='Sensations')
    interruptions = FieldList(label='Interruptions', unbound_field=FormField(SleepInterruptionSubform))
    add_note = BooleanField(label='Add note')
    add_interruption = BooleanField(label='Add an interruption')
    submit = SubmitField(label='Save')


class SleepInterruptionForm(FlaskForm):
    """
    Parent form for InterruptionForm
    """
    interruption = UnvalidatedParamMultipleField(label='Interruptions', validators=[InputRequired()])
    start = DateTimeLocalField(label='Start time', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    stop = DateTimeLocalField(label='Stop time', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    duration = IntegerField(label='Duration', validators=[Optional()])
    add_interruption = BooleanField(label='Add another interruption')
    add_note = BooleanField(label='Add a note')
    record_id = HiddenField(label='Record id')
    submit = SubmitField(label='Save')


class SleepNoteForm(FlaskForm):
    note = TextAreaField(label='Note')
    important = BooleanField(label='Important')
    submit = SubmitField(label='Save')


class TagForm(FlaskForm):
    tag = StringField(label='Tag', validators=[InputRequired()])
    submit = SubmitField(label='Save')


class RatingForm(FlaskForm):
    rating = IntegerField(label='Rating', validators=[NumberRange(max=4, min=0), InputRequired()])
    emotions = UnvalidatedParamMultipleField(label='Emotions')
    sensations = UnvalidatedParamMultipleField(label='Sensations')
    submit = SubmitField(label='Save')
