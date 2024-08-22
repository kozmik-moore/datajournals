from datetime import datetime
from types import SimpleNamespace

import pandas as pd
from flask import render_template, request, url_for, redirect, flash
from flask_login import login_required

from datajournals import db
from datajournals.authorization import requires_access
from datajournals.base_methods import convert_tagmodels_to_options, convert_options_to_tagmodels
from datajournals.models.restaurantdb import RestaurantRecord, RestaurantTag, RestaurantVisit, RestaurantNote
from datajournals.restaurantdb import bp
from datajournals.restaurantdb.forms import RestaurantForm, VisitForm, NoteForm, TagForm
from datajournals.restaurantdb.stats import visit_stats, get_restaurant_stats, get_ratings_stats, get_tag_stats, \
    get_note_stats, get_visit_stats, get_time_counts


def _get_name_options():
    _choices: list[tuple[str, str, [str, dict]]] = [(x.name, x.name, '') for x in RestaurantRecord.query.all()]
    _choices = sorted(_choices, key=lambda e: e[1])
    params = dict(selected=True)
    _choices.insert(0, ('', 'Choose a name', params))
    return _choices


@bp.route('/dashboard')
@bp.route('/index')
@bp.route('/')
@login_required
def index():
    r = get_restaurant_stats()
    rt = get_ratings_stats()
    t = get_tag_stats()
    n = get_note_stats()
    v = get_visit_stats()
    return render_template('restaurantdb/index.html',
                           restaurantstats=r,
                           ratingstats=rt,
                           tagstats=t,
                           notestats=n,
                           visitstats=v
                           )


@bp.route('/records')
@login_required
def records():
    page = request.args.get('page', 1, type=int)
    tid = request.args.get('tag', 0, int)
    tq = db.session.query(RestaurantTag).filter_by(id=tid).first()
    rq = db.session.query(RestaurantRecord).order_by(RestaurantRecord.name)
    if tq:
        rq = rq.filter(RestaurantRecord.tags.contains(tq))
    query = rq.paginate(page=page, per_page=10)
    return render_template('restaurantdb/records.html', paginator=query, tag=tq)


@bp.route('/records/<int:record_id>')
@login_required
def record(record_id):
    r = RestaurantRecord.query.filter_by(id=record_id).first()

    # Interfaces
    vs = SimpleNamespace()
    vsc = SimpleNamespace()
    setattr(vs, 'counts', vsc)
    ns = SimpleNamespace()
    nsc = SimpleNamespace()
    setattr(ns, 'counts', nsc)

    # Find stats and assign to interfaces
    # Visit stats
    vq = (db.session.query(RestaurantRecord.id.label('records'),
                           RestaurantVisit.id.label('visits'),
                           RestaurantVisit.date.label('dates')
                           )
          .join(RestaurantRecord.visits)
          .filter(RestaurantVisit.restaurant_id == record_id)
          )
    vdf = pd.read_sql(vq.statement, db.engine)
    lv = None
    if vdf.shape[0]:
        ldf = vdf.nlargest(1, 'dates', 'first').reset_index()
        lv = db.session.query(RestaurantVisit).filter_by(id=int(ldf.loc[0, 'visits'])).first()
    setattr(vs, 'latest', lv)
    vtc = get_time_counts(vdf)
    vtc['all'] = vdf
    for h, d in vtc.items():
        setattr(vsc, h, d.shape[0])

    # Note stats
    nq = (db.session.query(RestaurantRecord.id.label('records'),
                           RestaurantNote.id.label('notes'),
                           RestaurantNote.date_added.label('dates')
                           )
          .join(RestaurantRecord.notes)
          .filter(RestaurantRecord.id == record_id)
          )
    ndf = pd.read_sql(nq.statement, db.engine)
    ln = None
    if ndf.shape[0]:
        ldf = ndf.nlargest(1, 'dates', 'first').reset_index()
        ln = db.session.query(RestaurantNote).filter_by(id=int(ldf.loc[0, 'notes'])).first()
    setattr(ns, 'latest', ln)
    ntc = get_time_counts(ndf)
    ntc['all'] = ndf
    for h, d in ntc.items():
        setattr(nsc, h, d.shape[0])
    return render_template('restaurantdb/record.html',
                           record=r,
                           visitstats=vs,
                           notestats=ns
                           )


@bp.route('/tags')
@login_required
def tags():
    page = request.args.get('page', 1, type=int)
    query = RestaurantTag.query.order_by(RestaurantTag.tag.asc()).paginate(page=page, per_page=10)
    return render_template('restaurantdb/tags.html', paginator=query)


@bp.route('/tags/<int:tag_id>')
@login_required
def tag(tag_id):
    page = request.args.get('page', 1, type=int)
    tag_query = RestaurantTag.query.filter_by(id=tag_id).first()
    r_list = [x.id for x in tag_query.records]
    restaurant_query = RestaurantRecord.query \
        .filter(RestaurantRecord.id.in_(r_list)) \
        .order_by(RestaurantRecord.name.asc()) \
        .paginate(page=page, per_page=10)
    return render_template('restaurantdb/tag.html', paginator=restaurant_query, tag=tag_query)


@bp.route('/tags/edit/<int:tag_id>', methods=['GET', 'POST'])
@login_required
def edit_tag(tag_id):
    tq = db.session.query(RestaurantTag).filter_by(id=tag_id).first()
    f = TagForm()
    if f.validate_on_submit():
        ts = [x.tag for x in db.session.query(RestaurantTag).all()]
        if f.tag.data in ts:
            flash(f'Tag "{f.tag.data}" already exists', 'warning')
        else:
            tq.tag = f.tag.data
            db.session.add(tq)
            db.session.commit()
            return redirect(url_for('restaurantdb.tag', tag_id=tag_id))
    f.tag.data = tq.tag
    return render_template('restaurantdb/edit_tag.html', form=f, tag=tq)


@bp.route('/visits')
@login_required
def visits():
    page = request.args.get('page', 1, type=int)
    ri = request.args.get('restaurant', 0, int)
    rq = db.session.query(RestaurantRecord).filter_by(id=ri).first()
    nq = db.session.query(RestaurantVisit).order_by(RestaurantVisit.date.desc())
    if ri:
        nq = nq.filter(RestaurantVisit.record == rq)
    p = nq.paginate(page=page, per_page=10)
    return render_template('restaurantdb/visits.html', paginator=p, record=rq)


@bp.route('/visits/<int:visit_id>')
@login_required
def visit(visit_id):
    visit_ = RestaurantVisit.query.filter_by(id=visit_id).first()
    return render_template('restaurantdb/visit.html', visit=visit_)


@bp.route('/visits/records/<int:record_id>')
@login_required
def record_visits(record_id):
    record_ = RestaurantRecord.query.filter_by(id=record_id).first()
    page = request.args.get('page', 1, type=int)
    query = RestaurantVisit.query \
        .filter(RestaurantVisit.restaurant_id == record_id) \
        .order_by(RestaurantVisit.date.desc()) \
        .paginate(page=page, per_page=10)
    average = visit_stats(record_id)
    return render_template('restaurantdb/record_visits.html',
                           pagination=query,
                           record=record_,
                           average=average,
                           )


@bp.route('/notes')
@login_required
def notes():
    page = request.args.get('page', 1, type=int)
    ri = request.args.get('restaurant', 0, int)
    rq = db.session.query(RestaurantRecord).filter_by(id=ri).first()
    nq = db.session.query(RestaurantNote).order_by(RestaurantNote.date_added.desc())
    if ri:
        nq = nq.filter(RestaurantNote.record == rq)
    p = nq.paginate(page=page, per_page=10)
    return render_template('restaurantdb/notes.html', paginator=p, record=rq)


@bp.route('/notes/<int:note_id>')
@login_required
def note(note_id):
    note_ = RestaurantNote.query.filter_by(id=note_id).first()
    return render_template('restaurantdb/note.html', note=note_)


@bp.route('/notes/records/<int:record_id>')
@login_required
def record_notes(record_id):
    record_ = RestaurantRecord.query.filter_by(id=record_id).first()
    page = request.args.get('page', 1, type=int)
    query = RestaurantNote.query \
        .filter(RestaurantNote.restaurant_id == record_id) \
        .order_by(RestaurantNote.date_added.desc()) \
        .paginate(page=page, per_page=10)
    return render_template('restaurantdb/record_notes.html', pagination=query, record=record_)


@bp.route('/records/create', methods=('GET', 'POST'))
@login_required
@requires_access(['admin', 'editor'])
def create_record():
    form = RestaurantForm()

    if form.validate_on_submit():
        names = db.session.query(RestaurantRecord.name).all()

        # Check if restaurant name is already in database
        if (form.name.data,) not in names:
            r = RestaurantRecord()
            r.name = form.name.data
            r.date_added = datetime.utcnow()
            r.description = form.description.data
            r.avoid = form.avoid.data
            r.tags = convert_options_to_tagmodels(form.tags.data, RestaurantTag)
            db.session.add(r)
            db.session.commit()

            # Check if user wanted to add a visit; navigate to "add visit" if so
            if form.add_visit.data:
                return redirect(url_for('restaurantdb.create_visit', record_id=r.id))
            else:
                # Display new or updated restaurant page
                return redirect(url_for('restaurantdb.record', record_id=r.id))
        else:
            flash(f'"{form.name.data}" already exists in the database', 'warning')
    if form.tags.data is None:
        form.tags.data = []
    msg = 'Tags to describe this restaurant...'
    form.tags.choices = convert_tagmodels_to_options(RestaurantTag, message=msg)
    return render_template('restaurantdb/update_record.html', form=form)


@bp.route('/visits/create', methods=('GET', 'POST'))
@bp.route('/create_visit/<int:record_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin', 'editor'])
def create_visit(record_id=None):
    f = VisitForm()
    f.name.choices = _get_name_options()

    if f.validate_on_submit():
        r = RestaurantRecord.query.filter_by(name=f.name.data).first()

        # Get data from form and store in database
        v = RestaurantVisit()
        v.restaurant_id = r.id
        v.date = f.date.data
        v.meal = f.meal.data
        v.visit_rating = f.visit_rating.data
        v.price_rating = f.price_rating.data
        v.comments = f.comments.data

        db.session.add(v)
        db.session.commit()
        return redirect(url_for('restaurantdb.visit', visit_id=v.id))

    f.name.data = ''
    if record_id:
        f.name.data = RestaurantRecord.query.filter_by(id=record_id).first().name
    return render_template('restaurantdb/update_visit.html', form=f)


@bp.route('/notes/create', methods=('GET', 'POST'))
@bp.route('/notes/create/<int:record_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin', 'editor'])
def create_note(record_id=None):
    form = NoteForm()
    form.name.choices = _get_name_options()
    rq = None
    if record_id:
        rq = db.session.query(RestaurantRecord).filter_by(id=record_id).first()
    if form.validate_on_submit():

        # Get submitted restaurant name
        record_ = None
        if form.name.data:
            record_ = RestaurantRecord.query.filter_by(name=form.name.data).first()

        # Get data from form and store in database
        note_ = RestaurantNote()
        note_.restaurant_id = record_.id if record_ else None
        note_.date_added = note_.last_edited = datetime.utcnow()
        note_.note = form.note.data
        note_.important = form.important.data

        db.session.add(note_)
        db.session.commit()
        return redirect(url_for('restaurantdb.note', note_id=note_.id))

    form.name.data = ''
    if rq:
        form.name.data = rq.name
    return render_template('restaurantdb/create_note.html', form=form, record=rq)


@bp.route('records/edit/<int:record_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin', 'editor'])
def update_record(record_id):
    form = RestaurantForm()
    record_ = RestaurantRecord.query.filter_by(id=record_id).first()

    _exists = (form.name.data and
               (form.name.data,) in db.session.query(RestaurantRecord.name).all() and  # Exists in database
               form.name.data != record_.name  # Name was changed by user
               )
    if _exists:
        flash('Name already exists in database', 'warning')
    else:
        if form.validate_on_submit():
            record_.name = form.name.data
            record_.description = form.description.data
            record_.avoid = form.avoid.data
            record_.tags = convert_options_to_tagmodels(form.tags.data, RestaurantTag)

            db.session.add(record_)
            db.session.commit()
            return redirect(url_for('restaurantdb.record', record_id=record_id))

    form.name.data = record_.name
    form.description.data = record_.description
    msg = 'Tags to describe this restaurant...'
    form.tags.data = [x.tag for x in record_.tags]
    form.tags.choices = convert_tagmodels_to_options(RestaurantTag, message=msg)
    return render_template('restaurantdb/update_record.html',
                           form=form,
                           record=record_
                           )


@bp.route('/visits/edit/<int:visit_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin', 'editor'])
def update_visit(visit_id):
    visit_ = RestaurantVisit.query.filter_by(id=visit_id).first()
    form = VisitForm()
    form.name.choices = _get_name_options()

    if form.validate_on_submit():
        record_ = RestaurantRecord.query.filter_by(name=form.name.data).first()

        visit_.restaurant_id = record_.id
        visit_.date = form.date.data
        visit_.meal = form.meal.data
        visit_.visit_rating = form.visit_rating.data
        visit_.price_rating = form.price_rating.data
        visit_.comments = form.comments.data

        db.session.add(visit_)
        db.session.commit()

        return redirect(url_for('restaurantdb.visit', visit_id=visit_.id))

    form.name.data = visit_.record.name
    form.date.data = visit_.date
    form.meal.data = visit_.meal
    form.price_rating.data = visit_.price_rating
    form.visit_rating.data = visit_.visit_rating
    form.comments.data = visit_.comments
    return render_template('restaurantdb/update_visit.html', form=form, visit=visit_)


@bp.route('notes/edit/<int:note_id>', methods=('GET', 'POST'))
@login_required
@requires_access(['admin', 'editor'])
def update_note(note_id):
    # Load note
    note_ = RestaurantNote.query.filter_by(id=note_id).first()
    form = NoteForm()
    form.name.choices = _get_name_options()

    # Check submission
    if form.validate_on_submit():
        note_.note = form.note.data
        note_.important = form.important.data
        note_.last_edited = datetime.utcnow()
        db.session.add(note_)
        db.session.commit()
        return redirect(url_for('restaurantdb.note', note_id=note_.id))

    form.name.data = []
    if note_.record:
        form.name.data = note_.record.name
    form.note.data = note_.note
    form.important.data = note_.important
    return render_template('restaurantdb/update_note.html', form=form, note=note_)


@bp.route('delete_record/<int:record_id>', methods=('POST',))
@login_required
@requires_access(['admin', 'editor'])
def delete_record(record_id):
    record_ = RestaurantRecord.query.filter_by(id=record_id).first()
    db.session.delete(record_)
    db.session.commit()
    return redirect(url_for('restaurantdb.records', record_id=record_.id))


@bp.route('delete_visit/<int:visit_id>', methods=('POST',))
@login_required
@requires_access(['admin', 'editor'])
def delete_visit(visit_id):
    visit_ = RestaurantVisit.query.filter_by(id=visit_id).first()
    restaurant_ = RestaurantRecord.query.filter_by(id=visit_.restaurant_id).first()
    db.session.delete(visit_)
    db.session.commit()
    return redirect(url_for('restaurantdb.visits', restaurant=restaurant_.id))


@bp.route('delete_note/<int:note_id>', methods=('POST',))
@login_required
@requires_access(['admin', 'editor'])
def delete_note(note_id):
    note_ = RestaurantNote.query.filter_by(id=note_id).first()
    restaurant_ = RestaurantRecord.query.filter_by(id=note_.restaurant_id).first()
    db.session.delete(note_)
    db.session.commit()
    if restaurant_:
        return redirect(url_for('restaurantdb.restaurant_note', restaurant_id=restaurant_.id))
    return redirect(url_for('restaurantdb.notes'))
