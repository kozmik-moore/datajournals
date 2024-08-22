from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, MultipleFileField, DateTimeLocalField, HiddenField
from wtforms.fields.choices import SelectField
from wtforms.fields.form import FormField
from wtforms.fields.list import FieldList
from wtforms.fields.simple import StringField, BooleanField
from wtforms.form import Form
from wtforms.validators import InputRequired, Optional

from datajournals.base_methods import UnvalidatedParamMultipleField


class AttachmentsSubform(Form):
    attachment_id = HiddenField(label='Attachment id')
    filename = StringField(label='Filename', validators=[InputRequired()])
    delete = BooleanField(label='Delete?')


class CreateRecordForm(FlaskForm):
    record = TextAreaField(label='Record', validators=[InputRequired()])
    record_date = DateTimeLocalField('Date', format='%Y-%m-%dT%H:%M', validators=[InputRequired()])
    parent_id = HiddenField('Parent')
    subjects = UnvalidatedParamMultipleField(label='Subjects')
    descriptors = UnvalidatedParamMultipleField(label='Descriptors')
    emotions = UnvalidatedParamMultipleField(label='Emotions')
    unfinished = BooleanField(label='Unfinished')
    watched = BooleanField(label='Watch')
    attachments = MultipleFileField('Upload File(s)', render_kw={'enctype': 'multipart/form-data'})
    submit = SubmitField(label='Save')


class UpdateRecordForm(FlaskForm):
    record = TextAreaField(label='Record', validators=[InputRequired()])
    record_date = DateTimeLocalField(label='Date', format='%Y-%m-%dT%H:%M', validators=[InputRequired()])
    subjects = UnvalidatedParamMultipleField(label='Subjects')
    descriptors = UnvalidatedParamMultipleField(label='Descriptors')
    emotions = UnvalidatedParamMultipleField(label='Emotions')
    unfinished = BooleanField(label='Unfinished')
    watched = BooleanField(label='Watch')
    add_attachments = MultipleFileField('Upload File(s)', render_kw={'enctype': 'multipart/form-data'})
    attachments = FieldList(label='Delete attachments', unbound_field=FormField(AttachmentsSubform))
    submit = SubmitField(label='Save')


class AttachmentsForm(FlaskForm):
    record_id = HiddenField(label='Record')
    attachments = MultipleFileField(label='Upload File(s)', render_kw={'enctype': 'multipart/form-data'})
    submit = SubmitField(label='Save')


class TagForm(FlaskForm):
    tag = StringField(label='Tag name', validators=[InputRequired()])
    submit = SubmitField(label='Save')


class SearchRecordForm(FlaskForm):
    content = StringField(label='Content', validators=[Optional()])
    linktype = SelectField(label='Link type', choices=[(x, x) for x in ['', 'parent', 'child', 'both', 'neither']])
    subjects = UnvalidatedParamMultipleField(label='Subjects')
    descriptors = UnvalidatedParamMultipleField(label='Descriptors')
    emotions = UnvalidatedParamMultipleField(label='Emotions')
    unfinished = SelectField(label='Unfinished', choices=[(x, x) for x in ('', 'yes', 'no')])
    watched = SelectField(label='Watched', choices=[(x, x) for x in ('', 'yes', 'no')])
    submit = SubmitField(label='Search')


class SearchTagForm(FlaskForm):
    content = StringField(label='Content', validators=[InputRequired()])
    submit = SubmitField(label='Search')
