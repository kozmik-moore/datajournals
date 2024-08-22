import random
from datetime import datetime

from flask import render_template, request, url_for, redirect, flash, session
from flask_login import login_required
from sqlalchemy import or_

from datajournals import db
from datajournals.authorization import requires_access
from datajournals.base_methods import convert_tagmodels_to_options, convert_options_to_tagmodels
from datajournals.dreamdb import bp
from datajournals.dreamdb.forms import DreamCreateForm, DreamNoteForm, TagForm, RecordSearchForm, NoteSearchForm, \
    TagSearchForm
from datajournals.dreamdb.helper import get_dreams_stats, get_notes_stats, get_tags_stats, get_tag_stats
from datajournals.models.dreamdb import DreamRecord, DreamSubjectTag, DreamDescriptorTag, DreamEmotionTag, DreamNote


def _init_session_filters():
    """
    Checks if session filters exist. Creates them if needed.
    :return: None
    """
    sm = False  # 'session modified' flag
    if 'dream' not in session.keys():
        session['dream'] = {
            'filters': {
                'records': {},
                'notes': {},
                'tags': {},
            }
        }
        sm = True
    elif 'filters' not in session['dream'].keys():
        session['dream']['filters'] = {
            'records': {},
            'notes': {},
            'tags': {},
        }
        sm = True
    f: dict = session['dream']['filters']
    if 'records' not in f.keys() or not f['records']:
        f['records'] = {
            'timeofday': '',
            'sleeptype': '',
            'content': '',
            'subjects': [],
            'descriptors': [],
            'emotions': [],
        }
        sm = True
    if 'notes' not in f.keys() or not f['notes']:
        f['notes'] = {
            'content': '',
            'important': '',
            'record': 0,
            'hasrecord': ''
        }
        sm = True
    if 'tags' not in f.keys() or not f['tags']:
        f['tags'] = {
            'content': '',
        }
        sm = True
    if sm:
        session['modified'] = True


@bp.route('/dashboard')
@bp.route('/index')
@bp.route('/')
@login_required
@requires_access(['admin'])
def index():
    rr = None
    c = db.session.query(DreamRecord).count()
    if c:
        d = datetime.today()
        sv = d.day * d.month
        random.seed(sv)
        offset = random.randint(0, c - 1)
        rr = db.session.query(DreamRecord).offset(offset).limit(1).all()[0]
    ds = get_dreams_stats()
    ns = get_notes_stats()
    ts = get_tags_stats()
    return render_template('dreamdb/index.html',
                           record=rr,
                           dreamstats=ds,
                           notestats=ns,
                           tagstats=ts
                           )


@bp.route('/records', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def records():
    sm = False  # 'session modified' flag
    rf = RecordSearchForm()
    tmm = {
        'subjects': DreamSubjectTag,
        'descriptors': DreamDescriptorTag,
        'emotions': DreamEmotionTag,
    }
    page = request.args.get('page', 1, type=int)

    # Instantiate session filters
    try:
        f = session['dream']['filters']['records']
    except KeyError:
        _init_session_filters()
        f = session['dream']['filters']['records']

    # Update session filters by URL parameters
    # Filter by single tag
    for i in tmm.keys():
        ti = request.args.get(i[:-1], '', str)
        if ti:
            tm = tmm[i]
            tq = db.session.query(tm).filter_by(tag=ti).first()
            if tq:
                f[i] = [ti]
                session['modified'] = True
                getattr(rf, i).data = f[i]
                return redirect(url_for('dreamdb.records'))
            break

    # Filter by sleep type
    s = request.args.get('sleeptype', '', str)
    if s:
        f['sleeptype'] = s
        rf.sleep_type.data = s
        session['modified'] = True
        return redirect(url_for('dreamdb.records'))

    # Filter by time of day
    t = request.args.get('timeofday', '', str)
    if t:
        f['timeofday'] = t
        rf.time_of_day.data = t
        session['modified'] = True
        return redirect(url_for('dreamdb.records'))

    # Filter by content
    c = request.args.get('content', '', str)
    if c:
        f['content'] = c
        rf.content.data = c
        session['modified'] = True
        return redirect(url_for('dreamdb.records'))

    # Instantiate form fields and filter by form fields values OR update form to match session filters
    for i, m in tmm.items():
        getattr(rf, i).choices = convert_tagmodels_to_options(m)

    if rf.validate_on_submit():
        f['content'] = rf.content.data
        f['timeofday'] = rf.time_of_day.data
        f['sleeptype'] = rf.sleep_type.data
        for i, m in tmm.items():
            f[i] = getattr(rf, i).data
        session['modified'] = True
        return redirect(url_for('dreamdb.records'))
    else:
        rf.content.data = f['content']
        rf.sleep_type.data = f['sleeptype']
        rf.time_of_day.data = f['timeofday']
        for i, m in tmm.items():
            getattr(rf, i).data = f[i]

    # Remove filters from session, as applicable
    r = request.args.get('remove', '', str)
    if r == 'all':
        for i in 'content', 'sleeptype', 'timeofday':
            f[i] = ''
        for i in 'subjects', 'descriptors', 'emotions':
            f[i] = []
        session['modified'] = True
        return redirect(url_for('dreamdb.records'))
    if r and r in [x[:-1] for x in tmm.keys()]:
        r = r + 's'
        t = request.args.get('tag', '', str)
        tq = db.session.query(tmm[r]).filter_by(tag=t).first()
        if tq:
            try:
                f[r].remove(t)
                setattr(getattr(rf, r), 'data', f[r])
                session['modified'] = True
                return redirect(url_for('dreamdb.records'))
            except ValueError:
                pass
    elif r:
        f[r] = ''
        setattr(
            getattr(rf, {'content': 'content', 'sleeptype': 'sleep_type', 'timeofday': 'time_of_day'}[r]),
            'data',
            ''
        )
        session['modified'] = True
        return redirect(url_for('dreamdb.records'))

    for i in 'subjects', 'descriptors', 'emotions':
        attr = getattr(rf, i)
        if attr.data is None:
            attr.data = []

    q = db.session.query(DreamRecord).distinct()
    a = []
    for i in tmm.keys():
        q = q.outerjoin(getattr(DreamRecord, i))
        if f[i]:
            a.append(tmm[i].tag.in_(f[i]))
    q = q.filter(or_(*a))
    if f['content']:
        q = q.filter(DreamRecord.record.like(f'%{f["content"]}%'))
    if f['sleeptype']:
        q = q.filter(DreamRecord.sleep_type == f['sleeptype'])
    if f['timeofday']:
        q = q.filter(DreamRecord.time_of_day == f['timeofday'])
    q = q.order_by(DreamRecord.record_date.desc())
    p = q.paginate(page=page, per_page=10)
    if sm:
        session['modified'] = True
    opt = dict(paginator=p, form=rf, **f)
    return render_template('dreamdb/records.html', **opt)


@bp.route('/records/<int:record_id>')
@login_required
@requires_access(['admin'])
def record(record_id):
    rq = DreamRecord.query.get_or_404(record_id)
    return render_template('dreamdb/record.html', record=rq)


@bp.route('/subjects', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def subjects():
    page = request.args.get('page', 1, type=int)
    return tags('subjects', page)


@bp.route('/subjects/<int:subject_id>')
@login_required
@requires_access(['admin'])
def subject(subject_id):
    return tag('subjects', subject_id)


@bp.route('/descriptors', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def descriptors():
    page = request.args.get('page', 1, type=int)
    return tags('descriptors', page)


@bp.route('/descriptors/<int:descriptor_id>')
@login_required
@requires_access(['admin'])
def descriptor(descriptor_id):
    return tag('descriptors', descriptor_id)


@bp.route('/emotions', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def emotions():
    page = request.args.get('page', 1, type=int)
    return tags('emotions', page)


@bp.route('/emotions/<int:emotion_id>')
@login_required
@requires_access(['admin'])
def emotion(emotion_id):
    return tag('emotions', emotion_id)


def tags(tagtype: str, page: int = 1):
    sm = False
    tf = TagSearchForm()
    td = {
        'subjects': DreamSubjectTag,
        'descriptors': DreamDescriptorTag,
        'emotions': DreamEmotionTag
    }
    try:
        f = session['dream']['filters']['tags']
    except KeyError:
        _init_session_filters()
        f = session['dream']['filters']['tags']

    # Update session filters by URL parameters
    # Filter by content
    c = request.args.get('content', '', str)
    if c:
        f['content'] = c
        tf.content.data = c
        session['modified'] = True
        return redirect(url_for(f'dreamdb.{tagtype}', page=1))

    # Instantiate form fields and filter by form fields values OR update form to match session filters
    if tf.validate_on_submit():
        f['content'] = tf.content.data
        session['modified'] = True
        return redirect(url_for(f'dreamdb.{tagtype}'))
    else:
        tf.content.data = f['content']

    # Remove filters from session, as applicable
    r = request.args.get('remove', False, bool)
    if r:
        f['content'] = ''
        session['modified'] = True
        return redirect(url_for(f'dreamdb.{tagtype}'))

    q = db.session.query(td[tagtype])
    if f['content']:
        q = q.filter(td[tagtype].tag.like(f'%{f["content"]}%'))
    p = q.order_by(td[tagtype].tag).paginate(page=page, per_page=10)
    if sm:
        session['modified'] = True
    opt = dict(paginator=p, tagtype=tagtype, form=tf, **f)
    return render_template('dreamdb/tags.html', **opt)


def tag(tagtype: str, tag_id: int):
    td = {
        'subjects': DreamSubjectTag,
        'descriptors': DreamDescriptorTag,
        'emotions': DreamEmotionTag
    }
    t = db.session.query(td[tagtype]).filter_by(id=int(tag_id)).first()
    ts = get_tag_stats(t)
    return render_template('dreamdb/tag.html', tagtype=tagtype, tag=t, tagstats=ts)


@bp.route('/notes', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def notes():
    sm = False  # 'session modified' flag
    nf = NoteSearchForm()
    pg = request.args.get('page', 1, type=int)

    # Instantiate session filters
    try:
        f = session['dream']['filters']['notes']
    except KeyError:
        _init_session_filters()
        f = session['dream']['filters']['notes']

    # Update session filters by URL parameters
    # Filter by record id
    r = request.args.get('record', 0, int)
    if r:
        f['record'] = r
        session['modified'] = True
        return redirect(url_for('dreamdb.notes'))

    # Filter by content
    c = request.args.get('content', '', str)
    if c:
        f['content'] = c
        session['modified'] = True
        return redirect(url_for('dreamdb.notes'))

    # Filter by 'has record'
    i = request.args.get('hasrecord', '', str)
    if i:
        f['hasrecord'] = i
        session['modified'] = True
        return redirect(url_for('dreamdb.notes'))

    # Filter by 'marked important'
    i = request.args.get('important', '', str)
    if i:
        f['important'] = i
        session['modified'] = True
        return redirect(url_for('dreamdb.notes'))

    # Instantiate form fields and filter by form fields values OR update form to match session filters
    if nf.validate_on_submit():
        f['content'] = nf.content.data
        f['important'] = nf.important.data
        f['hasrecord'] = nf.hasrecord.data
        session['modified'] = True
        return redirect(url_for('dreamdb.notes'))
    else:
        nf.content.data = f['content']
        nf.important.data = f['important']
        nf.hasrecord.data = f['hasrecord']

    # Remove filters from session, as applicable
    r = request.args.get('remove', '', str)
    nfd = {'record': 0, 'content': '', 'important': '', 'hasrecord': ''}
    if r == 'all':
        for i, v in nfd.items():
            f[i] = v
        session['modified'] = True
        return redirect(url_for('dreamdb.notes'))
    if r:
        for i, v in nfd.items():
            if i == r:
                f[r] = v
                session['modified'] = True
                return redirect(url_for('dreamdb.notes'))

    rq = None
    q = db.session.query(DreamNote)
    if f['record']:
        q = q.filter(DreamNote.record_id == f['record'])
        rq = db.session.query(DreamRecord).filter_by(id=f['record']).first()
    if f['content']:
        q = q.filter(DreamNote.note.like(f'%{f["content"]}%'))
    if f['important']:
        q = q.filter(DreamNote.important == {
            'yes': True,
            'no': False
        }[f['important']])
    if f['hasrecord']:
        if f['hasrecord'] == 'yes':
            q = q.filter(DreamNote.record_id.isnot(None))
        else:
            q = q.filter(DreamNote.record_id.is_(None))
    q = q.order_by(DreamNote.date_added.desc())
    p = q.paginate(page=pg, per_page=10)
    if sm:
        session['modified'] = True
    opt = dict(paginator=p, form=nf, dreamrecord=rq, **f)
    return render_template('dreamdb/notes.html', **opt)


@bp.route('/notes/<int:note_id>')
@login_required
@requires_access(['admin'])
def note(note_id):
    note_ = DreamNote.query.filter_by(id=note_id).first()
    return render_template('dreamdb/note.html', note=note_)


@bp.route('/records/create', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def create_record():
    f = DreamCreateForm()

    if f.validate_on_submit():

        # Create record object and add to database
        r = DreamRecord()
        for a in 'record', 'record_date', 'time_of_day', 'sleep_type':
            setattr(r, a, f.data[a] if f.data[a] else None)
        for a, m in ('subjects', DreamSubjectTag), ('descriptors', DreamDescriptorTag), ('emotions', DreamEmotionTag):
            setattr(r, a, convert_options_to_tagmodels(f.data[a], m))

        db.session.add(r)
        db.session.commit()

        if f.add_note.data:
            return redirect(url_for('dreamdb.create_note', record_id=r.id))
        return redirect(url_for('dreamdb.record', record_id=r.id))

    for a, m in ('subjects', DreamSubjectTag), ('descriptors', DreamDescriptorTag), ('emotions', DreamEmotionTag):
        attr = getattr(f, a)
        setattr(attr, 'choices', convert_tagmodels_to_options(m))
        setattr(attr, 'data', [])
    return render_template('dreamdb/recordform.html', form=f)


@bp.route('/notes/create', methods=('GET', 'POST'))
@bp.route('/notes/create/<int:record_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def create_note(record_id=None):
    f = DreamNoteForm()
    r = DreamRecord.query.filter_by(id=record_id).first() if record_id else None
    if f.validate_on_submit():
        n = DreamNote()
        n.record = r
        for a in 'note', 'important':
            setattr(n, a, f.data[a])
        d = datetime.utcnow()
        for a in 'date_added', 'last_edited':
            setattr(n, a, d)
        db.session.add(n)
        db.session.commit()
        return redirect(url_for('dreamdb.note', note_id=n.id))
    return render_template('dreamdb/update_note.html', form=f, record=r)


@bp.route('/records/update/<int:record_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def update_record(record_id):
    record_ = DreamRecord.query.filter_by(id=record_id).first()
    form = DreamCreateForm()
    msg = {
        'subjects': 'This dream was about...',
        'descriptors': 'Words to describe this dream include...',
        'emotions': 'This dream made me feel...',
    }
    form.subjects.choices = convert_tagmodels_to_options(DreamSubjectTag, message=msg['subjects'])
    form.emotions.choices = convert_tagmodels_to_options(DreamEmotionTag, message=msg['emotions'])
    form.descriptors.choices = convert_tagmodels_to_options(DreamDescriptorTag, message=msg['descriptors'])

    if form.validate_on_submit():

        # Update record object
        record_.record = form.record.data
        record.record_date = form.record_date.data
        record_.time_of_day = form.time_of_day.data
        record_.sleep_type = form.sleep_type.data
        record_.subjects = convert_options_to_tagmodels(form.subjects.data, DreamSubjectTag)
        record_.descriptors = convert_options_to_tagmodels(form.descriptors.data, DreamDescriptorTag)
        record_.emotions = convert_options_to_tagmodels(form.emotions.data, DreamEmotionTag)

        db.session.add(record_)
        db.session.commit()

        if form.add_note.data:
            return redirect(url_for('dreamdb.create_note', record_id=record_.id))
        return redirect(url_for('dreamdb.record', record_id=record_.id))

    # Fill in form values
    form.subjects.data = [x.tag for x in record_.subjects] or []
    form.descriptors.data = [x.tag for x in record_.descriptors] or []
    form.emotions.data = [x.tag for x in record_.emotions] or []
    form.record.data = record_.record
    form.record_date.data = record_.record_date
    form.time_of_day.data = record_.time_of_day
    form.sleep_type.data = record_.sleep_type
    return render_template('dreamdb/recordform.html',
                           form=form,
                           record=record_,
                           )


@bp.route('/notes/update/<int:note_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def update_note(note_id):
    note_ = DreamNote.query.filter_by(id=note_id).first()
    form = DreamNoteForm()
    if form.validate_on_submit():
        note_.note = form.note.data
        note_.important = form.important.data
        note_.last_edited = datetime.utcnow()
        db.session.add(note_)
        db.session.commit()
        return redirect(url_for('dreamdb.note', note_id=note_id))
    form.note.data = note_.note
    form.important.data = note_.important
    return render_template('dreamdb/update_note.html', form=form, note=note_)


@bp.route('/<string:tagtype>/edit/<int:tag_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def update_tag(tagtype: str, tag_id: int):
    td = {
        'subjects': DreamSubjectTag,
        'descriptors': DreamDescriptorTag,
        'emotions': DreamEmotionTag
    }
    tq = db.session.query(td[tagtype])
    t: DreamSubjectTag | DreamDescriptorTag | DreamEmotionTag = tq.filter_by(id=tag_id).first()
    f = TagForm()
    f.tag.label = tagtype[:-1].capitalize()
    if f.validate_on_submit():
        tn = [x.tag for x in tq.all()]
        if f.tag.data not in tn or f.tag.data == t.tag:
            if f.tag.data not in tn:
                t.tag = f.tag.data
                db.session.add(t)
                db.session.commit()
            return tag(tagtype=tagtype, tag_id=tag_id)
        else:
            flash(f'"{f.tag.data}" already exists.', 'warning')
    f.tag.data = t.tag
    return render_template('dreamdb/update_tag.html', form=f, tagtype=tagtype, tag=t)


@bp.route('/delete_record/<int:record_id>', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def delete_record(record_id):
    record_ = DreamRecord.query.filter_by(id=record_id).first()
    db.session.delete(record_)
    db.session.commit()
    return redirect(url_for('dreamdb.records'))


@bp.route('/delete_note/<int:note_id>', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def delete_note(note_id):
    note_ = DreamNote.query.filter_by(id=note_id).first()
    record_ = note_.record
    db.session.delete(note_)
    db.session.commit()
    if record_:
        return redirect(url_for('dreamdb.record', record_id=record_.id))
    return redirect(url_for('dreamdb.notes'))


@bp.route('/<string:tagtype>/<int:tag_id>/delete', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def delete_tag(tagtype: str, tag_id: int):
    td = {
        'subjects': DreamSubjectTag,
        'descriptors': DreamDescriptorTag,
        'emotions': DreamEmotionTag
    }
    t = db.session.query(td[tagtype]).filter_by(id=tag_id).first()
    if not t.records:
        db.session.delete(t)
        db.session.commit()
        return tags(tagtype)
    else:
        return tag(tagtype, tag_id)
