import datetime
from types import SimpleNamespace

import pandas as pd

from datajournals import db
from datajournals.base_methods import timedelta_to_str
from datajournals.models import JournalRecord, JournalSubjectTag, JournalDescriptorTag, JournalEmotionTag


def get_records_stats(dataframe: pd.DataFrame = None):
    if dataframe is None:
        dq = db.session.query(JournalRecord.id.label('record'),
                              JournalRecord.record_date.label('date')
                              ).order_by(JournalRecord.record_date.desc())
        dataframe = pd.read_sql(dq.statement, db.engine)
    td = get_time_frames(dataframe)
    dd = {x: get_interval_description(y) for x, y in td.items()}

    s = SimpleNamespace()
    nd = {}
    for r in 'count', 'mean', 'std', 'med':
        n = []
        for c in 'week', 'month', 'halfyear', 'all':
            v = dd[c][r] if r in dd[c].index else None
            if r != 'count' and v is not None:
                v = timedelta_to_str(v)
            n.append(v)
        nd[r] = n
    setattr(s, 'timedata', nd)
    setattr(s, 'count', dataframe['date'].count())
    ln = None
    if td['all'].shape[0]:
        i = td['all'].reset_index().loc[0, 'record']
        ln = db.session.query(JournalRecord).filter_by(id=int(i)).first()
    setattr(s, 'latest', ln)
    return s


def get_unfinished_stats(dataframe: pd.DataFrame = None):
    if dataframe is None:
        dq = (db.session.query(JournalRecord.id.label('record'),
                               JournalRecord.record_date.label('date')
                               )
              .filter(JournalRecord.unfinished == 1)
              .order_by(JournalRecord.record_date.desc()))
        dataframe = pd.read_sql(dq.statement, db.engine)
    td = get_time_frames(dataframe)
    dd = {x: get_interval_description(y) for x, y in td.items()}

    s = SimpleNamespace()
    nd = {}
    for r in 'count', 'mean', 'std', 'med':
        n = []
        for c in 'week', 'month', 'halfyear', 'all':
            v = dd[c][r] if r in dd[c].index else None
            if r != 'count' and v is not None:
                v = timedelta_to_str(v)
            n.append(v)
        nd[r] = n
    setattr(s, 'timedata', nd)
    setattr(s, 'count', dataframe['date'].count())
    ln = None
    if td['all'].shape[0]:
        i = td['all'].reset_index().loc[0, 'record']
        ln = db.session.query(JournalRecord).filter_by(id=int(i)).first()
    setattr(s, 'latest', ln)
    return s


def get_watched_stats(dataframe: pd.DataFrame = None):
    if dataframe is None:
        dq = (db.session.query(JournalRecord.id.label('record'),
                               JournalRecord.record_date.label('date')
                               )
              .filter(JournalRecord.watched == 1)
              .order_by(JournalRecord.record_date.desc()))
        dataframe = pd.read_sql(dq.statement, db.engine)
    td = get_time_frames(dataframe)
    dd = {x: get_interval_description(y) for x, y in td.items()}

    s = SimpleNamespace()
    nd = {}
    for r in 'count', 'mean', 'std', 'med':
        n = []
        for c in 'week', 'month', 'halfyear', 'all':
            v = dd[c][r] if r in dd[c].index else None
            if r != 'count' and v is not None:
                v = timedelta_to_str(v)
            n.append(v)
        nd[r] = n
    setattr(s, 'timedata', nd)
    setattr(s, 'count', dataframe['date'].count())
    ln = None
    if td['all'].shape[0]:
        i = td['all'].reset_index().loc[0, 'record']
        ln = db.session.query(JournalRecord).filter_by(id=int(i)).first()
    setattr(s, 'latest', ln)
    return s


def get_tags_stats(dataframe: pd.DataFrame = None):
    if dataframe is None:
        nq = (db.session.query(JournalRecord.id.label('record'),
                               JournalRecord.record_date.label('date'),
                               JournalSubjectTag.id.label('subjects'),
                               JournalDescriptorTag.id.label('descriptors'),
                               JournalEmotionTag.id.label('emotions'),
                               )
              .join(JournalRecord.subjects)
              .join(JournalRecord.descriptors)
              .join(JournalRecord.emotions)
              )
        dataframe = pd.read_sql(nq.statement, db.engine)
    atd = {}
    atc = {}
    tc = {}
    for i, m in ('subjects', JournalSubjectTag), ('descriptors', JournalDescriptorTag), ('emotions', JournalEmotionTag):
        df = dataframe.drop_duplicates(['record', i])[['date', i]]
        td = get_time_frames(df)
        atd[i] = []
        for c in 'week', 'month', 'halfyear', 'all':
            cdf = td[c][i].value_counts()
            pdf = td[c][i].value_counts(normalize=True)
            mdf = pd.merge(cdf, pdf, left_index=True, right_index=True)
            ldf = mdf.nlargest(1, 'count', 'all')
            t = [db.session.query(m).filter_by(id=int(x)).first() for x in ldf.index]
            atd[i].append(t)
            if c == 'all':
                atc[i] = [(
                    db.session.query(m).filter_by(id=int(x)).first(),
                    mdf.loc[x, 'count'],
                    round(mdf.loc[x, 'proportion'], 3)
                ) for x in mdf.index]
                tc[i] = len(atc[i])

    s = SimpleNamespace()
    cn = SimpleNamespace()
    sn = SimpleNamespace()
    dn = SimpleNamespace()
    en = SimpleNamespace()
    setattr(s, 'timedata', atd)
    setattr(s, 'counts', cn)
    setattr(cn, 'all', sum(tc.values()))
    for ns, n in (sn, 'subjects'), (dn, 'descriptors'), (en, 'emotions'):  # 'tag' interfaces
        setattr(cn, n, tc[n])  # set 'counts' attributes
        setattr(s, n, ns)  # set 'tag' interface
        setattr(ns, 'all', atc[n])  # set 'all tags' attributes on 'tag' interface
        mcn = SimpleNamespace()
        setattr(ns, 'mostcommon', mcn)  # set 'most common' interface
        setattr(mcn, 'tags', atd[n][-1])  # set 'tags' attributes on 'most common' interface
    return s


def get_time_frames(dataframe: pd.DataFrame):
    """
    Sorts rows of dataframe with 'dates' column into bins of containing only the last week, last month, and last
    halfyear of rows. Appends the original dataframe to the final mapping.
    :param dataframe:
    :return:
    """

    def _date_to_datetime(date):
        return datetime.datetime.combine(date, datetime.datetime.min.time())

    if dataframe.shape[0] and type(dataframe.reset_index().loc[0, 'date']) is datetime.date:
        dataframe.loc[:, 'date'] = dataframe['date'].apply(_date_to_datetime)

    n = datetime.datetime.now()
    wi = n - datetime.timedelta(days=7)
    mi = n - datetime.timedelta(days=30)
    hi = n - datetime.timedelta(days=180)
    t = {}
    for i, d in ('week', wi), ('month', mi), ('halfyear', hi):
        t[i] = dataframe[dataframe['date'].between(d, n)]
    t['all'] = dataframe

    return t


def get_interval_description(dataframe: pd.DataFrame):
    """
    Gets data about the average interval between dates from a dataframe
    :param dataframe:
    :return:
    """
    dataframe = dataframe.sort_values(by='date', ascending=True)
    dataframe['diff'] = dataframe['date'].diff()
    d = dataframe['diff'].describe()
    d.rename(index={'25%': 'qtr1', '50%': 'med', '75%': 'qtr3'}, inplace=True)
    return d


def get_tag_stats(tag: JournalSubjectTag | JournalDescriptorTag | JournalEmotionTag, dataframe: pd.DataFrame = None):
    tm = type(tag)
    tt = {
        JournalSubjectTag: 'subject',
        JournalDescriptorTag: 'descriptor',
        JournalEmotionTag: 'emotion'
    }[tm]
    if dataframe is None:
        tq = (db.session.query(JournalRecord.id.label('record'),
                               JournalRecord.record_date.label('date'),
                               tm.id.label(tt),
                               )
              .join(getattr(JournalRecord, f'{tt}s'))
              )
        dataframe = pd.read_sql(tq.statement, db.engine)
    sdf = dataframe[dataframe[tt] == tag.id]  # tag-sorted dataframe
    tsdf = get_time_frames(sdf)  # time-sorted dataframe
    dtsd = {x: get_interval_description(y) for x, y in tsdf.items()}  # descriptive time-sorted dict
    tdd = {}  # time-data dict
    for r in 'count', 'mean', 'std', 'qtr1', 'med', 'qtr3':
        v = []
        for c in 'week', 'month', 'halfyear', 'all':
            if r != 'count' and r in dtsd[c].index:
                v.append(timedelta_to_str(dtsd[c][r]))
            elif r != 'count':
                v.append(None)
            else:
                v.append(tsdf[c].shape[0])
        tdd[r] = v

    s = SimpleNamespace()
    setattr(s, 'usecount', sdf.shape[0] or 0)
    setattr(s, 'timedata', tdd)
    for i in 'week', 'month', 'halfyear', 'all':
        sn = SimpleNamespace()
        setattr(s, i, sn)
        dd = get_interval_description(tsdf[i])
        for st in dd.index:
            if st == 'count':
                setattr(sn, st, dd[st])
            else:
                setattr(sn, st, timedelta_to_str(dd[st]))

    return s
