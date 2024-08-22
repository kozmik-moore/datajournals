import io
from datetime import datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pandas as pd
import seaborn as sns
from flask import render_template, request, url_for, redirect, send_file, flash
from flask_login import login_required

from datajournals import db
from datajournals.authorization import requires_access
from datajournals.base_methods import convert_options_to_tagmodels, convert_tagmodels_to_options, get_duration_tuple
from datajournals.models.sleepdb import (SleepRecord, SleepLocationTag, SleepInterruptionTag, SleepEmotionTag,
                                         SleepNote, SleepSensationTag, SleepInterruptionAssociation)
from datajournals.sleepdb import bp
from datajournals.sleepdb.forms import SleepRecordForm, SleepNoteForm, SleepInterruptionForm, TagForm, RatingForm
from datajournals.sleepdb.helperfunctions import SleepDurationStats, to_hours, filter_duration_data, \
    get_duration_data, get_duration_stats, get_index_stats, timedelta_to_str, get_all_tags_stats, \
    get_tag_stats_v2


@bp.route('/dashboard')
@bp.route('/index')
@bp.route('/')
@login_required
@requires_access(['admin'])
def index():
    q = db.session.query(SleepRecord)
    lr = q.order_by(SleepRecord.time_retire.desc()).first()
    s = get_index_stats()
    return render_template('sleepdb/index.html', stats=s, latest=lr)


@bp.route('/records')
@login_required
@requires_access(['admin'])
def records():
    page = request.args.get('page', 1, type=int)
    query = SleepRecord.query.order_by(SleepRecord.time_retire.desc())
    count = query.count()
    paginator = query.paginate(page=page, per_page=10)
    return render_template('sleepdb/records.html', paginator=paginator, count=count)


@bp.route('/records/<int:record_id>')
@login_required
@requires_access(['admin'])
def record(record_id):
    npg = request.args.get('notespage', 1, type=int)
    rq = SleepRecord.query.get_or_404(record_id)
    nids = [x.id for x in rq.notes]
    nq = (db.session.query(SleepNote)
          .filter(SleepNote.id.in_(nids))
          .order_by(SleepNote.date_added.desc())
          .paginate(page=npg, per_page=5)
          )
    ipg = request.args.get('interruptionspage', 1, type=int)
    iids = [x.id for x in rq.interruptions]
    iq = (db.session.query(SleepInterruptionAssociation)
          .filter(SleepInterruptionAssociation.id.in_(iids))
          .order_by(SleepInterruptionAssociation.start.desc())
          )
    iqp = iq.paginate(page=ipg, per_page=5)

    d = SimpleNamespace()

    # Calculate minutes in bed and create string to pass to jinja2 template
    dbs = None  # duration before sleep
    das = None  # duration after sleep
    if rq.time_retire and rq.time_start_sleep:
        dbs = rq.time_start_sleep - rq.time_retire
        setattr(d, 'before_sleep', timedelta_to_str(dbs))
    else:
        setattr(d, 'before_sleep', 'Insufficient data')
    if rq.time_rise and rq.time_stop_sleep:
        das = rq.time_rise - rq.time_stop_sleep
        setattr(d, 'after_sleep', timedelta_to_str(das))
    else:
        setattr(d, 'after_sleep', 'Insufficient data')
    if dbs is not None or das is not None:
        dbas = pd.Timedelta(seconds=0)
        dbas += dbs if dbs else pd.Timedelta(seconds=0)
        dbas += das if das else pd.Timedelta(seconds=0)
    else:
        dbas = None
    s = timedelta_to_str(dbas) if dbas is not None else 'Insufficient data'
    setattr(d, 'awake', s)  # duration before and after sleep

    # Calculate total interruptions
    idq = [x.duration for x in iq.all()]
    if idq:
        ti = int(np.sum(np.array([i or 0 for i in idq])))
        dti = pd.Timedelta(minutes=ti)
    else:
        dti = None
    s = timedelta_to_str(dti) if dti is not None else 'None'
    setattr(d, 'interruptions', s)

    # Calculate hours and minutes asleep and create string to pass to jinja2 template
    if rq.time_start_sleep and rq.time_stop_sleep:
        dasl = rq.time_stop_sleep - rq.time_start_sleep
    else:
        dasl = None
    s = timedelta_to_str(dasl) if dasl is not None else 'Insifficient data'
    setattr(d, 'asleep', s)

    # Calculate adjusted sleep and create string for jinja2 template
    adjs = dasl
    if dti is not None and adjs is not None:
        adjs = dasl - dti
    s = timedelta_to_str(adjs) if adjs is not None else 'Insufficent data'
    setattr(d, 'asleep_adjusted', s)

    # Calculate hours and minutes in bed and create string to pass to jinja2 template
    if rq.time_retire and rq.time_rise:
        dib = rq.time_rise - rq.time_retire
    else:
        dib = None
    s = timedelta_to_str(dib) if dib is not None else 'Insufficient data'
    setattr(d, 'in_bed', s)

    return render_template('sleepdb/record.html',
                           record=rq, notespaginator=nq, interruptionspaginator=iqp,
                           durations=d,
                           )


@bp.route('/emotions')
@login_required
@requires_access(['admin'])
def emotions():
    page = request.args.get('page', 1, type=int)
    query = SleepEmotionTag.query.order_by(SleepEmotionTag.tag).paginate(page=page, per_page=10)
    return render_template('sleepdb/emotions.html', paginator=query)


@bp.route('/emotions/<int:emotion_id>')
@login_required
@requires_access(['admin'])
def emotion(emotion_id):
    return redirect(url_for('sleepdb.tag', tagtype='emotion', tagid=emotion_id))


@bp.route('/locations')
@login_required
@requires_access(['admin'])
def locations():
    page = request.args.get('page', 1, type=int)
    query = SleepLocationTag.query.order_by(SleepLocationTag.tag).paginate(page=page, per_page=10)
    return render_template('sleepdb/locations.html', paginator=query)


@bp.route('/locations/<int:location_id>')
@login_required
@requires_access(['admin'])
def location(location_id):
    return redirect(url_for('sleepdb.tag', tagtype='location', tagid=location_id))


@bp.route('/sensations')
@login_required
@requires_access(['admin'])
def sensations():
    page = request.args.get('page', 1, type=int)
    query = SleepSensationTag.query.order_by(SleepSensationTag.tag).paginate(page=page, per_page=10)
    return render_template('sleepdb/sensations.html', paginator=query)


@bp.route('/sensations/<int:sensation_id>')
@login_required
@requires_access(['admin'])
def sensation(sensation_id):
    return redirect(url_for('sleepdb.tag', tagtype='sensation', tagid=sensation_id))


@bp.route('/interruptions')
@login_required
@requires_access(['admin'])
def interruptions():
    page = request.args.get('page', 1, type=int)
    query = SleepInterruptionTag.query.order_by(SleepInterruptionTag.tag).paginate(page=page, per_page=10)
    return render_template('sleepdb/interruptions.html', paginator=query)


@bp.route('/interruptions/<int:interruption_id>')
@login_required
@requires_access(['admin'])
def interruption(interruption_id):
    return redirect(url_for('sleepdb.tag', tagtype='interruption', tagid=interruption_id))


@bp.route('/notes')
@login_required
@requires_access(['admin'])
def notes():
    page = request.args.get('page', 1, type=int)
    query = SleepNote.query.order_by(SleepNote.date_added.desc()).paginate(page=page, per_page=10)
    return render_template('sleepdb/notes.html', paginator=query)


@bp.route('/notes/<int:note_id>')
@login_required
@requires_access(['admin'])
def note(note_id):
    note_ = SleepNote.query.filter_by(id=note_id).first()
    return render_template('sleepdb/note.html', note=note_)


@bp.route('/records/create', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def create_record():
    form = SleepRecordForm()
    msg = 'I am sleeping in...'
    form.locations.choices = convert_tagmodels_to_options(SleepLocationTag, message=msg)

    if form.validate_on_submit():

        # Create sleep object and add to database
        record_ = SleepRecord(time_retire=form.time_retire.data,
                              time_start_sleep=form.time_start.data,
                              time_stop_sleep=form.time_stop.data,
                              time_rise=form.time_rise.data,
                              date_added=datetime.utcnow(),
                              )
        record_.locations = convert_options_to_tagmodels(form.locations.data, SleepLocationTag)

        # Commit to database
        db.session.add(record_)
        db.session.commit()

        if form.add_note.data:
            return redirect(url_for('sleepdb.create_note', record_id=record_.id))

        return redirect(url_for('sleepdb.record', record_id=record_.id))

    form.locations.data = ['bedroom', 'bed']
    return render_template('sleepdb/create_record.html',
                           form=form,
                           )


@bp.route('/records/edit/<int:record_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def update_record(record_id):
    r = SleepRecord.query.filter_by(id=record_id).first()
    f = SleepRecordForm()
    msg = {
        'emotions': 'Upon waking, I felt...',
        'locations': 'I slept in...',
        'sensations': 'Upon waking, I physically felt...',
    }
    f.emotions.choices = convert_tagmodels_to_options(SleepEmotionTag, message=msg['emotions'])
    f.locations.choices = convert_tagmodels_to_options(SleepLocationTag, message=msg['locations'])
    f.sensations.choices = convert_tagmodels_to_options(SleepSensationTag, message=msg['sensations'])

    if f.validate_on_submit():

        # Update sleep object
        r.time_retire = f.time_retire.data
        r.time_rise = f.time_rise.data
        r.time_start_sleep = f.time_start.data
        r.time_stop_sleep = f.time_stop.data
        r.rating = f.rating.data
        r.emotions = convert_options_to_tagmodels(f.emotions.data, SleepEmotionTag)
        r.locations = convert_options_to_tagmodels(f.locations.data, SleepLocationTag)
        r.sensations = convert_options_to_tagmodels(f.sensations.data, SleepSensationTag)

        for d in f.interruptions.data:  # update interruption objects
            obj = SleepInterruptionAssociation.query.filter_by(id=d['interruption_id']).first()
            if not d['delete_interruption'] and d['interruption']:
                obj.start, obj.stop, obj.duration = get_duration_tuple(
                    d['start'],
                    d['stop'],
                    d['duration']
                )
                tl = []
                for t in d['interruption']:
                    tobj = (db.session.query(SleepInterruptionTag).filter_by(tag=t).first() or
                            SleepInterruptionTag(tag=t))
                    tl.append(tobj)
                obj.tags = tl
                db.session.add(obj)
            else:
                db.session.delete(obj)

        db.session.add(r)
        db.session.commit()

        if f.add_interruption.data and f.add_note.data:
            return redirect(url_for('sleepdb.add_interruption', record_id=r.id, add_note=True))

        elif f.add_interruption.data:
            return redirect(url_for('sleepdb.add_interruption', record_id=r.id))

        elif f.add_note.data:
            return redirect(url_for('sleepdb.create_note', record_id=r.id))

        else:
            return redirect(url_for('sleepdb.record', record_id=r.id))

    # Add interruption subforms and data
    stmt = (db.select(SleepInterruptionAssociation)
            .where(SleepInterruptionAssociation.record_id == record_id))
    interrupt_objs = db.session.execute(stmt).scalars()
    c = convert_tagmodels_to_options(SleepInterruptionTag, message='My sleep was interrupted by...')
    for obj in interrupt_objs:
        subform = f.interruptions.append_entry()
        subform.form.start.data = obj.start
        subform.form.stop.data = obj.stop
        subform.form.duration.data = obj.duration
        subform.form.interruption.choices = c
        subform.form.interruption.data = [x.tag for x in obj.tags]
        subform.form.interruption_id.data = obj.id

    # Fill in form values
    f.rating.data = r.rating
    f.emotions.data = [x.tag for x in r.emotions] or []
    f.locations.data = [x.tag for x in r.locations] or []
    f.sensations.data = [x.tag for x in r.sensations] or []
    f.time_retire.data = r.time_retire
    f.time_rise.data = r.time_rise
    f.time_start.data = r.time_start_sleep
    f.time_stop.data = r.time_stop_sleep
    return render_template('sleepdb/update_record.html',
                           form=f,
                           record=r,
                           )


@bp.route('/set_sleep_time/<int:record_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def set_sleep_time(record_id):
    dt = datetime.fromtimestamp(float(request.args.get('time')))
    dt.replace(microsecond=0)
    record_ = SleepRecord.query.filter_by(id=record_id).first()
    record_.time_start_sleep = dt
    db.session.add(record_)
    db.session.commit()
    return redirect(url_for('sleepdb.record', record_id=record_id))


@bp.route('/set_wake_time/<int:record_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def set_wake_time(record_id):
    dt = datetime.fromtimestamp(float(request.args.get('time')))
    dt.replace(microsecond=0)
    record_ = SleepRecord.query.filter_by(id=record_id).first()
    record_.time_stop_sleep = dt
    db.session.add(record_)
    db.session.commit()
    return redirect(url_for('sleepdb.record', record_id=record_id))


@bp.route('/set_rise_time/<int:record_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def set_rise_time(record_id):
    dt = datetime.fromtimestamp(float(request.args.get('time')))
    dt.replace(microsecond=0)
    record_ = SleepRecord.query.filter_by(id=record_id).first()
    record_.time_rise = dt
    db.session.add(record_)
    db.session.commit()
    return redirect(url_for('sleepdb.record', record_id=record_id))


@bp.route('/records/rate/<int:record_id>', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def set_rating(record_id):
    f = RatingForm()
    f.emotions.choices = convert_tagmodels_to_options(SleepEmotionTag)
    f.sensations.choices = convert_tagmodels_to_options(SleepSensationTag)
    r = db.session.query(SleepRecord).filter_by(id=record_id).first()
    if f.validate_on_submit():
        r.rating = f.rating.data
        r.emotions = convert_options_to_tagmodels(f.emotions.data, SleepEmotionTag)
        r.sensations = convert_options_to_tagmodels(f.sensations.data, SleepSensationTag)
        db.session.add(r)
        db.session.commit()
        return redirect(url_for('sleepdb.record', record_id=record_id))
    f.rating.data = r.rating
    f.emotions.data = [x.tag for x in r.emotions]
    f.sensations.data = [x.tag for x in r.sensations]
    return render_template('sleepdb/set_rating.html', form=f, record=r)


@bp.post('/delete_record/<int:record_id>')
@login_required
@requires_access(['admin'])
def delete_record(record_id):
    sleep_ = SleepRecord.query.filter_by(id=record_id).first()
    db.session.delete(sleep_)
    db.session.commit()
    return redirect(url_for('sleepdb.records'))


@bp.route('/sessions/interruptions/add/<int:record_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def add_interruption(record_id):
    f = SleepInterruptionForm()
    f.interruption.choices = convert_tagmodels_to_options(
        SleepInterruptionTag,
        message='My sleep was interrupted by...',
        ph_args=dict(selected=True, hidden=True),
        placeholder=False,
    )
    if f.validate_on_submit():
        r = db.get_or_404(SleepRecord, record_id)
        ia = SleepInterruptionAssociation()
        ia.start, ia.stop, ia.duration = get_duration_tuple(f.start.data, f.stop.data, f.duration.data)
        tl = []
        for t in f.interruption.data:
            tobj = db.session.query(SleepInterruptionTag).filter_by(tag=t).first() or SleepInterruptionTag(tag=t)
            tl.append(tobj)
        ia.tags = tl
        r.interruptions.append(ia)
        db.session.add(r)
        db.session.commit()
        if f.add_interruption.data and f.add_note.data:
            return redirect(url_for('sleepdb.add_interruption', record_id=record_id, add_note=True))
        elif f.add_interruption.data:
            return redirect(url_for('sleepdb.add_interruption', record_id=record_id))
        elif f.add_note.data:
            return redirect(url_for('sleepdb.create_note', record_id=record_id))
        else:
            return redirect(url_for('sleepdb.record', record_id=record_id))
    r = db.get_or_404(SleepRecord, record_id)
    f.interruption.data = []
    if request.args.get('add_note'):
        f.add_note.data = True
    return render_template('sleepdb/edit_interruption.html', record=r, form=f)


@bp.route('/sessions/interruptions/edit/<int:interruption_id>', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def update_interruption(interruption_id: int):
    q = db.session.query(SleepInterruptionAssociation).filter_by(id=interruption_id).first()
    f = SleepInterruptionForm()
    f.interruption.choices = convert_tagmodels_to_options(SleepInterruptionTag)
    if f.validate_on_submit():
        q.start, q.stop, q.duration = get_duration_tuple(f.start.data, f.stop.data, f.duration.data)
        q.tags = convert_options_to_tagmodels(f.interruption.data, SleepInterruptionTag)
        db.session.add(q)
        db.session.commit()
        if f.add_interruption.data and f.add_note.data:
            return redirect(url_for('sleepdb.add_interruption', record_id=q.record_id, add_note=True))
        elif f.add_interruption.data:
            return redirect(url_for('sleepdb.add_interruption', record_id=q.record_id))
        elif f.add_note.data:
            return redirect(url_for('sleepdb.create_note', record_id=q.record_id))
        return redirect(url_for('sleepdb.record', record_id=q.record_id))
    f.interruption.data = [x.tag for x in q.tags]
    f.start.data = q.start
    f.stop.data = q.stop
    f.duration.data = q.duration
    return render_template('/sleepdb/edit_interruption.html', form=f, interruption=q)


@bp.route('/notes/create', methods=('GET', 'POST'))
@bp.route('/notes/create/<int:record_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def create_note(record_id=None):
    form = SleepNoteForm()
    if form.validate_on_submit():
        date = datetime.utcnow()
        note_ = SleepNote(record_id=record_id,
                          note=form.note.data,
                          important=form.important.data,
                          date_added=date,
                          last_edited=date,
                          )
        db.session.add(note_)
        db.session.commit()
        return redirect(url_for('sleepdb.note', note_id=note_.id))
    record_ = SleepRecord.query.filter_by(id=record_id).first()
    return render_template('sleepdb/create_note.html', form=form, record=record_)


@bp.route('/notes/edit/<int:note_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def update_note(note_id):
    note_ = SleepNote.query.filter_by(id=note_id).first()
    form = SleepNoteForm()
    if form.validate_on_submit():
        note_.note = form.note.data
        note_.important = form.important.data
        note_.last_edited = datetime.utcnow()
        db.session.add(note_)
        db.session.commit()
        return redirect(url_for('sleepdb.note', note_id=note_id))
    form.note.data = note_.note
    form.important.data = note_.important
    return render_template('sleepdb/update_note.html', form=form, note=note_)


@bp.post('/delete_note/<int:note_id>')
@login_required
@requires_access(['admin'])
def delete_note(note_id):
    note_ = SleepNote.query.filter_by(id=note_id).first()
    record_ = note_.record
    db.session.delete(note_)
    db.session.commit()
    if record_:
        return redirect(url_for('sleepdb.record', record_id=record_.id))
    return redirect(url_for('sleepdb.notes'))


@bp.route('/stats/<sleeptype>')
@login_required
@requires_access(['admin'])
def sleepstats(sleeptype):
    sleeptype = {
        'regular': 'reg',
        'nap': 'nap',
        'powernap': 'pnap',
        'overall': 'all'
    }[sleeptype]
    n = datetime.now()
    dr = {
        'week': (n - timedelta(days=7), n),
        'month': (n - timedelta(days=30), n),
        'halfyear': (n - timedelta(days=180), n),
        'all': None,
    }
    d = get_duration_data(True)
    s = SimpleNamespace()
    for k, v in dr.items():
        o = SimpleNamespace()
        setattr(s, k, o)
        fd = filter_duration_data([sleeptype], data=d, dates=v, with_tags=True)
        ds = get_duration_stats(fd)
        setattr(o, 'durationstats', ds)
        t = get_all_tags_stats(fd)
        setattr(o, 'tagstats', t)
    return render_template('sleepdb/sleepstats.html', stats=s, sleeptype=sleeptype)


@bp.route('/durationsplot/<sleeptype>/<statstype>/<plottype>')
@login_required
@requires_access(['admin'])
def durationsplot(sleeptype, statstype, plottype):
    ptypes = {
        'hist': sns.histplot,
        'boxplot': sns.boxplot,
    }
    if plottype not in ptypes.keys():
        plot = io.BytesIO(b'')
    else:
        plot = io.BytesIO()
        pltfunc = ptypes[plottype]
        s = SleepDurationStats([sleeptype])
        d = getattr(getattr(getattr(s, sleeptype), statstype), 'data').apply(to_hours)
        fig = pltfunc(d).get_figure()
        fig.savefig(plot)
        fig.clf()
        plot.seek(0)
    return send_file(plot, mimetype='image/png')


@bp.route('/<string:tagtype>/<int:tagid>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def tag(tagtype: str, tagid: int):
    page = request.args.get('page', 1, type=int)
    mtt = tagtype + 's'
    tof = {'emotions': SleepEmotionTag,
           'sensations': SleepSensationTag,
           'locations': SleepLocationTag,
           'interruptions': SleepInterruptionTag}
    tobj = db.session.query(tof[mtt]).filter_by(id=tagid).first()
    d = get_duration_data(True)
    s = get_tag_stats_v2(tagid, mtt, d)
    fd = filter_duration_data(data=d, tag=(tagid, mtt))
    for n, d in fd.items():
        so = get_duration_stats(d, n)
        setattr(so, 'proportion', round(so.in_bed.count / s.count, 3))
        setattr(s, n, so)
    rs = [int(x) for x in fd['all']['record_id'].unique()]
    u = SimpleNamespace()
    setattr(s, 'unfinished', u)
    uc = s.count - (s.reg.in_bed.count +
                    s.nap.in_bed.count +
                    s.pnap.in_bed.count)
    setattr(u, 'count', uc)
    up = uc / s.count
    setattr(u, 'proportion', round(up, 3))
    p = (db.session.query(SleepRecord)
         .filter(SleepRecord.id.in_(rs))
         .order_by(SleepRecord.time_retire.desc())
         .paginate(page=page, per_page=10))
    return render_template('sleepdb/tagpage.html',
                           tagtype=tagtype,
                           tag=tobj,
                           stats=s,
                           paginator=p
                           )


@bp.route('/<string:tagtype>/edit/<int:tagid>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def update_tag(tagtype: str, tagid: str):
    f = TagForm()
    tof = {'emotion': SleepEmotionTag,
           'sensation': SleepSensationTag,
           'location': SleepLocationTag,
           'interruption': SleepInterruptionTag}
    t = db.session.query(tof[tagtype]).filter_by(id=tagid).first()
    if db.session.query(tof[tagtype]).filter_by(tag=f.tag.data).first() is None:
        if f.validate_on_submit():
            t.tag = f.tag.data
            db.session.add(t)
            db.session.commit()
            return redirect(url_for('sleepdb.tag', tagtype=tagtype, tagid=tagid))
    else:
        flash(message=f'Another {tagtype} tag with that name already exists', category='warning')
    f.tag.data = t.tag
    return render_template('sleepdb/update_tag.html', form=f, tagtype=tagtype, tag=t)
