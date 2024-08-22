from datetime import datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pandas as pd
from flask import render_template, redirect, url_for
from sqlalchemy import func
from sqlalchemy.orm import Query

from datajournals import db
from datajournals.base_methods import timedelta_to_str
from datajournals.models import Game, GamingSessionInterruption, GamingSessionRecord, GamingNote, GamingEmotionTag, \
    GamingInterruptionTag


def datetimes_to_string_spans(dt1: datetime, dt2: datetime, datefmt='%A, %B %d, %Y', timefmt='%H:%M'):
    """
    Takes two datetimes and returns a dict of strings representing their time span.
    Considers all parts of the date down to and including the minute
    :param dt1: the first datetime
    :param dt2: the second datetime
    :param datefmt: the format for the date strings
    :param timefmt: the format for the time strings
    :return: a dict of strings representing the span of dates and the span of times
    """
    if not all([
        dt1.date() == dt2.date(),
        dt1.hour == dt2.hour,
        dt1.minute == dt2.minute
    ]):
        first = min(dt1, dt2)
        second = max(dt1, dt2)
        if dt1.date() == dt2.date():
            datespan = dt1.strftime(datefmt)
        else:
            datespan = f'{first.strftime(datefmt)} - {second.strftime(datefmt)}'
        timespan = f'{first.strftime(timefmt)} - {second.strftime(timefmt)}'
    else:
        datespan = f'{dt1.strftime(datefmt)} -'
        timespan = f'{dt1.strftime(timefmt)} -'
    return {'date_str': datespan, 'time_str': timespan}


def seconds_to_hrs_mins(seconds: timedelta.seconds):
    hours = int(seconds // 3600)
    minutes = int(seconds // 60) % 60
    return hours, minutes


def hrs_mins_to_string(dur: tuple[int, int], sep=', ', zero_minutes=False, zero_hours=False):
    hours = dur[0]
    minutes = dur[1]
    hours_desc = ' hour' if hours == 1 else ' hours' if hours or zero_hours else ''
    minutes_desc = ' minute' if minutes == 1 else ' minutes' if minutes or zero_minutes else ''
    hours_str = f'{hours if hours or zero_hours else ""}{hours_desc}'
    minutes_str = f'{minutes if minutes or zero_minutes else ""}{minutes_desc}'
    return f'{hours_str}{sep if hours_str and minutes_str else ""}{minutes_str}'


def _filter_float(value):
    return int(value) if value == int(value) else value


class RecordsQueryStats:

    def __init__(self, records_query: Query, precision=3):
        class _DurationStat:
            def __init__(self, durations: np.array):
                self._durations = durations

            @property
            def mean(self):
                if self._durations.size:
                    return hrs_mins_to_string(seconds_to_hrs_mins(np.mean(self._durations)), )
                else:
                    return ''

            @property
            def stdev(self):
                if self._durations.size:
                    # TODO return '0' when 0 instead of ''
                    return hrs_mins_to_string(seconds_to_hrs_mins(np.std(self._durations)))
                else:
                    return ''

            @property
            def median(self):
                if self._durations.size:
                    return hrs_mins_to_string(seconds_to_hrs_mins(np.median(self._durations)))
                else:
                    return ''

            @property
            def iqr(self):
                if self._durations.size:
                    first = np.quantile(self._durations, 0.25)
                    third = np.quantile(self._durations, 0.75)
                    return (f'(({hrs_mins_to_string(seconds_to_hrs_mins(first))}), '
                            f'({hrs_mins_to_string(seconds_to_hrs_mins(third))}))')
                else:
                    return ''

            @property
            def sum(self):
                if self._durations.size:
                    return hrs_mins_to_string(seconds_to_hrs_mins(np.sum(self._durations)))
                else:
                    return ''

            @property
            def count(self):
                return str(self._durations.size)

        class _RatingStat:
            def __init__(self, ratings: np.array):
                self._ratings = ratings

            @property
            def mean(self):
                if self._ratings.size:
                    return str(_filter_float(round(np.mean(self._ratings), precision)))
                else:
                    return ''

            @property
            def stdev(self):
                if self._ratings.size:
                    return str(_filter_float(round(np.std(self._ratings), precision)))
                else:
                    return ''

            @property
            def median(self):
                if self._ratings.size:
                    return str(_filter_float(round(np.median(self._ratings), precision)))
                else:
                    return ''

            @property
            def iqr(self):
                if self._ratings.size:
                    first = round(np.quantile(self._ratings, 0.25), precision)
                    third = round(np.quantile(self._ratings, 0.75), precision)
                    return f'({_filter_float(first)}, {_filter_float(third)})'
                else:
                    return ''

            @property
            def count(self):
                return str(self._ratings.size) if self._ratings.size else ''

        start_times = [x.start_time for x in records_query if x.start_time]  # TODO Test: remove conditional
        stop_times = [x.stop_time for x in records_query if x.stop_time]  # TODO Test: remove conditional
        starts_arr = np.array([x.start_time.timestamp() for x in records_query])
        stops_arr = np.array([x.stop_time.timestamp() if x.stop_time else np.nan for x in records_query])
        self._count_incomplete = abs(len(start_times) - len(stop_times))
        d = stops_arr - starts_arr
        d_array = d[np.logical_not(np.isnan(d))]
        self._durations = _DurationStat(d_array)
        r = np.array([x.session_rating for x in records_query])
        r_array = r[r != np.array(None)]
        self._ratings = _RatingStat(r_array)

    @property
    def durations(self):
        return self._durations

    @property
    def ratings(self):
        return self._ratings

    @property
    def incomplete(self):
        return self._count_incomplete


class RecordDurationStats:
    _ddf = None

    def __init__(self, recordsdf: pd.DataFrame = None):
        if recordsdf is None:
            rq = db.session.query(GamingSessionRecord)
            recordsdf = pd.read_sql(rq.statement, db.engine)
        df = recordsdf
        df['duration'] = (recordsdf['stop_time'].astype('datetime64[ns]') -
                          recordsdf['start_time'].astype('datetime64[ns]'))
        ddf = df['duration'].describe()
        ddf['sum'] = df['duration'].sum()
        self._ddf = ddf

    @property
    def count(self):
        return self._ddf.loc['count']

    @property
    def mean(self):
        return timedelta_to_str(self._ddf.loc['mean']) if self._ddf.loc['count'] else None

    @property
    def std(self):
        return timedelta_to_str(self._ddf.loc['std']) if self._ddf.loc['count'] else None

    @property
    def min(self):
        return timedelta_to_str(self._ddf.loc['min']) if self._ddf.loc['count'] else None

    @property
    def qtr1(self):
        return timedelta_to_str(self._ddf.loc['25%']) if self._ddf.loc['count'] else None

    @property
    def med(self):
        return timedelta_to_str(self._ddf.loc['50%']) if self._ddf.loc['count'] else None

    @property
    def qtr3(self):
        return timedelta_to_str(self._ddf.loc['75%']) if self._ddf.loc['count'] else None

    @property
    def max(self):
        return timedelta_to_str(self._ddf.loc['max']) if self._ddf.loc['count'] else None

    @property
    def sum(self):
        return timedelta_to_str(self._ddf.loc['sum']) if self._ddf.loc['count'] else None


class RecordRatingStats:
    _ddf = None

    def __init__(self, recordsdf: pd.DataFrame = None):
        if recordsdf is None:
            rq = db.session.query(GamingSessionRecord)
            recordsdf = pd.read_sql(rq.statement, db.engine)
        df = recordsdf
        self._ddf = df['session_rating'].describe()

    @property
    def count(self):
        return int(self._ddf.loc['count'])

    @property
    def mean(self):
        return round(self._ddf.loc['mean'], 3) if self._ddf.loc['count'] else None

    @property
    def std(self):
        return round(self._ddf.loc['std'], 3) if self._ddf.loc['count'] else None

    @property
    def min(self):
        return self._ddf.loc['min'] if self._ddf.loc['count'] else None

    @property
    def qtr1(self):
        return round(self._ddf.loc['25%'], 3) if self._ddf.loc['count'] else None

    @property
    def med(self):
        return round(self._ddf.loc['50%'], 3) if self._ddf.loc['count'] else None

    @property
    def qtr3(self):
        return round(self._ddf.loc['75%'], 3) if self._ddf.loc['count'] else None

    @property
    def max(self):
        return self._ddf.loc['max'] if self._ddf.loc['count'] else None


class BasicUsageStats:
    _df = None

    def __init__(self, recordsdf: pd.DataFrame = None):
        if recordsdf is None:
            recordsdf = pd.read_sql(db.session.query(GamingSessionRecord).statement, db.engine)
        df = recordsdf.copy()
        df.loc[:, 'complete'] = 0
        df.loc[~(df['start_time'].isna() | df['stop_time'].isna()), 'complete'] = 1
        self._df = df
        self._aq = db.session.query(GamingSessionRecord)

    @property
    def frequency(self):
        if self._aq.count():
            return round(self._df.shape[0] / self._aq.count(), 3)
        return None

    @property
    def complete(self):
        if self._df.shape[0]:
            ddf = self._df['complete'].value_counts()
            return ddf[1] if 1 in ddf.index else 0
        return None

    @property
    def incomplete(self):
        if self._df.shape[0]:
            ddf = self._df['complete'].value_counts()
            return ddf[0] if 0 in ddf.index else 0
        return None


class TagStats:

    def __init__(self,
                 tagtype: str = 'emotions',
                 data: pd.DataFrame = None,
                 ):
        tm = {
            'emotions': GamingEmotionTag,
            'interruptions': GamingInterruptionTag,
        }[tagtype]
        if data is None:
            q = (db.session.query(
                GamingSessionRecord.id.label('records'),
                GamingEmotionTag.id.label('emotions'),
                GamingInterruptionTag.id.label('interruptions')
            )
                 .outerjoin(GamingSessionRecord.emotions)
                 .outerjoin(GamingSessionRecord.session_interruptions)
                 .outerjoin(GamingSessionInterruption.tags)
                 )
            data = pd.read_sql(q.statement, db.engine)
        c = data[tagtype].value_counts().reset_index()
        p = data[tagtype].value_counts(normalize=True).reset_index()
        cp = pd.merge(c, p, on=tagtype).set_index(tagtype)
        cpl = cp.nlargest(1, 'count', 'all')
        t = [db.session.query(tm).filter_by(id=x).first() for x in cpl.index]
        cpl.reset_index(inplace=True)
        c = 0
        p = None
        if cpl.shape[0]:
            c = cpl.loc[0, 'count']
            p = round(cpl.loc[0, 'proportion'], 3)
        a = [
            (db.session.query(tm).filter_by(id=x).first(),
             cp.loc[x, 'count'],
             round(cp.loc[x, 'proportion'], 3)
             )
            for x in cp.index
        ]
        self._all = a
        self._mostcommon = SimpleNamespace()
        setattr(self._mostcommon, 'tags', t)
        setattr(self._mostcommon, 'count', c)
        setattr(self._mostcommon, 'proportion', p)

    @property
    def mostcommon(self):
        return self._mostcommon

    @property
    def all(self):
        return self._all


class NotesQueryStats:
    def __init__(self, precision=3):
        self._notes_query = db.session.query(GamingNote).all()
        self._precision = precision

    @property
    def count(self):
        return len(self._notes_query)

    @property
    def important(self):
        c = len([x.important for x in self._notes_query if x.important])
        return f'{c} ({self.meanimportant})'

    @property
    def meanimportant(self):
        m = round(np.array([x.important for x in self._notes_query]).mean(), self._precision)
        return m

    @property
    def stdevimportant(self):
        std = round(np.array([x.important for x in self._notes_query]).std(), self._precision)
        return std

    @property
    def withgame(self):
        g = [1 if x.game else 0 for x in self._notes_query]
        return f'{int(np.sum(g))} ({round(np.mean(g), self._precision)})'

    @property
    def withrecord(self):
        r = [1 if x.record else 0 for x in self._notes_query]
        return f'{int(np.sum(r))} ({round(np.mean(r), self._precision)})'

    @property
    def meaninterval(self):
        return

    @property
    def meanlength(self):
        return


class GamesQueryStats:
    def __init__(self, precision: int = 3):
        self._precision = precision

    @property
    def count(self):
        return db.session.query(Game).count()

    @property
    def mostplayedbycount(self):
        q = (db.session.query(Game.id, Game.name, func.count(GamingSessionRecord.game_id).label('count'))
             .join(GamingSessionRecord.game).group_by(GamingSessionRecord.game_id))
        df = pd.read_sql(q.statement, db.engine)
        fdf = df[df['count'] == df['count'].max()][['id', 'name', 'count']].values
        return fdf

    @property
    def leastplayedbycount(self):
        q = (db.session.query(Game.id, Game.name, func.count(GamingSessionRecord.game_id).label('count'))
             .join(GamingSessionRecord.game).group_by(GamingSessionRecord.game_id))
        df = pd.read_sql(q.statement, db.engine)
        fdf = df[df['count'] == df['count'].min()][['id', 'name', 'count']].values
        return fdf

    @property
    def mostplayedbyduration(self):
        return

    @property
    def leastplayedbyduration(self):
        return


def get_notes_stats(dataframe: pd.DataFrame = None):
    if dataframe is None:
        nq = db.session.query(GamingNote)
        dataframe = pd.read_sql(nq.statement, db.engine)
    df = dataframe.copy()
    o = SimpleNamespace()
    # Get count for all notes and notes marked important
    setattr(o, 'count', df['note'].count())
    ic = df['important'].value_counts().reset_index()
    ip = df['important'].value_counts(normalize=True).reset_index()
    icp = pd.merge(ic, ip, on='important').set_index('important')
    so = SimpleNamespace()
    setattr(o, 'important', so)
    icv = 0
    icvp = 0.0
    if True in icp.index:
        icv = icp.loc[True, 'count']
        icvp = round(icp.loc[True, 'proportion'], 3)
    setattr(so, 'count', icv)
    setattr(so, 'proportion', icvp)
    # Get counts of notes with records
    rdf = df.dropna(subset='record_id')
    so = SimpleNamespace()
    setattr(o, 'records', so)
    setattr(so, 'count', rdf['record_id'].count())
    setattr(so, 'proportion', round(so.count / o.count, 3))
    # Get counts of notes with games
    gdf = df.dropna(subset='game_id')
    so = SimpleNamespace()
    setattr(o, 'games', so)
    setattr(so, 'count', gdf['game_id'].count())
    setattr(so, 'proportion', round(so.count / o.count, 3))
    gc = gdf['game_id'].value_counts().reset_index()
    gp = gdf['game_id'].value_counts(normalize=True).reset_index()
    gcp = pd.merge(gc, gp, on='game_id')
    a = [
        (db.session.query(Game).filter_by(id=int(gcp.loc[x, 'game_id'])).first(),
         gcp.loc[x, 'count'],
         round(gcp.loc[x, 'proportion'], 3))
        for x in gcp.index
    ]
    setattr(so, 'all', a)
    lgcp = gcp.nlargest(1, 'count', 'all')
    so1 = SimpleNamespace()
    setattr(so, 'mostcommon', so1)
    setattr(so1, 'tags', [db.session.query(Game).filter_by(id=x).first() for x in lgcp['game_id']])
    setattr(so1, 'count', None if not lgcp.shape[0] else lgcp.loc[0, 'count'])
    setattr(so1, 'proportion', None if not lgcp.shape[0] else round(lgcp.loc[0, 'proportion'], 3))
    so = SimpleNamespace()
    setattr(o, 'dates', so)
    e = df.nsmallest(n=1, columns=['date_added']).reset_index().loc[0, 'id']
    la = df.nlargest(n=1, columns=['date_added']).reset_index().loc[0, 'id']
    setattr(so, 'earliest', db.session.query(GamingNote).filter_by(id=int(e)).first())
    setattr(so, 'latest', db.session.query(GamingNote).filter_by(id=int(la)).first())
    sd = df['date_added'].sort_values()
    mtc = sd.diff()
    setattr(so, 'diffmean', timedelta_to_str(mtc.mean()))
    setattr(so, 'diffstd', timedelta_to_str(mtc.std()))
    return o


def get_games_stats(dataframe: pd.DataFrame = None):
    if dataframe is None:
        gq = (db.session.query(Game.id.label('games'),
                               GamingSessionRecord.id.label('records'),
                               GamingSessionRecord.start_time,
                               GamingSessionRecord.stop_time,
                               GamingEmotionTag.id.label('emotions'),
                               GamingInterruptionTag.id.label('interruptions')
                               )
              .outerjoin(Game.records)
              .outerjoin(GamingSessionRecord.emotions)
              .outerjoin(GamingSessionRecord.session_interruptions)
              .outerjoin(GamingSessionInterruption.tags)
              )
        dataframe = pd.read_sql(gq.statement, db.engine)
        dataframe['durations'] = dataframe['stop_time'] - dataframe['start_time']
    df = dataframe
    gc = len(df['games'].unique())  # game count
    rcf = df.drop_duplicates(['games', 'records']).groupby(['games'])['records'].count()  # number of records per game
    s = rcf.sum()  # total number of unique records
    rc = {x: (db.session.query(Game).filter_by(id=x).first(),
              rcf.loc[x],
              round(rcf.loc[x] / s, 3)
              ) for x in rcf.index
          }  # dict of game ids indexing game model, record count, and proportion of total record count
    rcs = [v for k, v in rc.items()]
    rcs = sorted(rcs, key=lambda e: e[2], reverse=True)
    lrcf = rcf.nlargest(1, keep='all')  # games with the largest record counts
    cl = [rc[x] for x in lrcf.index]  # list of most populous games
    cc = None if not cl else cl[0][1]  # record count
    cp = None if not cl else cl[0][2]  # records proportion

    dcf = df.drop_duplicates(['games', 'records']).groupby('games')['durations'].sum()  # sum of durations per game
    s = dcf.sum()  # total sum of all durations
    dca = {x: (rc[x][0],
               timedelta_to_str(dcf.loc[x]),
               round(dcf.loc[x] / s, 3)
               ) for x in dcf.index
           }  # dict of game ids indexing game model, record duration sum, and proportion of total sum
    dcs = [v for k, v in dca.items()]
    dcs = sorted(dcs, key=lambda e: e[2], reverse=True)
    ldcf = dcf.nlargest(1, keep='all')
    dl = [dca[x] for x in ldcf.index]  # list of most populous games
    dc = None if not dl else dl[0][1]  # record duration
    dp = None if not dl else dl[0][2]  # records proportion of total duration of all games

    o = SimpleNamespace()
    co = SimpleNamespace()
    co1 = SimpleNamespace()
    do = SimpleNamespace()
    do1 = SimpleNamespace()

    setattr(o, 'counts', co)
    setattr(co, 'gamecount', gc)
    setattr(co, 'all', rcs)
    setattr(co, 'mostcommon', co1)
    setattr(co1, 'games', [x[0] for x in cl])
    setattr(co1, 'count', cc)
    setattr(co1, 'proportion', cp)
    setattr(o, 'durations', do)
    setattr(do, 'all', dcs)
    setattr(do, 'mostcommon', do1)
    setattr(do1, 'games', [x[0] for x in dl])
    setattr(do1, 'count', dc)
    setattr(do1, 'proportion', dp)
    return o


def gamenames_to_options():
    """
    Converts tagmodel objects to a list of options for use in an HTML select input
    :return: list[tuple(int, str, str)]
    """
    games = Game.query.all()  # Get all tags for this model
    options = [(g.name, g.name, {}) for g in games]
    options = sorted(options, key=lambda e: e[0])
    p = [('', 'Select a game...', dict(selected=True, hidden=True))]
    return p + options


def route_interruption(form, interruption: GamingSessionInterruption):
    if form.add_interruption.data:
        form.duration.data = None
        form.interruption.data = ''
        form.add_interruption.data = False
        form.start_time.data = None
        form.stop_time.data = None
        if form.add_note.data:
            form.add_note.data = True
            return render_template(
                'gamingdb/create_session_interruption.html',
                record=interruption.record,
                form=form)
        else:
            return redirect(url_for(
                'gamingdb.create_session_interruption', record_id=interruption.record.id)
            )
    if form.add_note.data:
        return redirect(url_for('gamingdb.create_note', record_id=interruption.record.id))
    return redirect(
        url_for('gamingdb.session_interruption', session_interruption_id=interruption.id))


def solve_missing_time(start: datetime, stop: datetime, duration: int):
    if start and stop:
        duration = int((stop - start).total_seconds() // 60)
    elif start and duration is not None:
        stop = start + timedelta(minutes=duration)
    elif stop and duration is not None:
        start = stop - timedelta(minutes=duration)
    return start, stop, duration
