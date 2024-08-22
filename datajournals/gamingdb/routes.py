import datetime
from types import SimpleNamespace

import numpy as np
import pandas as pd
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from datajournals import db
from datajournals.authorization import requires_access
from datajournals.base_methods import convert_tagmodels_to_options, convert_options_to_tagmodels, get_duration_tuple
from datajournals.gamingdb import bp
from datajournals.gamingdb.forms import NoteForm, TagForm, InterruptionForm, RecordForm, RatingForm
from datajournals.gamingdb.helper import datetimes_to_string_spans, seconds_to_hrs_mins, hrs_mins_to_string, \
    gamenames_to_options, RecordDurationStats, RecordRatingStats, BasicUsageStats, TagStats, get_notes_stats, \
    get_games_stats
from datajournals.models import GamingSessionRecord, GamingNote, Game, GamingEmotionTag, GamingInterruptionTag, \
    GamingSessionInterruption


@bp.route('/dashboard')
@bp.route('/index')
@bp.route('/')
@login_required
@requires_access(['admin'])
def index():
    q = db.session.query(GamingSessionRecord)
    lr = q.order_by(GamingSessionRecord.start_time.desc()).first()
    fr = q.order_by(GamingSessionRecord.start_time.asc()).first()
    r = RecordDurationStats()
    b = BasicUsageStats()
    ra = RecordRatingStats()
    n = get_notes_stats()
    e = TagStats()
    i = TagStats('interruptions')
    g = get_games_stats()
    return render_template('gamingdb/index.html',
                           basicstats=b,
                           durationstats=r,
                           ratingstats=ra,
                           notestats=n,
                           gamestats=g,
                           emotionstats=e,
                           interruptionstats=i,
                           latest=lr,
                           first=fr
                           )


@bp.route('/search', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def search():
    page = request.args.get('page', 1, type=int)
    sa = request.args
    if 'emotions' in sa:
        sq = sa['emotions']
        st = 'emotions'
        dq = db.session.query(GamingEmotionTag).filter(GamingEmotionTag.tag.like(f'%{sq}%'))
    elif 'interruptions' in sa:
        sq = sa['interruptions']
        st = 'interruptions'
        dq = db.session.query(GamingInterruptionTag).filter(GamingInterruptionTag.tag.like(f'%{sq}%'))
    elif 'notes' in sa:
        sq = sa['notes']
        st = 'notes'
        dq = db.session.query(GamingNote).filter(GamingNote.note.like(f'%{sq}%'))
    else:
        sq = sa['games']
        st = 'games'
        dq = db.session.query(Game).filter(Game.name.like(f'%{sq}%'))
    p = dq.paginate(page=page, per_page=10)
    return render_template('gamingdb/search_results.html', type=st, query=sq, paginator=p)


@bp.route('/sessions')
@login_required
@requires_access(['admin'])
def records():
    page = request.args.get('page', 1, type=int)
    query = GamingSessionRecord.query.order_by(GamingSessionRecord.start_time.desc())
    count = query.count()
    pagination = query.paginate(page=page, per_page=10)
    return render_template('gamingdb/records.html', paginator=pagination, count=count)


# TODO add logic to handle case where interruption duration exceeeds session duration
@bp.route('/sessions/<int:record_id>')
@login_required
@requires_access(['admin'])
def record(record_id):
    page = request.args.get('page', 1, type=int)
    record_query: GamingSessionRecord = GamingSessionRecord.query.get_or_404(record_id)
    note_ids = [x.id for x in record_query.notes]
    notes_query = GamingNote.query.filter(GamingNote.id.in_(note_ids)).order_by(GamingNote.date_added.desc())
    paginator = notes_query.paginate(page=page, per_page=10)
    # TODO replace numpy calcs with pandas calcs
    if record_query:

        # Calculate total hours, minutes of interruptions and create string for jinja2 template
        interrupt_array = np.array([i.duration for i in record_query.session_interruptions])
        filtered_arry = interrupt_array[interrupt_array != np.array(None)]
        interruption_total = np.sum(filtered_arry)
        interruption_seconds = interruption_total * 60 if interruption_total else 0
        interruption_tuple = seconds_to_hrs_mins(interruption_seconds)
        duration_interruptions = f'{hrs_mins_to_string(interruption_tuple)}' if any(interruption_tuple) else ''
        # Calculate hours, minutes of playtime and total session and create string for jinja2 template
        if record_query.stop_time:
            session = record_query.stop_time - record_query.start_time
            session_tuple = seconds_to_hrs_mins(session.seconds)
            duration_session = hrs_mins_to_string(session_tuple)
            playing_tuple = seconds_to_hrs_mins(session.seconds - interruption_seconds)
            duration_playing = hrs_mins_to_string(playing_tuple)
            session_span = datetimes_to_string_spans(record_query.start_time, record_query.stop_time)
        else:
            duration_session = 'No stop time'
            duration_playing = 'No stop time'
            session_span = datetimes_to_string_spans(record_query.start_time, record_query.start_time)
        return render_template('gamingdb/record.html',
                               record=record_query, paginator=paginator,
                               duration_session=duration_session,
                               duration_playing=duration_playing,
                               duration_interruptions=duration_interruptions,
                               session_span=session_span,
                               )


@bp.route('/sessions/create', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def create_record():
    f = RecordForm()
    f.game.choices = gamenames_to_options()
    if f.validate_on_submit():
        r = GamingSessionRecord()
        r.start_time = f.start_time.data
        r.date_added = datetime.datetime.utcnow()
        gn = [x.name for x in Game.query.all()]
        if f.game.data in gn:
            r.game = Game.query.filter_by(name=f.game.data).first()
        else:
            r.game = Game(name=f.game.data)
        db.session.add(r)
        db.session.commit()
        if f.add_note.data:
            return redirect(url_for('gamingdb.create_note', record_id=r.id))
        return redirect(url_for('gamingdb.record', record_id=r.id))
    f.game.data = ''
    return render_template('gamingdb/create_record.html', form=f)


@bp.route('/sessions/edit/<int:record_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def update_record(record_id):
    f = RecordForm()
    r: GamingSessionRecord = GamingSessionRecord.query.filter_by(id=record_id).first()
    f.game.choices = gamenames_to_options()
    f.emotions.choices = convert_tagmodels_to_options(GamingEmotionTag,
                                                      message='This session made me feel...',
                                                      ph_args=dict(hidden=True, selected=True))
    if f.validate_on_submit():
        r.start_time = f.start_time.data
        r.stop_time = f.stop_time.data
        r.session_rating = f.session_rating.data
        r.game = Game.query.filter_by(name=f.game.data).first() if \
            f.game.data in [x.name for x in Game.query.all()] else \
            Game(name=f.game.data)
        r.emotions = convert_options_to_tagmodels(f.emotions.data, GamingEmotionTag)
        for d in f.interruptions.data:
            sio = GamingSessionInterruption.query.filter_by(id=d['interruption_id']).first()
            if not d['delete_interruption']:
                sio.start_time, sio.stop_time, sio.duration = get_duration_tuple(
                    d['start_time'], d['stop_time'], d['duration'])
                itol = []
                for its in d['interruption']:
                    ito = (db.session.query(GamingInterruptionTag).filter_by(tag=its).first() or
                           GamingInterruptionTag(tag=its))
                    itol.append(ito)
                    sio.tags = itol
                db.session.add(sio)
            else:
                db.session.delete(sio)

        db.session.add(r)
        db.session.commit()
        if f.add_interruption.data:
            return redirect(
                url_for(
                    'gamingdb.create_session_interruption',
                    record_id=r.id,
                    add_note=f.add_note.data))
        elif f.add_note.data:
            return redirect(url_for('gamingdb.create_note', record_id=r.id))
        return redirect(url_for('gamingdb.record', record_id=r.id))

    ic = convert_tagmodels_to_options(GamingInterruptionTag,
                                      message='This gaming session was interrupted by...',
                                      ph_args=dict(hidden=True, selected=True))
    f.start_time.data = r.start_time
    f.stop_time.data = r.stop_time
    f.session_rating.data = r.session_rating
    f.game.data = r.game.name
    f.emotions.data = [x.tag for x in r.emotions]
    si = [x for x in r.session_interruptions]
    si = sorted(si, key=lambda e: e.id)
    for s in si:
        sub = f.interruptions.append_entry()
        sub.form.start_time.data = s.start_time
        sub.form.stop_time.data = s.stop_time
        sub.form.duration.data = s.duration
        sub.form.interruption.choices = ic
        sub.form.interruption.data = [x.tag for x in s.tags]
        sub.form.interruption_id.data = s.id
    return render_template('gamingdb/update_record.html', form=f, record=r)


@bp.route('/sessions/edit/quick/<int:record_id>', methods=('POST', 'GET'))
@login_required
@requires_access(['admin'])
def quickupdate_record(record_id):
    """
    Set stop time on gaming session, given datetime.
    :param record_id:
    :return:
    """
    dt = datetime.datetime.fromtimestamp(float(request.args.get('time')))
    dt.replace(microsecond=0)
    r = GamingSessionRecord.query.filter_by(id=record_id).first()
    r.stop_time = dt
    db.session.add(r)
    db.session.commit()
    return redirect(url_for('gamingdb.record', record_id=r.id))


@bp.route('/sessions/interruptions/<int:session_interruption_id>')
@login_required
@requires_access(['admin'])
def session_interruption(session_interruption_id):
    si = GamingSessionInterruption.query.filter_by(id=session_interruption_id).first()
    return render_template('gamingdb/session_interruption.html', session_interruption=si)


@bp.route('/sessions/interruptions/create/<int:record_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def create_session_interruption(record_id):
    f = InterruptionForm()
    f.interruption.choices = convert_tagmodels_to_options(
        GamingInterruptionTag,
        message='Choose or create a tag',
        ph_args=dict(selected=True, hidden=True)
    )
    if f.validate_on_submit():
        r = GamingSessionRecord.query.filter_by(id=record_id).first()
        i = GamingSessionInterruption()
        i.start_time, i.stop_time, i.duration = get_duration_tuple(f.start_time.data,
                                                                   f.stop_time.data,
                                                                   f.duration.data)
        i.record = r
        i.tags = convert_options_to_tagmodels(f.interruption.data, GamingInterruptionTag)
        db.session.add(i)
        db.session.commit()
        if f.add_interruption.data:
            return redirect(
                url_for(
                    'gamingdb.create_session_interruption',
                    record_id=record_id,
                    add_note=f.add_note.data
                ))
        if f.add_note.data:
            return redirect(url_for('gamingdb.create_note', record_id=record_id))
        if not i.duration:
            return redirect(url_for('gamingdb.session_interruption', session_interruption_id=i.id))
        else:
            return redirect(url_for('gamingdb.record', record_id=r.id))
    r = db.get_or_404(GamingSessionRecord, record_id)
    f.interruption.data = ''
    if request.args.get('add_note'):
        f.add_note.data = request.args.get('add_note', False, type=bool)
    return render_template('gamingdb/create_session_interruption.html', record=r, form=f)


@bp.route('/sessions/interruptions/edit/<int:session_interruption_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def update_session_interruption(session_interruption_id):
    f = InterruptionForm()
    f.interruption.choices = convert_tagmodels_to_options(
        GamingInterruptionTag,
        message='This session was interrupted by...',
        ph_args=dict(selected=True, hidden=True)
    )
    si: GamingSessionInterruption = GamingSessionInterruption.query.filter_by(id=session_interruption_id).first()
    if f.validate_on_submit():
        r = si.record
        si.tags = convert_options_to_tagmodels(f.interruption.data, GamingInterruptionTag)
        si.start_time, si.stop_time, si.duration = get_duration_tuple(
            f.start_time.data, f.stop_time.data, f.duration.data
        )
        db.session.add(si)
        db.session.commit()
        if f.add_interruption.data:
            return redirect(url_for('gamingdb.create_session_interruption',
                                    record_id=r.id,
                                    add_note=f.add_note.data))
        elif f.add_note.data:
            return redirect(url_for('gamingdb.create_note', record_id=r.id))
        elif not si.duration:
            return redirect(url_for('gamingdb.session_interruption',
                                    session_interruption_id=session_interruption_id))
        else:
            return redirect(url_for('gamingdb.record', record_id=r.id))
    f.interruption.data = [x.tag for x in si.tags]
    f.duration.data = si.duration
    f.start_time.data = si.start_time
    f.stop_time.data = si.stop_time
    return render_template('gamingdb/create_session_interruption.html', form=f,
                           session_interruption=si)


@bp.route('/sessions/interruptions/edit/quick/<int:session_interruption_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def quickupdate_session_interruption(session_interruption_id):
    """
    Updates the session interruption stop time with a given time
    :param session_interruption_id:
    :return:
    """
    dt = datetime.datetime.fromtimestamp(float(request.args.get('time')))
    dt.replace(microsecond=0)
    si: GamingSessionInterruption = GamingSessionInterruption.query.filter_by(id=session_interruption_id).first()
    r = si.record
    si.start_time, si.stop_time, si.duration = get_duration_tuple(si.start_time, dt, si.stop_time)
    db.session.add(si)
    db.session.commit()
    return redirect(url_for('gamingdb.record', record_id=r.id))


@bp.post('/sessions/interruptions/delete/<int:session_interruption_id>')
@login_required
@requires_access(['admin'])
def delete_session_interruption(session_interruption_id):
    si: GamingSessionInterruption = GamingSessionInterruption.query.filter_by(id=session_interruption_id).first()
    r: GamingSessionRecord = si.record
    db.session.delete(si)
    db.session.commit()
    return redirect(url_for('gamingdb.record', record_id=r.id))


@bp.post('/sessions/delete/<int:record_id>')
@login_required
@requires_access(['admin'])
def delete_record(record_id):
    r = GamingSessionRecord.query.filter_by(id=record_id).first()
    db.session.delete(r)
    db.session.commit()
    return redirect(url_for('gamingdb.records'))


@bp.route('/games')
@login_required
@requires_access(['admin'])
def games():
    page = request.args.get('page', 1, type=int)
    query = Game.query.order_by(Game.name)
    count = query.count()
    pagination = query.paginate(page=page, per_page=10)
    return render_template('gamingdb/games.html', paginator=pagination, count=count)


@bp.route('/games/<int:game_id>')
@login_required
@requires_access(['admin'])
def game(game_id):
    recordpage = request.args.get('recordspage', 1, type=int)
    notepage = request.args.get('notespage', 1, type=int)
    gq = Game.query.filter_by(id=game_id).first()
    rids = [x.id for x in gq.records]
    rq = (GamingSessionRecord
          .query.filter(GamingSessionRecord.id.in_(rids))
          .order_by(GamingSessionRecord.start_time.desc()))
    rpgr = rq.paginate(page=recordpage, per_page=10)
    nids = [x.id for x in gq.notes]
    nq = (GamingNote
          .query.filter(GamingNote.id.in_(nids))
          .order_by(GamingNote.date_added.desc()))
    npgr = nq.paginate(page=notepage, per_page=10)
    df = pd.read_sql(rq.statement, db.engine)
    stats = SimpleNamespace()
    setattr(stats, 'durations', RecordDurationStats(df))
    setattr(stats, 'ratings', RecordRatingStats(df))
    setattr(stats, 'usage', BasicUsageStats(df))
    
    # Get data for emotions tags
    eq = (db.session.query(GamingEmotionTag.id.label('emotions'))
          .join(GamingEmotionTag.records)
          .filter(GamingSessionRecord.id.in_(rids))
          )
    df = pd.read_sql(eq.statement, db.engine)
    ec = df['emotions'].value_counts().reset_index()
    ep = df['emotions'].value_counts(normalize=True).reset_index()
    ecp = pd.merge(ec, ep, on=['emotions'])
    ecpl = ecp.nlargest(1, ['count'], 'all')
    o = SimpleNamespace()
    setattr(stats, 'emotions', o)
    t = None
    c = None
    p = None
    if ecpl.shape[0]:
        t = [db.session.query(GamingEmotionTag).filter_by(id=x).first() for x in ecpl['emotions']]
        c = ecpl.loc[0, 'count']
        p = round(ecpl.loc[0, 'proportion'], 3)
    so = SimpleNamespace()
    setattr(o, 'mostcommon', so)
    setattr(so, 'tags', t)
    setattr(so, 'count', c)
    setattr(so, 'proportion', p)
    iecp = ecp.set_index(['emotions'])
    a = [(
        db.session.query(GamingEmotionTag).filter_by(id=x).first(),
        iecp.loc[x, 'count'],
        round(iecp.loc[x, 'proportion'], 3),
    ) for x in iecp.index]
    setattr(o, 'all', a)
    
    # Get data for emotions tags
    iq = (db.session.query(GamingInterruptionTag.id.label('interruptions'))
          .join(GamingInterruptionTag.session_interruptions)
          .join(GamingSessionInterruption.record)
          .filter(GamingSessionRecord.id.in_(rids))
          )
    df = pd.read_sql(iq.statement, db.engine)
    ic = df['interruptions'].value_counts().reset_index()
    ip = df['interruptions'].value_counts(normalize=True).reset_index()
    icp = pd.merge(ic, ip, on=['interruptions'])
    icpl = icp.nlargest(1, ['count'], 'all')
    o = SimpleNamespace()
    setattr(stats, 'interruptions', o)
    t = None
    c = None
    p = None
    if icpl.shape[0]:
        t = [db.session.query(GamingInterruptionTag).filter_by(id=x).first() for x in icpl['interruptions']]
        c = icpl.loc[0, 'count']
        p = round(icpl.loc[0, 'proportion'], 3)
    so = SimpleNamespace()
    setattr(o, 'mostcommon', so)
    setattr(so, 'tags', t)
    setattr(so, 'count', c)
    setattr(so, 'proportion', p)
    iicp = icp.set_index(['interruptions'])
    a = [(
        db.session.query(GamingInterruptionTag).filter_by(id=x).first(),
        iicp.loc[x, 'count'],
        round(iicp.loc[x, 'proportion'], 3),
    ) for x in iicp.index]
    setattr(o, 'all', a)
    return render_template('gamingdb/game.html', game=gq, recordpaginator=rpgr, stats=stats,
                           notepaginator=npgr)


@bp.route('/games/edit/<int:game_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def update_game(game_id):
    form = TagForm()
    game_query = Game.query
    game_names = [g.name for g in game_query.all()]
    game_ = game_query.filter_by(id=game_id).first()
    game_names.remove(game_.name)
    if form.tag.data not in game_names:
        if form.validate_on_submit():
            game_.name = form.tag.data
            db.session.add(game_)
            db.session.commit()
            return redirect(url_for('gamingdb.game', game_id=game_id))
    else:
        flash(f'"{form.tag.data}" already exists in the database.\nChoose another name.', 'warning')
    form.tag.data = game_.name
    return render_template('gamingdb/update_game.html', form=form, game=game_)


@bp.route('/emotions/<int:emotion_id>')
@login_required
@requires_access(['admin'])
def emotion(emotion_id):
    page = request.args.get('page', 1, type=int)
    eq = GamingEmotionTag.query.filter_by(id=emotion_id).first()
    rq = (db.session.query(GamingSessionRecord)
          .join(GamingSessionRecord.emotions)
          .filter(GamingEmotionTag.id == eq.id)
          .order_by(GamingSessionRecord.start_time.desc())
          )
    r_ids = [x.id for x in rq.all()]
    paginator = rq.paginate(page=page, per_page=10)
    stats = SimpleNamespace()
    df = pd.read_sql(rq.statement, db.engine)
    setattr(stats, 'durations', RecordDurationStats(df))
    setattr(stats, 'ratings', RecordRatingStats(df))

    # Get tags dataframe
    esq = (db.session.query(
        GamingSessionRecord.id.label('records'),
        GamingSessionRecord.start_time,
        GamingSessionRecord.stop_time,
        GamingEmotionTag.id.label('emotions'),
        GamingInterruptionTag.id.label('interruptions')
    )
           .outerjoin(GamingSessionRecord.emotions)
           .outerjoin(GamingSessionRecord.session_interruptions)
           .outerjoin(GamingSessionInterruption.tags)
           )
    df = pd.read_sql(esq.statement, db.engine)

    # Clean and set basic usage data
    uef = df.dropna(subset=['emotions'])
    uef = uef.drop_duplicates(['records', 'emotions'])
    fuef = uef[uef['emotions'] == emotion_id]
    setattr(stats, 'usage', BasicUsageStats(fuef))

    # Set joint emotions data
    fef = uef[uef['records'].isin(r_ids)]
    fef = fef[fef['emotions'] != emotion_id]
    setattr(stats, 'emotions', TagStats(data=fef))

    # Filters and calculations for joint interruptions data
    uif = df.dropna(subset=['interruptions'])
    uif = uif.drop_duplicates(['records', 'interruptions'])
    fif = uif[uif['records'].isin(r_ids)]
    setattr(stats, 'interruptions', TagStats(tagtype='interruptions', data=fif))

    return render_template('gamingdb/emotion.html', paginator=paginator,
                           stats=stats, emotion=eq,
                           )


@bp.route('/emotions/edit/<int:emotion_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def update_emotion(emotion_id):
    form = TagForm()
    tags_query = GamingEmotionTag.query
    tagstrings = [t.tag for t in tags_query.all()]
    tag = tags_query.filter_by(id=emotion_id).first()
    tagstrings.remove(tag.tag)
    if form.tag.data not in tagstrings:
        if form.validate_on_submit():
            tag.tag = form.tag.data
            db.session.add(tag)
            db.session.commit()
            return redirect(url_for('gamingdb.emotion', emotion_id=emotion_id))
    else:
        flash(f'"{form.tag.data}" already exists in the database.\nChoose another tag.', 'warning')
    form.tag.data = tag.tag
    return render_template('gamingdb/update_emotion.html', form=form, emotion=tag)


@bp.route('/emotions')
@login_required
@requires_access(['admin'])
def emotions():
    page = request.args.get('page', 1, type=int)
    q = db.session.query(GamingEmotionTag).order_by(GamingEmotionTag.tag)
    p = q.paginate(page=page, per_page=10)
    return render_template('gamingdb/emotions.html', paginator=p)


@bp.route('/interruptions/<int:interruption_id>')
@login_required
@requires_access(['admin'])
def interruption(interruption_id):
    page = request.args.get('page', 1, type=int)
    iq = GamingInterruptionTag.query.filter_by(id=interruption_id).first()
    rq = (db.session.query(GamingSessionRecord)
          .join(GamingSessionRecord.session_interruptions)
          .join(GamingSessionInterruption.tags)
          .filter(GamingInterruptionTag.id == interruption_id)
          .distinct()
          .order_by(GamingSessionRecord.start_time.desc())
          )
    r_ids = [x.id for x in rq.all()]
    paginator = rq.paginate(page=page, per_page=10)
    stats = SimpleNamespace()
    df = pd.read_sql(rq.statement, db.engine)
    setattr(stats, 'durations', RecordDurationStats(df))
    setattr(stats, 'ratings', RecordRatingStats(df))

    # Get tags dataframe
    isq = (
        db.session.query(
            GamingSessionRecord.id.label('records'),
            GamingSessionRecord.start_time,
            GamingSessionRecord.stop_time,
            GamingEmotionTag.id.label('emotions'),
            GamingInterruptionTag.id.label('interruptions')
        )
        .outerjoin(GamingSessionRecord.emotions)
        .outerjoin(GamingSessionRecord.session_interruptions)
        .outerjoin(GamingSessionInterruption.tags))
    df = pd.read_sql(isq.statement, db.engine)

    # Set basic usage data
    uif = df.dropna(subset=['interruptions'])
    uif = uif.drop_duplicates(['records', 'interruptions'])
    fuif = uif[uif['interruptions'] == interruption_id]
    setattr(stats, 'usage', BasicUsageStats(fuif))

    # Filters and calculations for joint interruptions data
    fif = uif[uif['records'].isin(r_ids)]
    fif = fif[fif['interruptions'] != interruption_id]
    setattr(stats, 'interruptions', TagStats(tagtype='interruptions', data=fif))

    # Filters and calculations for joint emotions data
    uef = df.dropna(subset=['emotions'])
    uef = uef.drop_duplicates(['records', 'emotions'])
    fef = uef[uef['records'].isin(r_ids)]
    setattr(stats, 'emotions', TagStats(data=fef))

    return render_template('gamingdb/interruption.html', paginator=paginator,
                           stats=stats, interruption=iq,
                           )


@bp.route('/interruptions/edit/<int:interruption_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def update_interruption(interruption_id):
    form = TagForm()
    tags_query = GamingInterruptionTag.query
    tagstrings = [t.tag for t in tags_query.all()]
    tag = tags_query.filter_by(id=interruption_id).first()
    tagstrings.remove(tag.tag)
    if form.tag.data not in tagstrings:
        if form.validate_on_submit():
            tag.tag = form.tag.data
            db.session.add(tag)
            db.session.commit()
            return redirect(url_for('gamingdb.interruption', interruption_id=interruption_id))
    else:
        flash(f'"{form.tag.data}" already exists in the database.\nChoose another tag.', 'warning')
    form.tag.data = tag.tag
    return render_template('gamingdb/update_interruption.html', form=form, interruption=tag)


@bp.route('/interruptions')
@login_required
@requires_access(['admin'])
def interruptions():
    page = request.args.get('page', 1, type=int)
    q = db.session.query(GamingInterruptionTag).order_by(GamingInterruptionTag.tag)
    p = q.paginate(page=page, per_page=10)
    return render_template('gamingdb/interruptions.html', paginator=p)


@bp.route('/notes')
@login_required
@requires_access(['admin'])
def notes():
    page = request.args.get('page', 1, type=int)
    query = GamingNote.query.order_by(GamingNote.date_added.desc())
    count = query.count()
    pagination = query.paginate(page=page, per_page=10)
    return render_template('gamingdb/notes.html', paginator=pagination, count=count)


@bp.route('/notes/<int:note_id>')
@login_required
@requires_access(['admin'])
def note(note_id):
    query = GamingNote.query.filter_by(id=note_id).first()
    return render_template('gamingdb/note.html', note=query)


@bp.route('/notes/create', methods=['GET', 'POST'])
@bp.route('/notes/create/<int:record_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def create_note(record_id: int = None):
    record_ = GamingSessionRecord.query.filter_by(id=record_id).first() if record_id else None
    game_id = record_.game.id if record_id else request.args.get('game_id')
    game_ = Game.query.filter_by(id=game_id).first() if game_id else None
    form = NoteForm()
    form.game.choices = gamenames_to_options()

    if form.validate_on_submit():
        note_ = GamingNote()
        if record_:
            note_.record = record_
            note_.game = note_.record.game
        elif game_:
            note_.game = game_
        elif form.game.data:
            game_names = [x.name for x in Game.query.all()]
            if form.game.data in game_names:
                note_game = Game.query.filter_by(name=form.game.data).first()
            else:
                note_game = Game(name=form.game.data)
            note_.game = note_game
        note_.date_added = datetime.datetime.now()
        note_.note = form.note.data
        note_.important = form.important.data

        db.session.add(note_)
        db.session.commit()

        if record_:
            return redirect(url_for('gamingdb.record', record_id=record_id))
        if game_:
            return redirect(url_for('gamingdb.game', game_id=game_id))
        return redirect(url_for('gamingdb.note', note_id=note_.id))
    game_name = game_.name if game_ else ''
    form.game.data = game_name
    return render_template('gamingdb/create_note.html', form=form, record=record_, game=game_)


@bp.route('/notes/edit/<int:note_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin'])
def update_note(note_id):
    form = NoteForm()
    form.game.choices = gamenames_to_options()
    note_ = GamingNote.query.filter_by(id=note_id).first()
    if form.validate_on_submit():
        note_.note = form.note.data
        note_.important = form.important.data
        if not note_.record:
            if form.game.data:
                game_names = [x.name for x in Game.query.all()]
                if form.game.data in game_names:
                    note_game = Game.query.filter_by(name=form.game.data).first()
                else:
                    note_game = Game(name=form.game.data)
                note_.game = note_game
            else:
                note_.game = None
        db.session.add(note_)
        db.session.commit()
        return redirect(url_for('gamingdb.note', note_id=note_id))
    form.note.data = note_.note
    form.important.data = note_.important
    form.game.data = note_.game.name if note_.game else ''
    return render_template('gamingdb/create_note.html',
                           form=form, game=note_.game, record=note_.record, note=note_)


@bp.post('/notes/delete/<int:note_id>')
@login_required
@requires_access(['admin'])
def delete_note(note_id):
    note_ = GamingNote.query.filter_by(id=note_id).first()
    record_ = note_.record
    db.session.delete(note_)
    db.session.commit()
    if record_:
        return redirect(url_for('gamingdb.record', record_id=record_.id))
    return redirect(url_for('gamingdb.notes'))


@bp.route('/sessions/rate/<int:record_id>', methods=['GET', 'POST'])
@login_required
@requires_access(['admin'])
def set_rating(record_id):
    f = RatingForm()
    f.emotions.choices = convert_tagmodels_to_options(GamingEmotionTag)
    r = db.session.query(GamingSessionRecord).filter_by(id=record_id).first()
    if f.validate_on_submit():
        r.session_rating = f.rating.data
        r.emotions = convert_options_to_tagmodels(f.emotions.data, GamingEmotionTag)
        db.session.add(r)
        db.session.commit()
        if f.add_note.data:
            return redirect(url_for('gamingdb.create_note', record_id=record_id))
        return redirect(url_for('gamingdb.record', record_id=record_id))
    f.emotions.data = [x.tag for x in r.emotions]
    return render_template('gamingdb/set_rating.html', form=f, record=r)
