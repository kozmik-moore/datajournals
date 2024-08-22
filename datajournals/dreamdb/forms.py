from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, BooleanField, SelectField, DateField
from wtforms.fields.simple import StringField
from wtforms.validators import InputRequired, Optional

from datajournals.base_methods import UnvalidatedParamMultipleField


class DreamCreateForm(FlaskForm):
    record = TextAreaField(label='Record', validators=[InputRequired()])
    record_date = DateField('Date', format='%Y-%m-%d', validators=[InputRequired()])
    time_of_day = SelectField(label='Time of day',
                              choices=[(x, x) for x in ('early morning',
                                                        'late morning',
                                                        'early afternoon',
                                                        'late afternoon',
                                                        'early evening',
                                                        'late evening')
                                       ])
    sleep_type = SelectField(label='Sleep type',
                             choices=[(x, x) for x in ('regular sleep',
                                                       'long nap',
                                                       'short nap',
                                                       'daydream')]
                             )
    subjects = UnvalidatedParamMultipleField(label='Subjects')
    descriptors = UnvalidatedParamMultipleField(label='Descriptors')
    emotions = UnvalidatedParamMultipleField(label='Emotions')
    add_note = BooleanField(label='Add a note')
    submit = SubmitField(label='Save')


class DreamNoteForm(FlaskForm):
    note = TextAreaField(label='Note')
    important = BooleanField(label='Important')
    submit = SubmitField('Save')


class TagForm(FlaskForm):
    tag = StringField(validators=[InputRequired()])
    submit = SubmitField(label='Save')


class RecordSearchForm(FlaskForm):
    content = StringField(label='Content', validators=[Optional()])
    subjects = UnvalidatedParamMultipleField(label='Subjects', validators=[Optional()])
    descriptors = UnvalidatedParamMultipleField(label='Descriptors', validators=[Optional()])
    emotions = UnvalidatedParamMultipleField(label='Emotions', validators=[Optional()])
    time_of_day = SelectField(label='Time of day',
                              choices=[(x, x) for x in ('',
                                                        'early morning',
                                                        'late morning',
                                                        'early afternoon',
                                                        'late afternoon',
                                                        'early evening',
                                                        'late evening')
                                       ],
                              validators=[Optional()]
                              )
    sleep_type = SelectField(label='Sleep type',
                             choices=[(x, x) for x in ('',
                                                       'regular sleep',
                                                       'long nap',
                                                       'short nap',
                                                       'daydream')
                                      ],
                             validators=[Optional()]
                             )
    submit = SubmitField(label='Search')


class NoteSearchForm(FlaskForm):
    content = StringField(label='Content', validators=[Optional()])
    hasrecord = SelectField('Has record', choices=[(x, x) for x in ('', 'yes', 'no')])
    important = SelectField('Marked important', choices=[(x, x) for x in ('', 'yes', 'no')])
    submit = SubmitField(label='Search')


class TagSearchForm(FlaskForm):
    content = StringField(label='Content', validators=[Optional()])
    submit = SubmitField(label='Search')

