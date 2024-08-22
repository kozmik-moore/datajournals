import base64
import datetime as dt
import io

import pandas as pd
import seaborn as sns

from datajournals import db
from datajournals.models import SleepRecord, SleepInterruptionAssociation, SleepEmotionTag, SleepSensationTag, \
    SleepLocationTag, SleepInterruptionTag, SleepNote


def to_minutes(td: pd.Timedelta):
    return td.seconds // 60


def to_hours(td: pd.Timedelta):
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) / 3600
    return round(hours + minutes, 3)


def timedelta_to_str(td: pd.Timedelta):
    if type(td) is dt.timedelta:
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


class _StatsObject(object):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name


class SleepDurationStats:

    def __init__(self, sleepobjects: list = None, createcharts: bool = True):
        desc = {
            'all': 'all sleep durations',
            'reg': 'greater than 4 hours sleep duration',
            'nap': 'between 30 minutes and 4 hours sleep duration',
            'pnap': 'less than 30 minutes sleep duration'
        }
        long_name = {
            'all': 'All sleep',
            'reg': 'Regular sleep',
            'nap': 'Naps',
            'pnap': 'Power naps',
        }
        if sleepobjects is None:
            sleepobjects = ['all', 'reg', 'nap', 'pnap']
        else:
            tmp = []
            if {'reg', 'regular'}.intersection(sleepobjects):
                tmp.append('reg')
            if {'all', 'overall'}.intersection(sleepobjects):
                tmp.append('all')
            if {'nap'}.intersection(sleepobjects):
                tmp.append('nap')
            if {'pnap', 'powernap', 'power nap', 'power_nap'}.intersection(sleepobjects):
                tmp.append('pnap')
            sleepobjects = tmp
        self._regular_object = _StatsObject('reg') if 'reg' in sleepobjects else None
        self._nap_object = _StatsObject('nap') if 'nap' in sleepobjects else None
        self._pnap_object = _StatsObject('pnap') if 'pnap' in sleepobjects else None
        self._overall_object = _StatsObject('all') if 'all' in sleepobjects else None

        eq = db.session.query(SleepRecord.id.label('record'),
                              SleepRecord.time_retire.label('retire'),
                              SleepRecord.time_start_sleep.label('sleep'),
                              SleepRecord.time_stop_sleep.label('wake'),
                              SleepRecord.time_rise.label('rise'),
                              SleepInterruptionAssociation.tag_id.label('interruption'),
                              SleepInterruptionAssociation.duration.label('duration')
                              ).outerjoin(SleepRecord.interruptions)
        df = pd.read_sql(str(eq), db.engine, dtype={'retire': 'datetime64[ns]',
                                                    'sleep': 'datetime64[ns]',
                                                    'wake': 'datetime64[ns]',
                                                    'rise': 'datetime64[ns]',
                                                    'duration': 'timedelta64[m]',
                                                    }
                         )
        dfd = df.drop_duplicates(['record', 'retire'])[['record', 'retire', 'sleep', 'wake', 'rise']]
        dfi = df.groupby(['record'])['duration'].sum()
        dfi.rename('interruptions', inplace=True)
        dfd_merged: pd.DataFrame = dfd.merge(dfi, on='record')
        dfd_merged['in_bed'] = dfd_merged['rise'] - dfd_merged['retire']
        dfd_merged['asleep'] = dfd_merged['wake'] - dfd_merged['sleep']
        dfd_merged['asleep_adjusted'] = dfd_merged['asleep'] - dfd_merged['interruptions']
        dfd_merged['awake'] = dfd_merged['in_bed'] - dfd_merged['asleep_adjusted']
        stats = ['in_bed', 'asleep', 'interruptions', 'asleep_adjusted', 'awake']
        fr = 'asleep_adjusted'
        f = {
            'all': dfd_merged[fr] != 'NaN',
            'reg': dfd_merged[fr] > dt.timedelta(hours=4),
            'nap': dfd_merged[fr].between(dt.timedelta(minutes=30), dt.timedelta(hours=4)),
            'pnap': dfd_merged[fr] < dt.timedelta(minutes=30)
        }
        for o in [self._regular_object, self._nap_object, self._pnap_object, self._overall_object]:
            if o is not None:
                setattr(o, 'description', desc[o.name])
                setattr(o, 'long_name', long_name[o.name])
                for s in stats:
                    so = _StatsObject(s)
                    data: pd.Series = dfd_merged[f[o.name]][s]
                    desc_stats = data.describe()

                    if createcharts:
                        def _get_boxplot_fig(d: pd.Series):
                            a = sns.boxplot(x=d)
                            return a

                        for pltype, pltfunc in {
                            'hist': sns.histplot,
                            'boxplot': _get_boxplot_fig
                        }.items():
                            img = io.BytesIO()
                            ax = pltfunc(data.apply(to_hours))
                            ax.set(xlabel='Duration (hours)')
                            fig = ax.get_figure()
                            fig.savefig(img, format='jpg')
                            fig.clf()
                            img.seek(0)
                            url = base64.b64encode(img.getvalue()).decode()
                            setattr(so, pltype, url)
                    setattr(so, 'data', data)
                    setattr(so, 'description', desc_stats)
                    for p, i in {'mean': 1,
                                 'std': 2,
                                 'med': 5,
                                 'qtr1': 4,
                                 'qtr3': 6,
                                 'min': 3,
                                 'max': 7,
                                 'count': 0
                                 }.items():
                        if p in ['mean', 'std', 'min', 'max', ]:
                            setattr(so, p, timedelta_to_str(desc_stats[i]))
                        elif p == 'med':
                            setattr(so, p, timedelta_to_str(desc_stats[i]))
                        elif p == 'qtr1':
                            setattr(so, p, timedelta_to_str(desc_stats[i]))
                        elif p == 'qtr3':
                            setattr(so, p, timedelta_to_str(desc_stats[i]))
                        elif p == 'count':
                            setattr(so, p, desc_stats[i])
                    setattr(o, so.name, so)

    @property
    def regular(self):
        return self._regular_object

    @property
    def nap(self):
        return self._nap_object

    @property
    def powernap(self):
        return self._pnap_object

    @property
    def overall(self):
        return self._overall_object


def get_duration_data(with_tags=False):
    """

    :rtype: pd.DataFrame
    """
    if with_tags:
        rq = (db.session.query(SleepRecord.id.label('record_id'),
                               SleepRecord.time_retire.label('retire'),
                               SleepRecord.time_start_sleep.label('sleep'),
                               SleepRecord.time_stop_sleep.label('wake'),
                               SleepRecord.time_rise.label('rise'),
                               SleepEmotionTag.id.label('emotions'),
                               SleepSensationTag.id.label('sensations'),
                               SleepLocationTag.id.label('locations'),
                               SleepInterruptionTag.id.label('interruptions'),
                               SleepInterruptionAssociation.id.label('interruption_id'),
                               SleepInterruptionAssociation.duration.label('interruption_duration'),
                               )
              .outerjoin(SleepRecord.interruptions)
              .outerjoin(SleepRecord.emotions)
              .outerjoin(SleepRecord.sensations)
              .outerjoin(SleepRecord.locations)
              .outerjoin(SleepInterruptionAssociation.tags)
              )
    else:
        rq = db.session.query(SleepRecord.id.label('record_id'),
                              SleepRecord.time_retire.label('retire'),
                              SleepRecord.time_start_sleep.label('sleep'),
                              SleepRecord.time_stop_sleep.label('wake'),
                              SleepRecord.time_rise.label('rise'),
                              SleepInterruptionAssociation.id.label('interruption_id'),
                              SleepInterruptionAssociation.duration.label('interruption_duration'),
                              ).outerjoin(SleepRecord.interruptions)
    df = pd.read_sql(str(rq), db.engine, dtype={'retire': 'datetime64[s]',
                                                'sleep': 'datetime64[s]',
                                                'wake': 'datetime64[s]',
                                                'rise': 'datetime64[s]',
                                                }
                     )
    df['interruption_duration'] = pd.to_timedelta(df['interruption_duration'], unit='m')
    df['in_bed'] = df['rise'] - df['retire']
    df['asleep'] = df['wake'] - df['sleep']
    df['asleep_adjusted'] = df['asleep'] - df['interruption_duration']
    df['awake'] = df['in_bed'] - df['asleep_adjusted']
    return df


def filter_duration_data(f: list[str] = None,
                         lower: float = 0.5,
                         upper: float = 4,
                         metric='asleep',
                         data: pd.DataFrame = None,
                         tag: tuple[int, str] = None,
                         with_tags=False,
                         dates: tuple[dt.datetime, dt.datetime] = None
                         ):
    if f is None:
        f = ['reg', 'nap', 'pnap', 'all']
    if tag:
        with_tags = True
    if data is None:
        data = get_duration_data(with_tags=with_tags)
    if data.shape[0] > 0:
        if tag:
            t, tt = tag
            try:
                data = data.copy().loc[data[tt] == t]  # TODO find if there is a better way to do this
            except KeyError:
                pass
        if dates:
            start, stop = dates
            data = data.copy().loc[data['retire'].between(start, stop)]
    fr = metric
    filters = {
        'reg': data[fr] > dt.timedelta(hours=upper),
        'nap': data[fr].between(dt.timedelta(hours=lower), dt.timedelta(hours=upper), inclusive='left'),
        'pnap': data[fr] < dt.timedelta(hours=lower)
    }
    if data.shape[0] > 0:
        data.loc[filters['reg'], 'sleeptype'] = 'reg'
        data.loc[filters['nap'], 'sleeptype'] = 'nap'
        data.loc[filters['pnap'], 'sleeptype'] = 'pnap'
    if len(f) == 1 and 'all' in f:
        return data
    elif len(f) == 1:
        return data[filters[f[0]]]
    elif 'all' in f:
        s = {'all': data}
        f.remove('all')
    else:
        s = {}
    for slt in f:
        s[slt] = data[filters[slt]]
    return s


def get_duration_stats(data: pd.DataFrame = None, name: str = None, metric='asleep'):
    if data is None:
        data = filter_duration_data(['all'], metric=metric)
    data = data.drop_duplicates(['record_id', 'interruption_id'])
    i = data.groupby(['record_id'])['interruption_duration'].sum()
    data = data.drop_duplicates(['record_id', 'retire']).set_index('record_id')
    data.loc[:, 'interruption_duration'] = i
    s = _StatsObject('durationstats' if not name else name)
    for stt in ['in_bed', 'asleep', 'interruption_duration', 'asleep_adjusted', 'awake']:
        so = _StatsObject(stt)
        setattr(s, stt, so)
        description = data[stt].describe()
        description.rename({'25%': 'qtr1', '50%': 'med', '75%': 'qtr3'}, inplace=True)
        for p in description.index:
            if p == 'count':
                setattr(so, p, description[p])
            else:
                setattr(so, p, timedelta_to_str(description[p]))
        setattr(so, 'sum', timedelta_to_str(data[stt].sum()))
    return s


def get_tag_stats(tagid: int, tagtype: str, data: pd.DataFrame = None, metric='asleep'):
    tms = {
        'emotions': SleepEmotionTag,
        'sensations': SleepSensationTag,
        'locations': SleepLocationTag,
        'interruptions': SleepInterruptionTag
    }
    if data is None:
        data = filter_duration_data(['all'], metric=metric)
    s = _StatsObject('tagstats')  # create stats object
    setattr(s, 'tag_id', tagid)
    setattr(s, 'type', tagtype)
    tm = tms[tagtype]
    r = data.reset_index()['record_id']
    rmo = SleepRecord.id
    rma = getattr(tm, 'records')
    if tagtype == 'interruptions':
        rmo = SleepInterruptionAssociation.record_id
        rma = SleepInterruptionTag.interruptions
    tq = (db.session.query(rmo.label('records'))
          .join(rma)
          .filter(rmo.in_(r))
          .filter(tm.id == tagid))
    for ak, am in tms.items():  # Create associated tags objects
        aso = _StatsObject(ak)
        setattr(s, ak, aso)
        mo = _StatsObject('mostcommon')
        setattr(aso, 'mostcommon', mo)
        lo = _StatsObject('leastcommon')
        setattr(aso, 'leastcommon', lo)
        rmi = SleepRecord.id
        if ak == 'interruptions':
            rmi = SleepInterruptionAssociation.record_id
        atq = (db.session.query(am.id.label(ak), am.tag.label('name'), rmi.label('records'))
               .join(am.records)
               .filter(rmi.in_([x[0] for x in tq.all()]))
               ).filter(am.id != tagid)
        df = pd.read_sql(atq.statement, db.engine)
        atc = df[ak].value_counts()
        atp = df[ak].value_counts(normalize=True)
        ats = pd.merge(atc, atp, on=ak).reset_index()
        mct = []
        lct = []
        mcc = lcc = mcp = lcp = None
        if atc.shape[0]:
            # most common tags
            mc = ats.nlargest(1, keep='all', columns=['count'])
            mct = [db.session.query(am).filter_by(id=x).first() for x in mc[ak]]
            mcc = mc['count'][0]
            mcp = round(mc['proportion'][0], 3)
            # least common tags
            lc = ats.nsmallest(1, keep='all', columns=['count'])
            lct = [db.session.query(am).filter_by(id=x).first() for x in lc[ak]]
            lcc = lc.reset_index()['count'][0]
            lcp = round(lc.reset_index()['proportion'][0], 3)
        setattr(aso, 'records', df['records'])
        setattr(aso, 'data', ats)
        setattr(mo, 'tags', mct)
        setattr(mo, 'percent', mcp)
        setattr(mo, 'count', mcc)
        setattr(lo, 'tags', lct)
        setattr(lo, 'percent', lcp)
        setattr(lo, 'count', lcc)
    return s


def get_tag_stats_v2(tagid: int, tagtype: str, data: pd.DataFrame = None, metric='asleep'):
    tms = {
        'emotions': SleepEmotionTag,
        'sensations': SleepSensationTag,
        'locations': SleepLocationTag,
        'interruptions': SleepInterruptionTag
    }
    tm = tms[tagtype]
    tobj = db.session.query(tm).filter_by(id=tagid).first()
    if data is None:
        data = filter_duration_data(['all'], metric=metric)
    s = _StatsObject(f'tagstats-{tobj.tag}')  # create stats object
    setattr(s, 'tag_id', tagid)
    setattr(s, 'type', tagtype)
    ti = ['record_id', 'interruption_id', 'interruptions'] if tagtype == 'interruptions' else ['record_id', tagtype]
    d: pd.DataFrame = data.drop_duplicates(ti)
    tc = d[tagtype].value_counts()[tagid]
    setattr(s, 'count', tc)
    tp = d[tagtype].value_counts(normalize=True)[tagid]
    setattr(s, 'proportion', round(tp, 3))
    rs = list(d['record_id'].apply(int))
    setattr(s, 'record_ids', rs)
    return s


def get_all_tags_stats(data: pd.DataFrame = None):
    if data is None:
        data = get_duration_data(with_tags=True)
    s = _StatsObject('tags_stats')
    for tt, tm in {
        'emotions': SleepEmotionTag,
        'sensations': SleepSensationTag,
        'locations': SleepLocationTag,
        'interruptions': SleepInterruptionTag
    }.items():
        tobj = _StatsObject(tt)
        setattr(s, tt, tobj)
        mco = _StatsObject('mostcommon')
        setattr(tobj, 'mostcommon', mco)
        lco = _StatsObject('leastcommon')
        setattr(tobj, 'leastcommon', lco)
        if tt in ['emotions', 'sensations', 'locations']:
            ud = data.drop_duplicates(['record_id', tt])
        else:
            ud = data.drop_duplicates(['record_id', 'interruption_id'])
        c = ud[tt].value_counts()
        p = ud[tt].value_counts(normalize=True)
        m = pd.merge(c, p, on=tt).reset_index()
        mc = m.nlargest(1, keep='all', columns='count')
        lc = m.nsmallest(1, keep='all', columns='count')
        setattr(mco, 'tags', db.session.query(tm).filter(tm.id.in_(mc[tt])).all())
        setattr(mco, 'count', int(mc['count'].mean()) if not mc['count'].empty else '')
        setattr(mco, 'percent', round(mc['proportion'].mean(), 3) if not mc['proportion'].empty else '')
        setattr(lco, 'tags', db.session.query(tm).filter(tm.id.in_(lc[tt])).all())
        setattr(lco, 'count', int(lc['count'].mean()) if not lc['count'].empty else '')
        setattr(lco, 'percent', round(lc['proportion'].mean(), 3) if not lc['proportion'].empty else '')
        at = [db.session.query(tm).filter_by(id=x).first() for x in c.index]
        ato = _StatsObject('all_tags')
        setattr(tobj, 'all_tags', ato)
        setattr(ato, 'tags', at)
        setattr(ato, 'count', len(at))
        setattr(ato, 'percent', 1.0)
    return s


def get_day_stats(data: pd.DataFrame = None, metric='asleep'):
    if data is None:
        data = filter_duration_data(['all'], metric=metric)
    data = data.drop_duplicates(['record_id', 'retire'])

    s = _StatsObject('daystats')
    try:
        du = data.nsmallest(n=1, columns='retire')['record_id'].iloc[0]  # first day in frame
        setattr(s, 'first', db.session.query(SleepRecord).filter_by(id=int(du)).first())
        du = data.nlargest(n=1, columns='retire')['record_id'].iloc[0] # last day in frame
        setattr(s, 'last', db.session.query(SleepRecord).filter_by(id=int(du)).first())
    except IndexError:
        setattr(s, 'first', None)
        setattr(s, 'last', None)

    o = _StatsObject('shortest')  # shortest duration by metric in frame
    setattr(s, o.name, o)
    du = data.nsmallest(n=1, keep='all', columns=metric)
    t = [db.session.query(SleepRecord).filter_by(id=int(x)).first() for x in du['record_id']]
    setattr(o, 'records', t)
    d = timedelta_to_str(du[metric].mean())
    setattr(o, 'duration', d)

    o = _StatsObject('longest')  # longest duration by metric in frame
    setattr(s, o.name, o)
    du = data.nlargest(n=1, keep='all', columns=metric)
    t = [db.session.query(SleepRecord).filter_by(id=int(x)).first() for x in du['record_id']]
    setattr(o, 'records', t)
    d = timedelta_to_str(du[metric].mean())
    setattr(o, 'duration', d)

    return s


def get_index_stats():
    s = _StatsObject('stats')
    d = get_duration_data(True)
    fd = filter_duration_data(data=d)
    do = _StatsObject('durationstats')
    setattr(s, do.name, do)
    for slt, sld in fd.items():
        setattr(do, 'data', sld)
        o = get_duration_stats(data=sld, name=slt)
        setattr(do, o.name, o)
        setattr(o, 'daystats', get_day_stats(sld))
    setattr(s, 'tagstats', get_all_tags_stats(d))
    rc = db.session.query(SleepRecord).count()
    setattr(s, 'recordscount', rc)
    nc = db.session.query(SleepNote).count()
    setattr(s, 'notescount', nc)
    return s


def get_plots(data: pd.DataFrame = None, metric='asleep', stats: list[str] = None):
    if data is None:
        data = filter_duration_data(['all'], metric=metric, with_tags=True)
    if stats is None:
        stats = ['in_bed', 'asleep', 'interruption_duration', 'asleep_adjusted', 'awake']

    def _get_boxplot_fig(d: pd.Series):
        a = sns.boxplot(x=d)
        return a

    s = _StatsObject('plots')
    for sc in stats:
        so = _StatsObject(sc)
        setattr(s, so.name, so)
        tdf = data[sc]
        for pltype, pltfunc in [
            ('hist', sns.histplot),
            ('boxplot', _get_boxplot_fig),
        ]:
            img = io.BytesIO()
            ax = pltfunc(tdf.apply(to_hours))
            ax.set(xlabel='Duration (hours)')
            fig = ax.get_figure()
            fig.savefig(img, format='jpg')
            fig.clf()
            img.seek(0)
            url = base64.b64encode(img.getvalue()).decode()
            setattr(so, pltype, url)

    return s
