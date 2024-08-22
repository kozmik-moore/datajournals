import datetime
from math import ceil
from types import SimpleNamespace

import pandas as pd

from datajournals import db
from datajournals.models.restaurantdb import RestaurantNote, RestaurantVisit, RestaurantRecord, RestaurantTag


# TODO use numpy for these calculations
def visit_stats(restaurant_id):
    visits_ = RestaurantVisit.query.filter_by(restaurant_id=restaurant_id).all()
    num_visits = len(visits_)

    visits_rubric = {'Loved it!': 4,
                     'Liked it': 3,
                     'It was okay': 2,
                     'Did not like it': 1
                     }
    price_rubric = {'$$$$': 4,
                    '$$$': 3,
                    '$$': 2,
                    '$': 1
                    }

    visits_sum = 0
    price_sum = 0
    for visit in visits_:
        visits_sum += visits_rubric[visit.visit_rating]
        price_sum += price_rubric[visit.price_rating]
    visits_average = ceil(visits_sum / num_visits) if num_visits else 0
    price_average = ceil(price_sum / len(visits_)) if visits_ else 0
    return {4: 'Love it!',
            3: 'Like it',
            2: 'It\'s okay',
            1: 'Do not like it',
            0: 'No visits'}[visits_average], \
        {4: '$$$$',
         3: '$$$',
         2: '$$',
         1: '$',
         0: 'No visits'}[price_average], \
        num_visits


def note_stats(restaurant_id):
    notes_ = RestaurantNote.query \
        .filter_by(restaurant_id=restaurant_id) \
        .order_by(RestaurantNote.date_added.desc()).all()
    num_notes = len(notes_)
    num_most_recent = 5
    recent_notes = []
    i = 0
    while i < num_most_recent and notes_:
        recent_notes.append(notes_[i])
        i += 1
    return recent_notes, num_notes


def get_restaurant_stats(dataframe: pd.DataFrame = None):
    if dataframe is None:
        rq = (db.session.query(RestaurantRecord.id.label('restaurants'),
                               RestaurantVisit.id.label('visits'),
                               RestaurantVisit.date.label('dates')
                               )
              .join(RestaurantRecord.visits)
              )
        dataframe = pd.read_sql(rq.statement, db.engine)
    cdf = dataframe['restaurants'].value_counts().reset_index()
    pdf = dataframe['restaurants'].value_counts(normalize=True).reset_index()
    cp = pd.merge(cdf, pdf, on='restaurants')
    lcp = cp.nlargest(1, ['count'], 'all')
    a = [
        (
            db.session.query(RestaurantRecord).filter_by(id=int(cp.loc[x, 'restaurants'])).first(),
            cp.loc[x, 'count'],
            round(cp.loc[x, 'proportion'], 3)
        ) for x in cp.index
    ]
    a = sorted(a, key=lambda e: e[1], reverse=True)
    ts = [db.session.query(RestaurantRecord).filter_by(id=int(lcp.loc[x, 'restaurants'])).first() for x in lcp.index]
    c = 0
    p = 0.0
    if lcp.shape[0]:
        c = lcp.loc[0, 'count']
        p = round(lcp.loc[0, 'proportion'], 3)

    # Calculate timedata
    td = get_time_counts(dataframe)
    tdds = {}
    for i, df in td.items():
        cdf = df['restaurants'].value_counts().reset_index()
        pdf = df['restaurants'].value_counts(normalize=True).reset_index()
        cpdf = pd.merge(cdf, pdf, on='restaurants')
        lcp = cpdf.nlargest(1, 'count', 'all')
        tdt = [db.session.query(RestaurantRecord)
               .filter_by(id=int(lcp.loc[x, 'restaurants']))
               .first() for x in lcp.index]
        tdc = 0
        tdp = 0.0
        if cpdf.shape[0]:
            tdc = lcp.loc[0, 'count']
            tdp = round(lcp.loc[0, 'proportion'], 3)
        temp = {'tags': tdt, 'count': tdc, 'proportion': tdp}
        tdds[i] = temp
    tdds['all'] = {'tags': ts, 'count': c, 'proportion': p}

    # Create interfaces for data
    o = SimpleNamespace()
    mo = SimpleNamespace()
    to = SimpleNamespace()
    setattr(o, 'count', len(a))
    setattr(o, 'all', a)
    setattr(o, 'mostcommon', mo)
    setattr(o, 'timedata', to)
    setattr(mo, 'tags', ts)
    setattr(mo, 'count', c)
    setattr(mo, 'proportion', p)
    for i, ds in tdds.items():
        sto = SimpleNamespace()
        setattr(to, i, sto)
        for s, v in ds.items():
            setattr(sto, s, v)

    return o


def get_ratings_stats(dataframe: pd.DataFrame = None):
    sm = {
        'Loved it!': 3,
        'Liked it': 2,
        'It was okay': 1,
        'Did not like it': 0
    }

    def _integerize_satisfaction(v):
        return sm[v]

    def _integerize_price(v):
        return len(v) - 1

    if dataframe is None:
        rq = db.session.query(RestaurantVisit.id.label('visits'),
                              RestaurantVisit.price_rating.label('price'),
                              RestaurantVisit.visit_rating.label('satisfaction'),
                              RestaurantVisit.date.label('dates')
                              )
        dataframe = pd.read_sql(rq.statement, db.engine)
    dataframe['price_int'] = dataframe['price'].apply(_integerize_price)
    dataframe['satisfaction_int'] = dataframe['satisfaction'].apply(_integerize_satisfaction)
    pde = dataframe['price_int'].describe()
    sde = dataframe['satisfaction_int'].describe()
    td = get_time_counts(dataframe)
    td['all'] = dataframe
    ptdd = {}
    stdd = {}
    for i, df in td.items():
        ptdd[i] = df['price_int'].describe()
        stdd[i] = df['satisfaction_int'].describe()

    # Create interface
    n = SimpleNamespace()
    for ds, dn in (pde, 'price'), (sde, 'satisfaction'):
        sn = SimpleNamespace()
        setattr(n, dn, sn)
        for i in ['count', 'mean', 'std', 'min', 'max']:
            setattr(sn, i, round(ds[i], 3) if i != 'count' else int(ds[i]))
        for i, sub in ('25%', 'qtr1'), ('50%', 'med'), ('75%', 'qtr3'):
            setattr(sn, sub, round(ds[i], 3))
    sn = SimpleNamespace()
    setattr(n, 'timedata', sn)
    for ds, dn in (ptdd, 'price'), (stdd, 'satisfaction'):
        tn = SimpleNamespace()
        setattr(sn, dn, tn)
        for i, d in ds.items():
            qn = SimpleNamespace()
            setattr(tn, i, qn)
            for si in ['count', 'mean', 'std', 'min', 'max']:
                setattr(qn, si, round(d[si], 3) if si != 'count' else int(d[si]))
            for si, sub in ('25%', 'qtr1'), ('50%', 'med'), ('75%', 'qtr3'):
                setattr(qn, sub, round(d[si], 3))

    return n


def get_tag_stats(dataframe: pd.DataFrame = None):
    if dataframe is None:
        tq = (db.session.query(RestaurantRecord.id.label('restaurants'), RestaurantTag.id.label('tags'))
              .join(RestaurantRecord.tags))
        dataframe = pd.read_sql(tq.statement, db.engine)
    cdf = dataframe['tags'].value_counts().reset_index()
    pdf = dataframe['tags'].value_counts(normalize=True).reset_index()
    cp = pd.merge(cdf, pdf, on='tags')
    lcp = cp.nlargest(1, 'count', 'all').reset_index()
    t = [db.session.query(RestaurantTag).filter_by(id=int(x)).first() for x in lcp['tags']]
    a = [(
        db.session.query(RestaurantTag).filter_by(id=int(cp.loc[x, 'tags'])).first(),
        cp.loc[x, 'count'],
        round(cp.loc[x, 'proportion'], 3)
    ) for x in cp.index]
    c = 0
    p = 0.0
    if lcp.shape[0]:
        c = lcp.loc[0, 'count']
        p = round(lcp.loc[0, 'proportion'], 3)

    # Interface
    n = SimpleNamespace()
    sn = SimpleNamespace()
    setattr(n, 'mostcommon', sn)
    setattr(n, 'all', a)
    setattr(n, 'count', len(pd.unique(dataframe['tags'])))
    setattr(sn, 'tags', t)
    setattr(sn, 'count', c)
    setattr(sn, 'proportion', p)

    return n


def get_note_stats(dataframe: pd.DataFrame = None):
    if dataframe is None:
        nq = db.session.query(RestaurantNote.id.label('notes'), RestaurantNote.date_added.label('dates'))
        dataframe = pd.read_sql(nq.statement, db.engine)
    ldf = dataframe.nlargest(1, 'dates').reset_index(drop=True)
    ln = None
    if ldf.shape[0]:
        ln = db.session.query(RestaurantNote).filter_by(id=int((ldf.loc[0, 'notes']))).first()

    # Interface
    n = SimpleNamespace()
    setattr(n, 'count', dataframe.shape[0])
    setattr(n, 'latest', ln)

    return n


def get_visit_stats(dataframe: pd.DataFrame = None):
    if dataframe is None:
        vq = db.session.query(RestaurantVisit.id.label('visits'),
                              RestaurantVisit.restaurant_id.label('restaurants'),
                              RestaurantVisit.date.label('dates')
                              )
        dataframe = pd.read_sql(vq.statement, db.engine)
    dataframe['weekday'] = dataframe['dates'].dt.dayofweek
    c = dataframe['weekday'].value_counts().reset_index()
    p = dataframe['weekday'].value_counts(normalize=True).reset_index()
    cp = pd.merge(c, p, on='weekday').set_index('weekday')
    dm = {
        0: 'monday',
        1: 'tuesday',
        2: 'wednesday',
        3: 'thursday',
        4: 'friday',
        5: 'saturday',
        6: 'sunday',
    }
    a = []
    for i, w in dm.items():
        try:
            t = (w, cp.loc[i, 'count'], round(cp.loc[i, 'proportion'], 3))
        except KeyError:
            t = (w, 0, 0.0)
        a.append(t)
    a = sorted(a, key=lambda e: e[1], reverse=True)
    lcp = cp.nlargest(1, 'count', 'all')
    ds = [dm[x] for x in lcp.index]
    lc = 0
    lp = 0.0
    if lcp.shape[0]:
        lc = lcp.reset_index().loc[0, 'count']
        lp = round(lcp.reset_index().loc[0, 'proportion'], 3)
    ldf = dataframe.nlargest(1, 'dates').set_index('visits')
    ld = db.session.query(RestaurantVisit).filter_by(id=int(ldf.index[0])).first()
    td = get_time_counts(dataframe)
    tdds = {}
    for i, d in td.items():
        tcdf = d['weekday'].value_counts().reset_index()
        tpdf = d['weekday'].value_counts(normalize=True).reset_index()
        tcp = pd.merge(tcdf, tpdf, on='weekday').set_index('weekday')
        ltcp = tcp.nlargest(1, 'count', 'all')
        tc = 0
        tp = 0.0
        if ltcp.shape[0]:
            tc = ltcp.reset_index().loc[0, 'count']
            tp = round(ltcp.reset_index().loc[0, 'proportion'], 3)
        tdds[i] = {'days': [dm[x] for x in ltcp.index], 'count': tc, 'proportion': tp}
    tdds['all'] = {'days': ds, 'count': lc, 'proportion': lp}

    # Create interface
    s = SimpleNamespace()
    sn = SimpleNamespace()
    tn = SimpleNamespace()
    setattr(s, 'mostcommon', sn)
    setattr(s, 'all', a)
    setattr(s, 'latest', ld)
    setattr(s, 'timedata', tn)
    setattr(sn, 'days', ds)
    setattr(sn, 'count', lc)
    setattr(sn, 'proportion', lp)
    for i, d in tdds.items():
        qn = SimpleNamespace()
        setattr(tn, i, qn)
        for k, v in d.items():
            setattr(qn, k, v)

    return s


def get_time_counts(dataframe: pd.DataFrame):
    cd = datetime.datetime.now()
    wtd = cd - datetime.timedelta(days=7)
    mtd = cd - datetime.timedelta(days=30)
    htd = cd - datetime.timedelta(days=180)
    w = dataframe[dataframe['dates'].between(wtd, cd)]
    m = dataframe[dataframe['dates'].between(mtd, cd)]
    h = dataframe[dataframe['dates'].between(htd, cd)]

    return {'week': w, 'month': m, 'halfyear': h}


def get_most_common(dataframe: pd.DataFrame, column: str, count=1, keep='all'):
    c = 0
    p = 0.0
    cdf = dataframe[column].value_counts().reset_index()
    pdf = dataframe[column].value_counts(normalize=True).reset_index()
    mdf = pd.merge(cdf, pdf, on=column)
    ldf = mdf.nlargest(count, 'count', keep=keep)
    if ldf.shape[0]:
        c = ldf.reset_index().loc[0, 'count']
        p = round(ldf.reset_index().loc[0, 'proportion'], 3)
    i = [x for x in ldf.index]

    s = SimpleNamespace()
    setattr(s, 'items', i)
    setattr(s, 'count', c)
    setattr(s, 'proportion', p)

    return s


def get_all_counts(dataframe: pd.DataFrame, column: str):
    c = dataframe[column].value_counts().reset_index()
    p = dataframe[column].value_counts(normalize=True).reset_index()
    mcp = pd.merge(c, p, on=column)
    a = [[
        x,
        mcp.loc[x, 'count'],
        round(mcp.loc[x, 'proportion'], 3)
    ] for x in mcp.index]

    return a
