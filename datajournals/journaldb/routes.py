import random
from datetime import datetime
from os.path import join

from flask import render_template, request, url_for, redirect, send_file, current_app, session, flash
from flask_login import login_required
from sqlalchemy import or_

from datajournals import db
from datajournals.authorization import requires_access
from datajournals.base_methods import convert_tagmodels_to_options, convert_options_to_tagmodels, get_attachments, \
    remove_attachment_file
from datajournals.journaldb import bp
from datajournals.journaldb.forms import CreateRecordForm, AttachmentsForm, SearchRecordForm, SearchTagForm, TagForm, \
    UpdateRecordForm
from datajournals.journaldb.helper import get_records_stats, get_unfinished_stats, get_watched_stats, get_tags_stats, \
    get_tag_stats
from datajournals.models.journaldb import JournalRecord, JournalSubjectTag, JournalDescriptorTag, JournalEmotionTag, \
    JournalAttachment


def _init_session_filters():
    if 'journaldb' not in session.keys():
        session['journaldb'] = {
            'filters': {
                'records': {},
                'tags': {}
            }
        }
    elif 'filters' not in session['journaldb'].keys():
        session['journaldb']['filters'] = {
            'records': {},
            'tags': {}
        }
    f = session['journaldb']['filters']
    if not f['records'] or 'records' not in f.keys():
        f['records'] = {
            'content': '',
            'linktype': '',
            'unfinished': '',
            'watched': '',
            'subjects': [],
            'descriptors': [],
            'emotions': [],
        }
    if not f['tags'] or 'tags' not in f.keys():
        f['tags'] = {
            'content': '',
        }


@bp.route('/index/')
@bp.route('/dashboard/')
@bp.route('/')
@login_required
@requires_access(['admin'])
def index():
    rr = None
    c = db.session.query(JournalRecord).count()
    if c:
        d = datetime.today()
        sv = d.month * d.day
        random.seed(sv)
        offset = random.randint(0, c - 1)
        rr = db.session.query(JournalRecord).offset(offset).limit(1).all()[0]
    rs = get_records_stats()
    us = get_unfinished_stats()
    ws = get_watched_stats()
    ts = get_tags_stats()
    return render_template('journaldb/index.html',
                           recordstats=rs,
                           unfinishedstats=us,
                           watchedstats=ws,
                           tagstats=ts,
                           randomrecord=rr
                           )


@bp.route('/records/', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def records():
    tmm = {
        'subjects': JournalSubjectTag,
        'descriptors': JournalDescriptorTag,
        'emotions': JournalEmotionTag
    }
    try:
        f = session['journaldb']['filters']['records']
    except KeyError:
        _init_session_filters()
        f = session['journaldb']['filters']['records']

    # Update session filters from URL parameters
    rr = False  # Redirect required

    # Update content filter
    c = request.args.get('content', '', str)
    if c:
        f['content'] = c
        rr = True

    # Update linktype filter
    lt = request.args.get('linktype', '', str)
    if lt and lt in ('parent', 'child', 'both', 'neither'):  # 'Has parent', 'has child', 'has both', 'has neither'
        f['linktype'] = lt
        rr = True

    # Update unfinished filter
    c = request.args.get('unfinished', '', str)
    if c:
        f['unfinished'] = c
        rr = True

    # Update watched filter
    c = request.args.get('watched', '', str)
    if c:
        f['watched'] = c
        rr = True

    # Update tags filter
    for i in tmm.keys():
        ti = request.args.get(i[:-1], '', str)
        if ti:
            f[i] = [ti]
            rr = True

    if rr:
        session['modified'] = True
        return redirect(url_for('journaldb.records'))

    # Instantiate form and update session filters from form field and/or update form fields from session filters
    rf = SearchRecordForm()
    for i, m in tmm.items():
        setattr(getattr(rf, i), 'choices', convert_tagmodels_to_options(m))
    if rf.validate_on_submit():
        for i in f.keys():
            f[i] = getattr(rf, i).data
            if f[i]:
                rr = True
        if rr:
            session['modified'] = True
            return redirect(url_for('journaldb.records'))
    else:
        for i in f.keys():
            setattr(getattr(rf, i), 'data', f[i])

    # Remove filters, as applicable
    r = request.args.to_dict(flat=False)
    if 'remove' in r.keys():
        # Remove all filters
        if 'all' in r['remove']:
            for i in 'content', 'linktype', 'unfinished', 'watched':
                f[i] = ''
            for i in tmm.keys():
                f[i] = []
            rr = True

        # Remove content, linktype filters
        else:
            for i in 'content', 'linktype', 'unfinished', 'watched':
                if i in r['remove']:
                    f[i] = ''
                    rr = True

    # Remove tags filters
    for i in tmm.keys():
        ri = 'remove' + i[:-1]
        if ri in r.keys():
            for ti in r[ri]:
                try:
                    f[i].remove(ti)
                    rr = True
                except ValueError:
                    pass
    if rr:
        session['modified'] = True
        return redirect(url_for('journaldb.records'))

    page = request.args.get('page', 1, type=int)
    q = db.session.query(JournalRecord).distinct()
    if f['content']:
        q = q.filter(JournalRecord.record.like(f'%{f["content"]}%'))
    if f['linktype']:
        lt = f['linktype']
        if lt == 'both':
            q = q.filter(JournalRecord.parent_id.is_not(None) & JournalRecord.children.any())
        elif lt == 'neither':
            q = q.filter(JournalRecord.parent_id.is_(None) & ~JournalRecord.children.any())
        elif lt == 'parent':
            q = q.filter(JournalRecord.parent_id.is_not(None) & ~JournalRecord.children.any())
        elif lt == 'child':
            q = q.filter(JournalRecord.parent_id.is_(None) & JournalRecord.children.any())
    if f['unfinished']:
        ut = {'yes': 1, 'no': 0}[f['unfinished']]
        q = q.filter(JournalRecord.unfinished == ut)
    if f['watched']:
        wt = {'yes': 1, 'no': 0}[f['watched']]
        q = q.filter(JournalRecord.watched == wt)
    a = []
    for i in tmm.keys():
        if f[i]:
            q = q.outerjoin(getattr(JournalRecord, i))
            a.append(tmm[i].tag.in_(f[i]))
    if a:
        q = q.filter(or_(*a))
    q = q.order_by(JournalRecord.record_date.desc())
    p = q.paginate(page=page, per_page=10)
    options = dict(paginator=p, form=rf, **f)
    return render_template('journaldb/records.html', **options)


@bp.route('/records/<int:record_id>/')
@login_required
@requires_access(['admin'])
def record(record_id):
    record_query = JournalRecord.query.get_or_404(record_id)
    return render_template('journaldb/record.html', record=record_query)


@bp.route('/<string:tagtype>/', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def tags(tagtype: str = None):
    tmm = {
        'subjects': JournalSubjectTag,
        'descriptors': JournalDescriptorTag,
        'emotions': JournalEmotionTag
    }
    tm = tmm[tagtype]
    try:
        f = session['journaldb']['filters']['tags']
    except KeyError:
        _init_session_filters()
        f = session['journaldb']['filters']['tags']

    #  Update session filters from URL parameters
    c = request.args.get('content', '', str)
    if c:
        f['content'] = c
        session['modified'] = True
        return redirect(url_for('.tags', tagtype=tagtype))

    # Instantiate filter form and update form fields and session filters
    tf = SearchTagForm()
    if tf.validate_on_submit():
        f['content'] = tf.content.data
        session['modified'] = True
        return redirect(url_for('.tags', tagtype=tagtype))
    else:
        tf.content.data = f['content']

    # Remove filters from session filters
    r = request.args.get('remove', '', str)
    if r == 'true':
        f['content'] = ''
        session['modified'] = True
        return redirect(url_for('.tags', tagtype=tagtype))

    pg = request.args.get('page', 1, int)
    q = db.session.query(tm)
    if f['content']:
        q = q.filter(tm.tag.like(f'%{f["content"]}%'))
    q = q.order_by(tm.tag.asc())
    p = q.paginate(page=pg, per_page=10)
    o = dict(paginator=p, form=tf, tagtype=tagtype, **f)
    return render_template('journaldb/tags.html', **o)


@bp.route('/<string:tagtype>/<int:tagid>/', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def tag(tagtype: str, tagid: int):
    tmm = {
        'subjects': JournalSubjectTag,
        'descriptors': JournalDescriptorTag,
        'emotions': JournalEmotionTag
    }
    q = db.session.query(tmm[tagtype]).filter_by(id=tagid).first()
    ts = get_tag_stats(q)
    return render_template('journaldb/tag.html', tagtype=tagtype, tag=q, tagstats=ts)


@bp.route('/attachments/')
@login_required
@requires_access(['admin'])
def attachments():
    page = request.args.get('page', 1, type=int)
    query = JournalAttachment.query.order_by(JournalAttachment.date_added.desc()).paginate(page=page, per_page=10)
    return render_template('journaldb/attachments.html', pagination=query)


@bp.route('/attachments/<int:attachment_id>/')
@login_required
@requires_access(['admin'])
def attachment(attachment_id):
    attachment_ = JournalAttachment.query.filter_by(id=attachment_id).first()
    return render_template('journaldb/attachment.html', attachment=attachment_)


@bp.route('/attachments/add/<int:record_id>', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def add_attachments(record_id):
    r = db.session.query(JournalRecord).filter_by(id=record_id).first()
    af = AttachmentsForm()
    if af.validate_on_submit():
        r.attachments += get_attachments(af.attachments.data,
                                         'JOURNAL_ATTACHMENTS_DIR',
                                         JournalAttachment)
        db.session.add(r)
        db.session.commit()
        return redirect(url_for('.record', record_id=record_id))
    af.record_id.data = r.id
    return render_template('journaldb/add_attachments.html', form=af, record=r)


@bp.route('/records/create/', methods=('GET', 'POST'))
@bp.route('/records/link/<int:parent_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def create_record(parent_id=None):
    tmm = {
        'subjects': JournalSubjectTag,
        'descriptors': JournalDescriptorTag,
        'emotions': JournalEmotionTag,
    }
    f = CreateRecordForm()
    for i, m in tmm.items():
        setattr(getattr(f, i), 'choices', convert_tagmodels_to_options(m))

    if f.validate_on_submit():
        # Create journal object and add to database
        r = JournalRecord()
        r.record = f.record.data
        r.record_date = f.record_date.data
        r.date_added = datetime.utcnow()
        r.parent_id = f.parent_id.data if f.parent_id.data else None
        r.unfinished = f.unfinished.data
        r.watched = f.watched.data
        for i, m in tmm.items():
            setattr(r, i, convert_options_to_tagmodels(getattr(f, i).data, m))

        r.attachments = get_attachments(f.attachments.data,
                                        'JOURNAL_ATTACHMENTS_DIR',
                                        JournalAttachment)

        db.session.add(r)
        db.session.commit()
        return redirect(url_for('journaldb.record', record_id=r.id))

    # Load tags and parent id, if applicable
    f.subjects.data = []
    f.descriptors.data = []
    f.emotions.data = []
    if parent_id:
        pq = JournalRecord.query.filter_by(id=parent_id).first()
        f.subjects.data = [x.tag for x in pq.subjects]
        f.descriptors.data = [x.tag for x in pq.descriptors]
        f.emotions.data = [x.tag for x in pq.emotions]
        f.watched.data = pq.watched
        f.parent_id.data = parent_id

    return render_template('journaldb/create_record.html', form=f)


@bp.route('/records/update/<int:record_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def update_record(record_id):
    tmm = {
        'subjects': JournalSubjectTag,
        'descriptors': JournalDescriptorTag,
        'emotions': JournalEmotionTag,
    }
    r = JournalRecord.query.filter_by(id=record_id).first()
    f = UpdateRecordForm()
    for i, m in tmm.items():
        setattr(getattr(f, i), 'choices', convert_tagmodels_to_options(m))

    if f.validate_on_submit():
        r.record = f.record.data
        r.record_date = f.record_date.data
        r.unfinished = f.unfinished.data
        r.watched = f.watched.data
        for i, m in tmm.items():
            setattr(r, i, convert_options_to_tagmodels(getattr(f, i).data, m))
        r.attachments += get_attachments(f.add_attachments.data,
                                         'JOURNAL_ATTACHMENTS_DIR',
                                         JournalAttachment
                                         )
        for d in f.attachments.data:
            aq = db.session.query(JournalAttachment).filter_by(id=int(d['attachment_id'])).first()
            if d['delete']:
                remove_attachment_file(aq.uuid, 'JOURNAL_ATTACHMENTS_DIR')
                db.session.delete(aq)
                db.session.commit()
            else:
                aq.filename = d['filename']
                db.session.add(aq)
                db.session.commit()

        db.session.add(r)
        db.session.commit()
        return redirect(url_for('journaldb.record', record_id=r.id))

    f.subjects.data = [x.tag for x in r.subjects]
    f.descriptors.data = [x.tag for x in r.descriptors]
    f.emotions.data = [x.tag for x in r.emotions]
    f.record.data = r.record
    f.record_date.data = r.record_date
    f.unfinished.data = r.unfinished
    f.watched.data = r.watched
    for a in r.attachments:
        sf = f.attachments.append_entry()
        sf.form.attachment_id.data = a.id
        sf.form.filename.data = a.filename
    return render_template('journaldb/create_record.html', form=f, record=r)


@bp.route('/<string:tagtype>/update/<int:tagid>', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def update_tag(tagtype: str, tagid: int):
    tmm = {
        'subjects': JournalSubjectTag,
        'descriptors': JournalDescriptorTag,
        'emotions': JournalEmotionTag
    }
    tm = tmm[tagtype]
    t = db.session.query(tm).filter_by(id=tagid).first()
    tf = TagForm()
    if tf.validate_on_submit():
        n = tf.tag.data
        tn = [x.tag for x in db.session.query(tm).all()]
        if n in tn:
            flash(f'"{n}" already exists', 'warning')
        else:
            t.tag = n
            db.session.add(t)
            db.session.commit()
            return redirect(url_for('.tag', tagtype=tagtype, tagid=tagid))
    if not tf.tag.data:
        tf.tag.data = t.tag
    return render_template('/journaldb/update_tag.html', form=tf, tag=t, tagtype=tagtype)


@bp.route('/records/delete/<int:record_id>')  # TODO needs testing
@login_required
@requires_access(['admin'])
def delete_record(record_id):
    r = JournalRecord.query.filter_by(id=record_id).first()
    db.session.delete(r)
    db.session.commit()
    return redirect(url_for('journaldb.records'))


@bp.route('/<string:tagtype>/delete/<int:tagid>')
@login_required
@requires_access(['admin'])
def delete_tag(tagtype: str, tagid: int):
    tmm = {
        'subjects': JournalSubjectTag,
        'descriptors': JournalDescriptorTag,
        'emotions': JournalEmotionTag
    }
    tm = tmm[tagtype]
    t = db.session.query(tm).filter_by(id=tagid).first()
    db.session.delete(t)
    db.session.commit()
    return redirect(url_for('.tags', tagtype=tagtype))


@bp.route('/attachments/delete/<int:attachment_id>')
@login_required
@requires_access(['admin'])
def delete_attachment(attachment_id):
    a = JournalAttachment.query.filter_by(id=attachment_id).first()
    r = a.record
    remove_attachment_file(a.uuid, 'JOURNAL_ATTACHMENTS_DIR')
    db.session.delete(a)
    db.session.commit()
    return redirect(url_for('journaldb.record', record_id=r.id))


@bp.route('/attachments/download/<int:attachment_id>')
@login_required
@requires_access(['admin'])
def download_attachment(attachment_id):
    b = request.args.get('browser', 'yes', str)
    if b in ('yes', 'no'):
        aa = {'yes': False, 'no': True}[b]
    else:
        aa = False
    a = JournalAttachment.query.filter_by(id=attachment_id).first()
    p = join(current_app.config['JOURNAL_ATTACHMENTS_DIR'], a.uuid)
    return send_file(p, download_name=a.filename, as_attachment=aa)
