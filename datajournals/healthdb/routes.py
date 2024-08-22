from datetime import datetime
from os.path import join

from flask import render_template, request, current_app, send_file, redirect, url_for
from flask_login import login_required

from datajournals import db
from datajournals.authorization import requires_access
from datajournals.base_methods import convert_options_to_tagmodels, get_attachments, convert_tagmodels_to_options
from datajournals.healthdb import bp
from datajournals.healthdb.forms import RecordForm, NoteForm
from datajournals.models.healthdb import HealthRecord, HealthNote, HealthDescriptorTag, HealthEmotionTag, \
    HealthGlucoseRecord, HealthWeightRecord, HealthPainRecord, HealthCardioRecord, HealthAttachment


@bp.route('/')
@login_required
@requires_access(['admin'])
def index():
    return render_template('healthdb/index.html')


@bp.route('/records')
@login_required
@requires_access(['admin'])
def records():
    page = request.args.get('page', 1, type=int)
    query = HealthRecord.query.order_by(HealthRecord.record_date.desc())
    count = query.count()
    pagination = query.paginate(page=page, per_page=10)
    return render_template('healthdb/records.html', paginator=pagination, count=count)


@bp.route('/record/<int:record_id>/')
@login_required
@requires_access(['admin'])
def record(record_id):
    page = request.args.get('page', 1, type=int)
    record_ = HealthRecord.query.filter_by(id=record_id).first()
    notes_ = HealthNote.query.filter(HealthNote.record_id == record_id).paginate(page=page, per_page=10)
    return render_template('healthdb/record.html', record=record_, paginator=notes_)


@bp.route('/descriptors/')
@login_required
@requires_access(['admin'])
def descriptors():
    page = request.args.get('page', 1, type=int)
    query = HealthDescriptorTag.query.order_by(HealthDescriptorTag.tag.asc()).paginate(page=page, per_page=10)
    return render_template('healthdb/descriptors.html', paginator=query)


@bp.route('/descriptor/<int:descriptor_id>/')
@login_required
@requires_access(['admin'])
def descriptor(descriptor_id):
    page = request.args.get('page', 1, type=int)
    descriptor_ = HealthDescriptorTag.query.filter_by(id=descriptor_id).first()
    record_ids = [x.id for x in descriptor_.records]
    records_query = HealthRecord.query \
        .filter(HealthRecord.id.in_(record_ids)) \
        .order_by(HealthRecord.record_date.desc()) \
        .paginate(page=page, per_page=10)
    return render_template('healthdb/descriptor.html', descriptor=descriptor_, paginator=records_query)


@bp.route('/emotions/')
@login_required
@requires_access(['admin'])
def emotions():
    page = request.args.get('page', 1, type=int)
    query = HealthEmotionTag.query.order_by(HealthEmotionTag.tag.asc()).paginate(page=page, per_page=10)
    return render_template('healthdb/emotions.html', paginator=query)


@bp.route('/emotion/<int:emotion_id>/')
@login_required
@requires_access(['admin'])
def emotion(emotion_id):
    page = request.args.get('page', 1, type=int)
    emotion_ = HealthEmotionTag.query.filter_by(id=emotion_id).first()
    record_ids = [x.id for x in emotion_.records]
    records_query = HealthRecord.query \
        .filter(HealthRecord.id.in_(record_ids)) \
        .order_by(HealthRecord.record_date.desc()) \
        .paginate(page=page, per_page=10)
    return render_template('healthdb/emotion.html', emotion=emotion_, paginator=records_query)


@bp.route('/glucose/')
@bp.route('/glucose/<int:glucose_id>/')
@login_required
@requires_access(['admin'])
def glucose(glucose_id=None):
    if glucose_id:
        record_ = HealthGlucoseRecord.query.filter_by(id=glucose_id).first()
        return render_template('healthdb/glucose_record.html', record=record_)
    page = request.args.get('page', 1, type=int)
    record_ids = [x.record_id for x in HealthGlucoseRecord.query.all()]
    count = len(record_ids)
    records_ = (HealthRecord.query
                .filter(HealthRecord.id.in_(record_ids))
                .order_by(HealthRecord.record_date.desc())
                .paginate(page=page, per_page=10))
    return render_template('healthdb/glucose_records.html', paginator=records_, count=count)


@bp.route('/cardio/')
@bp.route('/cardio/<int:cardio_id>/')
@login_required
@requires_access(['admin'])
def cardio(cardio_id=None):
    if cardio_id:
        record_ = HealthCardioRecord.query.filter_by(id=cardio_id).first()
        return render_template('healthdb/cardio_record.html', record=record_)
    page = request.args.get('page', 1, type=int)
    record_ids = [x.record_id for x in HealthCardioRecord.query.all()]
    count = len(record_ids)
    records_ = (HealthRecord.query
                .filter(HealthRecord.id.in_(record_ids))
                .order_by(HealthRecord.record_date.desc())
                .paginate(page=page, per_page=10))
    return render_template('healthdb/cardio_records.html', paginator=records_, count=count)


@bp.route('/pain/')
@bp.route('/pain/<int:pain_id>/')
@login_required
@requires_access(['admin'])
def pain(pain_id=None):
    if pain_id:
        record_ = HealthPainRecord.query.filter_by(id=pain_id).first()
        return render_template('healthdb/pain_record.html', record=record_)
    page = request.args.get('page', 1, type=int)
    record_ids = [x.record_id for x in HealthPainRecord.query.all()]
    count = len(record_ids)
    records_ = (HealthRecord.query
                .filter(HealthRecord.id.in_(record_ids))
                .order_by(HealthRecord.record_date.desc())
                .paginate(page=page, per_page=10))
    return render_template('healthdb/pain_records.html', paginator=records_, count=count)


@bp.route('/weight/')
@bp.route('/weight/<int:weight_id>/')
@login_required
@requires_access(['admin'])
def weight(weight_id=None):
    if weight_id:
        record_ = HealthWeightRecord.query.filter_by(id=weight_id).first()
        return render_template('healthdb/weight_record.html', record=record_)
    page = request.args.get('page', 1, type=int)
    record_ids = [x.record_id for x in HealthWeightRecord.query.all()]
    count = len(record_ids)
    records_ = (HealthRecord.query
                .filter(HealthRecord.id.in_(record_ids))
                .order_by(HealthRecord.record_date.desc())
                .paginate(page=page, per_page=10))
    return render_template('healthdb/weight_records.html', paginator=records_, count=count)


@bp.route('/notes/')
@login_required
@requires_access(['admin'])
def notes():
    page = request.args.get('page', 1, type=int)
    query = HealthNote.query.order_by(HealthNote.date_added.desc())
    count = query.count()
    notes_ = query.paginate(page=page, per_page=10)
    return render_template('healthdb/notes.html', paginator=notes_, count=count)


@bp.route('/note/<int:note_id>/')
@login_required
@requires_access(['admin'])
def note(note_id):
    query = HealthNote.query.filter_by(id=note_id).first()
    return render_template('healthdb/note.html', note=query)


@bp.route('/attachments/')
@login_required
@requires_access(['admin'])
def attachments():
    page = request.args.get('page', 1, type=int)
    query = HealthAttachment.query.order_by(HealthAttachment.record.record_date.desc()).paginate(page=page, per_page=10)
    return render_template('healthdb/attachments.html', pagination=query)


@bp.route('/download_attachment/<int:attachment_id>/')
@login_required
@requires_access(['admin'])
def download_attachment(attachment_id):
    use_browser = bool(request.args.get('browser'))
    attachment_ = HealthAttachment.query.filter_by(id=attachment_id).first()
    uuid_file = join(current_app.config['HEALTH_ATTACHMENTS_DIR'], attachment_.uuid)
    return send_file(uuid_file, download_name=attachment_.filename, as_attachment=not use_browser)


@bp.route('/create_record/', methods=['GET', 'POST'])
@bp.route('/create_record/<int:parent_id>', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def create_record(parent_id=None):
    form = RecordForm()

    if form.validate_on_submit():

        # Create health record object and add to database
        record_ = HealthRecord()
        record_.record = form.record.data
        record_.record_date = form.record_date.data
        record_.date_added = datetime.utcnow()
        record_.is_tracked = form.is_tracked.data
        record_.parent_id = form.parent_id.data if form.parent_id.data else None
        record_.descriptors = convert_options_to_tagmodels(form.descriptors.data, HealthDescriptorTag)
        record_.emotions = convert_options_to_tagmodels(form.emotions.data, HealthEmotionTag)
        record_.attachments = get_attachments(paths=form.attachments.data,
                                              dirkey='HEALTH_ATTACHMENTS_DIR',
                                              model=HealthAttachment
                                              )
        recordtext = ''
        if form.glucose_measure.data:
            subrecord = HealthGlucoseRecord()
            subrecord.measure = form.glucose_measure.data
            subrecord.units = form.glucose_units.data
            record_.glucose_record = [subrecord]
            if not record_.record:
                recordtext += 'Added a glucose record.'
        if form.systolic.data or form.diastolic.data or form.heart_rate.data:
            subrecord = HealthCardioRecord()
            subrecord.systolic = form.systolic.data
            subrecord.diastolic = form.diastolic.data
            subrecord.heart_rate = form.heart_rate.data
            record_.cardio_record = [subrecord]
            if not record_.record:
                if recordtext:
                    recordtext += '\n'
                recordtext += 'Added a cardio record'
        if form.pain_level.data and form.pain_description.data:
            subrecord = HealthPainRecord()
            subrecord.level = form.pain_level.data
            subrecord.description = form.pain_description.data
            record_.pain_record = [subrecord]
            if not record_.record:
                if recordtext:
                    recordtext += '\n'
                recordtext += 'Added a pain record'
        if form.weight_measure.data:
            subrecord = HealthWeightRecord()
            subrecord.measure = form.weight_measure.data
            subrecord.units = form.weight_units.data
            record_.weight_record = [subrecord]
            if not record_.record:
                if recordtext:
                    recordtext += '\n'
                recordtext += 'Added a weight record'
        if not record_.record:
            if not recordtext:
                recordtext = 'Added an empty record.'
            record_.record = recordtext

        db.session.add(record_)
        db.session.commit()

        if form.add_note.data:
            return redirect(url_for('healthdb.create_note', record_id=record_.id))
        else:
            return redirect(url_for('healthdb.record', record_id=record_.id))

    # Load tags and parent id, if applicable
    active_descriptors = []
    active_emotions = []
    if parent_id:
        form.parent_id.data = parent_id
        parent_query = HealthRecord.query.filter_by(id=parent_id).first()
        active_descriptors = parent_query.descriptors
        active_emotions = parent_query.emotions

    form.descriptors.data = active_descriptors
    form.descriptors.choices = convert_tagmodels_to_options(HealthDescriptorTag,
                                                            message='This record is about...'
                                                            )
    form.emotions.data = active_emotions
    form.emotions.choices = convert_tagmodels_to_options(HealthEmotionTag,
                                                         message='This record made me feel...')

    return render_template('healthdb/create_record.html',
                           form=form,
                           )


@bp.route('/create_subrecord/<string:sr_type>/', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def create_subrecord(sr_type):
    form = RecordForm()
    if sr_type == 'glucose' and form.glucose_measure.data or \
            sr_type == 'cardio' and (form.systolic.data or form.diastolic.data or form.heart_rate.data) or \
            sr_type == 'pain' and (form.pain_level.data or form.pain_description.data) or \
            sr_type == 'weight' and form.weight_measure.data:
        if form.validate_on_submit():
            record_ = HealthRecord()
            record_.record = f'Added a {sr_type} record.'
            record_.record_date = form.record_date.data
            record_.date_added = datetime.utcnow()
            record_.date_added = datetime.utcnow()
            if sr_type == 'glucose':
                subrecord = HealthGlucoseRecord()
                subrecord.measure = form.glucose_measure.data
                subrecord.units = form.weight_units.data
                record_.glucose_record = [subrecord]
            if sr_type == 'cardio':
                subrecord = HealthCardioRecord()
                subrecord.systolic = form.systolic.data
                subrecord.diastolic = form.diastolic.data
                subrecord.heart_rate = form.heart_rate.data
                record_.cardio_record = [subrecord]
            if sr_type == 'pain':
                subrecord = HealthPainRecord()
                subrecord.level = form.pain_level.data
                subrecord.description = form.pain_description.data
                record_.pain_record = [subrecord]
            if sr_type == 'weight':
                subrecord = HealthWeightRecord()
                subrecord.measure = form.weight_measure.data
                subrecord.units = form.weight_units.data
                record_.weight_record = [subrecord]

            record_.descriptors = convert_options_to_tagmodels(form.descriptors.data, HealthDescriptorTag)
            record_.emotions = convert_options_to_tagmodels(form.emotions.data, HealthEmotionTag)

            db.session.add(record_)
            db.session.commit()

            if form.add_note.data:
                return redirect(url_for('healthdb.create_note', record_id=record_.id))

            return redirect(url_for('healthdb.record', record_id=record_.id))

    form.descriptors.data = ['quick record']
    form.descriptors.choices = convert_tagmodels_to_options(HealthDescriptorTag,
                                                            message='This record is about...'
                                                            )
    form.emotions.data = []
    form.emotions.choices = convert_tagmodels_to_options(HealthEmotionTag,
                                                         message='This record made me feel...'
                                                         )
    return render_template('healthdb/create_subrecord.html',
                           form=form,
                           recordtype=sr_type
                           )


@bp.route('/update_record/<int:record_id>/', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def update_record(record_id):
    form = RecordForm()
    record_ = HealthRecord.query.filter_by(id=record_id).first()

    if form.validate_on_submit():

        # Create health record object and add to database
        record_.record = form.record.data
        record_.record_date = form.record_date.data
        record_.date_added = datetime.utcnow()
        record_.is_tracked = form.is_tracked.data
        record_.parent_id = form.parent_id.data if form.parent_id.data else None
        record_.descriptors = convert_options_to_tagmodels(form.descriptors.data, HealthDescriptorTag)
        record_.emotions = convert_options_to_tagmodels(form.emotions.data, HealthEmotionTag)
        record_.attachments += get_attachments(paths=form.attachments.data,
                                               dirkey='HEALTH_ATTACHMENTS_DIR',
                                               model=HealthAttachment
                                               )

        recordtext = ''
        # Glucose records
        form_has_data = form.glucose_measure.data is not None
        db_has_data = True if record_.glucose_record else False
        if not form_has_data and db_has_data:
            subrecord = record_.glucose_record[0]
            record_.glucose_record = []
            db.session.delete(subrecord)
        elif form_has_data or db_has_data:
            if form_has_data and db_has_data:
                subrecord = record_.glucose_record[0]
            elif not db_has_data:
                subrecord = HealthGlucoseRecord()
            subrecord.measure = form.glucose_measure.data
            subrecord.units = form.glucose_units.data
            record_.glucose_record = [subrecord]
            if not record_.record:
                recordtext += 'Added a glucose record.'

        # Cardio records
        form_has_data = form.systolic.data or form.diastolic.data or form.heart_rate.data
        db_has_data = True if record_.cardio_record else False
        if not form_has_data and db_has_data:
            subrecord = record_.cardio_record[0]
            record_.cardio_record = []
            db.session.delete(subrecord)
        elif form_has_data or db_has_data:
            if form_has_data and db_has_data:
                subrecord = record_.cardio_record[0]
            elif not db_has_data:
                subrecord = HealthCardioRecord()
            subrecord.systolic = form.systolic.data
            subrecord.diastolic = form.diastolic.data
            subrecord.heart_rate = form.heart_rate.data
            record_.cardio_record = [subrecord]
            if not record_.record:
                if recordtext:
                    recordtext += '\n'
                recordtext += 'Added a cardio record.'

        # Pain records
        form_has_data = form.pain_level.data or form.pain_description.data
        db_has_data = True if record_.pain_record else False
        if not form_has_data and db_has_data:
            subrecord = record_.pain_record[0]
            record_.pain_record = []
            db.session.delete(subrecord)
        elif form_has_data or db_has_data:
            if form_has_data and db_has_data:
                subrecord = record_.pain_record[0]
            elif not db_has_data:
                subrecord = HealthPainRecord()
            subrecord.level = form.pain_level.data
            subrecord.description = form.pain_description.data
            record_.pain_record = [subrecord]
            if not record_.record:
                if recordtext:
                    recordtext += '\n'
                recordtext += 'Added a pain record.'

        # Weight records
        form_has_data = form.weight_measure.data is not None
        db_has_data = True if record_.weight_record else False
        if not form_has_data and db_has_data:
            subrecord = record_.weight_record[0]
            record_.weight_record = []
            db.session.delete(subrecord)
        elif form_has_data or db_has_data:
            if form_has_data and db_has_data:
                subrecord = record_.weight_record[0]
            elif not db_has_data:
                subrecord = HealthWeightRecord()
            subrecord.measure = form.weight_measure.data
            subrecord.units = form.weight_units.data
            record_.weight_record = [subrecord]
            if not record_.record:
                if recordtext:
                    recordtext += '\n'
                recordtext += 'Added a weight record.'
        if not record_.record:
            if not recordtext:
                recordtext = 'Added an empty record.'
            record_.record = recordtext

        db.session.add(record_)
        db.session.commit()

        if form.add_note.data:
            return redirect(url_for('healthdb.create_note', record_id=record_.id))
        else:
            return redirect(url_for('healthdb.record', record_id=record_.id))

    open_panels = []
    form.record.data = record_.record
    form.record_date.data = record_.record_date
    if record_.parent_id:
        form.parent_id.data = record_.parent_id
    form.is_tracked.data = record_.is_tracked
    if record_.glucose_record:
        form.glucose_measure.data = record_.glucose_record[0].measure
        form.glucose_units.data = record_.glucose_record[0].units
        open_panels.append('glucose')
    if record_.cardio_record:
        form.systolic.data = record_.cardio_record[0].systolic
        form.diastolic.data = record_.cardio_record[0].diastolic
        form.heart_rate.data = record_.cardio_record[0].heart_rate
        open_panels.append('cardio')
    if record_.pain_record:
        form.pain_level.data = record_.pain_record[0].level
        form.pain_description.data = record_.pain_record[0].description
        open_panels.append('pain')
    if record_.weight_record:
        form.weight_measure.data = record_.weight_record[0].measure
        form.weight_units.data = record_.weight_record[0].units
        open_panels.append('weight')

    form.descriptors.data = [x.tag for x in record_.descriptors]
    form.descriptors.choices = convert_tagmodels_to_options(
        HealthDescriptorTag,
        message='This record is about...'
    )
    form.emotions.data = [x.tag for x in record_.emotions]
    form.emotions.choices = convert_tagmodels_to_options(
        HealthEmotionTag,
        message='This record made me feel...'
    )
    return render_template('healthdb/update_record.html',
                           form=form,
                           record=record_,
                           open_panels=open_panels
                           )


@bp.post('delete_record/<int:record_id>/')
def delete_record(record_id):
    record_ = HealthRecord.query.filter_by(id=record_id).first()
    db.session.delete(record_)
    db.session.commit()
    return redirect(url_for('healthdb.records'))


@bp.route('/create_note/', methods=['GET', 'POST'])
@bp.route('/create_note/<int:record_id>', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def create_note(record_id=None):
    form = NoteForm()
    if form.validate_on_submit():
        note_ = HealthNote()
        note_.record_id = record_id
        note_.note = form.note.data
        note_.important = form.important.data
        note_.date_added = note_.last_edited = datetime.utcnow()

        db.session.add(note_)
        db.session.commit()
        return redirect(url_for('healthdb.note', note_id=note_.id))
    record_ = HealthRecord.query.filter_by(id=record_id).first()
    return render_template('healthdb/create_note.html', form=form, record=record_)


@bp.route('/update_note/<int:note_id>/', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def update_note(note_id):
    form = NoteForm()
    note_ = HealthNote.query.filter_by(id=note_id).first()
    if form.validate_on_submit():
        note_.note = form.note.data
        note_.important = form.important.data
        note_.last_edited = datetime.utcnow()
        return redirect(url_for('healthdb.note', note_id=note_.id))

    form.note.data = note_.note
    form.important.data = note_.important
    return render_template('healthdb/update_note.html', form=form, note=note_)


@bp.post('delete_note/<int:note_id>/')
def delete_note(note_id):
    note_ = HealthNote.query.filter_by(id=note_id).first()
    record_ = note_.record
    db.session.delete(note_)
    db.session.commit()
    if record_:
        return redirect(url_for('healthdb.record', record_id=record_.id))
    return redirect(url_for('healthdb.notes'))


@bp.post('/delete_attachment/<int:attachment_id>/')
@login_required
@requires_access(['admin'])
def delete_attachment(attachment_id):
    attachment_ = HealthAttachment.query.filter_by(id=attachment_id).first()
    record_ = attachment_.record
    db.session.delete(attachment_)
    db.session.commit()
    return redirect(url_for('healthdb.record', record_id=record_.id))
