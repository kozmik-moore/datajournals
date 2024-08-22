from wtforms import HiddenField, MultipleFileField, IntegerField, StringField, TextAreaField, BooleanField, FloatField
from wtforms.validators import Optional

from datajournals.base_methods import BaseRecordForm, BaseNoteForm, UnvalidatedParamMultipleField


class RecordForm(BaseRecordForm):
    record = TextAreaField(label='Record', validators=[Optional()])
    parent_id = HiddenField(label='Parent')
    descriptors = UnvalidatedParamMultipleField(label='Descriptors')
    emotions = UnvalidatedParamMultipleField(label='Emotions')
    is_tracked = BooleanField(label='Add to tracked records')
    attachments = MultipleFileField('Upload File(s)', render_kw={'enctype': 'multipart/form-data'})
    add_note = BooleanField(label='Add note')

    # Glucose record fields
    glucose_measure = IntegerField(label='Glucose', validators=[Optional()])
    glucose_units = StringField(label='Units', validators=[Optional()])

    # Cardio record fields
    systolic = IntegerField(label='Systolic', validators=[Optional()])
    diastolic = IntegerField(label='Diastolic', validators=[Optional()])
    heart_rate = IntegerField(label='Heart rate', validators=[Optional()])

    # Pain record fields
    pain_level = IntegerField(label='Pain level', validators=[Optional()])
    pain_description = TextAreaField(label='Description', validators=[Optional()])

    # Weight record fields
    weight_measure = FloatField(label='Weight', validators=[Optional()])
    weight_units = StringField(label='Units', validators=[Optional()])


class NoteForm(BaseNoteForm):
    """
    BaseNoteForm
    """
