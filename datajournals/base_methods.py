import datetime
import os
from os.path import join
from uuid import uuid4

import pandas as pd
from flask import current_app
from flask_wtf import FlaskForm
from markupsafe import Markup, escape
from sqlalchemy import MetaData, inspect
from wtforms import TextAreaField, SubmitField, DateTimeLocalField, BooleanField, SelectMultipleField, SelectField
from wtforms.validators import InputRequired, ValidationError
from wtforms.widgets import Select, html_params

from datajournals import db


def create_init_tables_function(models: tuple, pseudodb_name: str, table_names: tuple = ()):
    """
    Creates a function for initializing tables for a pseudo-database (set of tables corresponding to specific sets of
    data in a database)
    :param models: a collection of SQLAlchemy models
    :param table_names: a collection of strings representing SQLAlchemy tables
    :param pseudodb_name: the name of the pseudo-database
    :return: a function
    """

    def init_tables(create_tables: bool = True):
        """
        Drop specified tables and create new empty ones
        :return: None
        """

        # Create metadata and inspection objects
        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        inspector = inspect(db.engine)

        # Check for existing intermediary tables
        tmp = list(table_names).copy()
        for i in range(len(table_names)):
            if not inspector.has_table(table_names[i]):
                tmp.remove(table_names[i])
        meta_tables = [metadata.tables[name] for name in tmp]

        # Check for existing models
        tmp = list(models).copy()
        for i in range(len(models)):
            if not inspector.has_table(models[i].__table__.name):
                tmp.remove(models[i])

        all_tables = meta_tables + [x.__table__ for x in models]

        db.metadata.drop_all(db.engine, tables=all_tables)
        current_app.logger.warning(f'Dropped all tables associated with {pseudodb_name}.')
        if create_tables:
            db.create_all()
            db.session.commit()
            current_app.logger.info(f'Created tables for {pseudodb_name}.')

    return init_tables


def create_init_tags_function(tags_dict: dict[db.Model: ()]):
    """
    Creates a function for initializing default tags on a pseudo-database (set of tables corresponding to specific
    sets of data in a database)
    :param tags_dict: a dict where the keys are tags models and the values are collections of default tags
    :return: a function
    """

    def init_tags():
        """
        Create and add default tags to the pseudo-database
        :return: None
        """
        all_objects = []
        for model in tags_dict:
            objects = []
            db_tags = [x.tag for x in model.query.all()]
            tags = tags_dict[model]
            for tag in tags:
                if tag not in db_tags:
                    objects.append(model(tag=tag))
            all_objects += objects

        db.session.add_all(all_objects)
        db.session.commit()

    return init_tags


def convert_options_to_tagmodels(tags, tagmodel):
    """
    Converts supplied tags to SQLAlchemy objects of the given type. Returned list of tagmodel objects may include
    objects that have not been committed to a database.
    :param tags: a list of str representing tags inside or outside the database
    :param tagmodel: the specified type of SQLAlchemy tag model
    :return: list of tagmodel objects
    """

    tagsobjects = []
    query = tagmodel.query.all()  # Get all tags from database
    dbtags = {x.tag: x for x in query}  # Map tags to tagmodel objects
    for t in tags:
        st = t.strip()
        if st in dbtags.keys():
            tagsobjects.append(dbtags[st])
        else:
            obj = tagmodel()
            obj.tag = st
            tagsobjects.append(obj)

    tagsobjects = sorted(tagsobjects, key=lambda e: e.tag)
    return tagsobjects


def convert_tagmodels_to_options(tagmodel,
                                 opt_args=None,
                                 placeholder=True,
                                 message='Select a tag...',
                                 ph_args=None
                                 ):
    """
    Converts tagmodel objects to a list of options for use in an HTML select input
    :param opt_args: a dict where the keys represent HTML parameters for option tags
    :param tagmodel: the SQLAlchemy model of the tag
    :param placeholder: if True, indicates that the returned list should include a select placeholder
    :param message: a placeholder message
    :param ph_args: arguments for the placeholder option
    :return: list[tuple(int, str, str)]
    """
    if opt_args is None:
        opt_args = {}
    options = []
    all_tags = tagmodel.query.all()  # Get all tags for this model
    for obj in all_tags:  # Create mapping
        tag = obj.tag
        options.append(
            (tag, tag, opt_args)
        )
    options = sorted(options, key=lambda e: e[0])
    if ph_args is None:
        ph_args = dict(selected=True, hidden=True)  # Default params for placeholder option
    if placeholder:
        if isinstance(ph_args, str):
            ph_args = {x: True for x in ph_args.split(' ')}
        options.insert(0,
                       ('', message, ph_args))
    return options


def get_attachments(paths, dirkey, model):
    """
    Creates a list of attachment models and manages files
    :param paths: a list of paths to files to be attached
    :param dirkey: the config key that indicates where attachment files are kept
    :param model: the attachment model type
    :return:
    """
    attachments = []
    for file in paths:
        if file.filename:  # Check if this is a file and not an octet-stream.
            uuid = str(uuid4())
            file.save(join(current_app.config[dirkey], uuid))
            attachments.append(model(filename=file.filename,
                                     uuid=uuid
                                     )
                               )
    return attachments


def remove_attachment_file(uuid, dirkey):
    p = join(current_app.config[dirkey], uuid)
    try:
        os.remove(p)
        return 'File deleted.'
    except FileNotFoundError as err:
        return err


def get_duration_tuple(start: datetime.datetime = None, stop: datetime.datetime = None, duration: int = None):
    """
    Calculates the missing value from a duration tuple, given two of its operands
    :param start: a datetime representing the start of the duration
    :param stop: a datetime representing the end
    :param duration: the duration between start and stop, in minutes
    :return: a tuple of start and stop times and the duration between
    """
    if start is not None and stop is not None:
        duration = (stop - start).total_seconds() // 60
    elif start is not None and duration is not None:
        stop = start + datetime.timedelta(minutes=duration)
    elif stop is not None and duration is not None:
        start = stop - datetime.timedelta(minutes=duration)
    return start, stop, duration


def timedelta_to_str(td: pd.Timedelta):
    if type(td) is datetime.timedelta:
        td = pd.Timedelta(td)
    if type(td) is pd.Timedelta:
        d = td.days
        d_desc = ' days' if d > 1 else ' day' if d == 1 else ''
        h = td.seconds // 3600
        h_desc = ' hours' if h > 1 else ' hour' if h == 1 else ''
        m = (td.seconds // 60) % 60
        m_desc = ' minutes' if m > 1 else ' minute' if m == 1 else ''
        return (f'{d if d else ""}{d_desc}{", " if d and h or d and m else ""}'
                f'{h if h else ""}{h_desc}{", " if h and m else ""}'
                f'{m if m else ""}{m_desc}')
    else:
        return ''


class BaseRecordForm(FlaskForm):
    record = TextAreaField(label='Record', validators=[InputRequired()])
    record_date = DateTimeLocalField(label='Date', format='%Y-%m-%dT%H:%M', validators=[InputRequired()])
    submit = SubmitField(label='Save')


class BaseNoteForm(FlaskForm):
    note = TextAreaField(label='Note')
    important = BooleanField(label='Important')
    submit = SubmitField(label='Save')


class ParamSelect(Select):
    """
    A select widget with methods which accept option parameters
    """
    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        if self.multiple:
            kwargs["multiple"] = True
        flags = getattr(field, "flags", {})
        for k in dir(flags):
            if k in self.validation_attrs and k not in kwargs:
                kwargs[k] = getattr(flags, k)
        html = ["<select %s>" % html_params(name=field.name, **kwargs)]
        if field.has_groups():
            for group, choices in field.iter_groups():
                html.append("<optgroup %s>" % html_params(label=group))
                for val, label, selected, opt_args in choices:
                    html.append(self.render_option(val, label, selected, opt_args))
                html.append("</optgroup>")
        else:
            for val, label, selected, opt_args in field.iter_choices():
                html.append(self.render_option(val, label, selected, opt_args))
        html.append("</select>")
        return Markup("".join(html))

    @classmethod
    def render_option(cls, value, label, selected, opt_args=None, **kwargs):
        if value is True:
            # Handle the special case of a 'True' value.
            value = str(value)

        if isinstance(opt_args, str):
            opt_args = {i: True for i in opt_args.split(' ')}

        options = dict(kwargs, value=value)
        if selected:
            options["selected"] = True
        if opt_args:
            options.update(opt_args)
        return Markup(
            "<option {}>{}</option>".format(html_params(**options), escape(label))
        )


class ParamField(SelectField):
    """
    A select field with methods which accept option parameters
    """
    widget = ParamSelect()

    def _choices_generator(self, choices):
        if not choices:
            _choices = []

        elif isinstance(choices[0], (list, tuple)):
            if any(len(x) != 3 for x in choices):
                msg = ('choices iterables must contain "value", "label", and "option arguments"\n'
                       'example: (1, "tag", "disabled")')
                raise ValueError(self.gettext(msg))
            _choices = choices

        else:
            _choices = zip(choices, choices, ['' for _ in range(len(choices))])

        for value, label, opt_args, in _choices:
            yield value, label, self.coerce(value) in self.data, opt_args

    def pre_validate(self, form):
        if self.choices is None:
            raise TypeError(self.gettext("Choices cannot be None."))

        if not self.validate_choice:
            return

        for _, _, match, _ in self.iter_choices():
            if match:
                break
        else:
            raise ValidationError(self.gettext("Not a valid choice."))
        
        
class UnvalidatedParamField(ParamField):
    """
    A select field with methods which accept option parameters and has no pre-validation
    """
    def pre_validate(self, form):
        pass


class UnvalidatedParamMultipleField(UnvalidatedParamField, SelectMultipleField):
    """
    A mulltiple select field with methods which accept option parameters and has no pre-validation
    """
    widget = ParamSelect(multiple=True)
