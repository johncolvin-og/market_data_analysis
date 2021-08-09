import pandas as pd
import numpy as np
import os
import sqlite3


# args:
# db: full name of the database (ex:'~/sparkdata/simulations/comex/feb/2021-02-16_360_24h.sqlite')
# contracts: list of contracts for which top_of_books is needed (ex: ['HGU1','HGV1','HGU1-HGV1'])
# returns: top_of_book dataframe


def get_top_books(db, contracts):
    where_txt = ''
    i = 0
    for s in contracts:
        p_filter = 'symbol=' + "'" + s + "'"
        prefix_or = '' if (i == 0) else ' or '
        where_txt = where_txt + prefix_or + p_filter
        i = i+1
    where_txt = '(' + where_txt + ')'
    query = 'select * from top_of_books where ' + where_txt
    print(query)
    return pd.read_sql_query(query, sqlite3.connect(db))

# args:
# db: full name of the database (ex:'~/sparkdata/simulations/comex/feb/2021-02-16_360_24h.sqlite')
# contracts: list of contracts for which top_of_books is needed (ex: ['HGU1','HGV1','HGU1-HGV1'])
# returns: tuple of top_of_books dataframe filtered for the contracts and the entire events table dataframe


def get_books_ev_from_db(db, contracts):
    bk_db = get_top_books(db, contracts)
    # so nans dont get converted to 'NaN' strings
    bk_db = bk_db.astype({'bid': 'float64', 'ask': 'float64',
                          'ibid': 'float64', 'iask': 'float64'})
    bk_db['mbid'] = np.where(
        bk_db['bid'] > bk_db['ibid'], bk_db['bid'], bk_db['ibid'])
    bk_db['mbid_qty'] = np.where(
        bk_db['bid'] > bk_db['ibid'], bk_db['bid_qty'], bk_db['ibid_qty'])
    bk_db['mask'] = np.where(
        bk_db['ask'] < bk_db['iask'], bk_db['ask'], bk_db['iask'])
    bk_db['mask_qty'] = np.where(
        bk_db['ask'] < bk_db['iask'], bk_db['ask_qty'], bk_db['iask_qty'])
    ev_db = pd.read_sql_query('select * from events', sqlite3.connect(db))
    return (bk_db, ev_db)

# args:
# events: entire events table dataframe
# top_books: top of books as returned by get_books_ev_from_db
# leg_contracts: list of contracts for which top_of_books is needed (ex: ['HGU1','HGV1','HGU1-HGV1'])
# returns: df with synced columns corresponding to the leg_contracts


def line_up_books(events, top_books, leg_contracts):
    print("Lining up book for: " + str(leg_contracts))

    def ren(col_name, i):
        return col_name + '_' + str(i)
    # cleanup books
    books = top_books[['symbol', 'eid', 'mbid',
                       'mbid_qty', 'mask', 'mask_qty']]
    prices = events
    i = 1
    for l in leg_contracts:
        # filter for the symbols we care
        leg_bk = books[books.symbol == l]
        leg_bk = leg_bk.rename({'symbol': ren('leg', i), 'eid': ren('eid', i),
                                'mbid': ren('bid', i), 'mbid_qty': ren('bid_qty', i),
                                'mask': ren('ask', i), 'mask_qty': ren('ask_qty', i)},
                               axis=1)
        prices = prices.merge(leg_bk,
                              how='outer',
                              left_on=['eid'],
                              right_on=[ren('eid', i)])
        i = i+1
    prices = prices.set_index(['eid'], drop=False)
    prices = prices.sort_index()
    # fill holes (every event only updates one symbol) with previous value of book
    prices = prices.ffill()
    prices = prices.rename_axis(None)
    return prices

# args:
# lined_up_books: lined up books as returned by the function line_up_books
# leg_qtys: leg qty's for each leg that lined_up_books has been lined up for
# returns: dataframe = lined_up_books + 4 columns corresponding to the synthetic top of book


def compute_synth_top(lined_up_books, leg_qtys):
    import sys
    rv = lined_up_books
    sz = lined_up_books['eid'].size
    # adding new columns
    rv['pb'] = pd.Series([0] * sz)
    rv['pbq'] = pd.Series([sys.maxsize] * sz)
    rv['pa'] = pd.Series([0] * sz)
    rv['paq'] = pd.Series([sys.maxsize] * sz)
    # To compute synthetic bid market, view it as => contract can be sold at the bid
    # so buy leg => sold, sell leg => bought
    # buy_leg -> sold -> bid price
    # sell_leg -> bought -> ask price
    # similiarly synthetic ask => contract be be bought at the ask
    # buy_leg -> bought -> ask price
    # sell_leg -> sold -> bid price
    i = 0
    for q in leg_qtys:
        i = i + 1
        leg_bid = lined_up_books['bid_'+str(i)]
        leg_bid_qty = lined_up_books['bid_qty_'+str(i)]
        leg_ask = lined_up_books['ask_'+str(i)]
        leg_ask_qty = lined_up_books['ask_qty_'+str(i)]
        # synth bid market
        if q > 0:
            # synth bid
            rv['pb'] = rv['pb'] + q * leg_bid
            rv['pbq'] = np.minimum(rv['pbq'], leg_bid_qty)
            # synth ask
            rv['pa'] = rv['pa'] + q * leg_ask
            rv['paq'] = np.minimum(rv['paq'], leg_ask_qty)
        else:
            rv['pb'] = rv['pb'] + q * leg_ask
            rv['pbq'] = np.minimum(rv['pbq'], leg_ask_qty)
            rv['pa'] = rv['pa'] + q * leg_bid
            rv['paq'] = np.minimum(rv['paq'], leg_bid_qty)
    return rv

# args:
# db: full name of the database (ex:'~/sparkdata/simulations/comex/feb/2021-02-16_360_24h.sqlite')
# synth_text: synthetic text as represented in the DB, ex: '+(HGK1-HGZ1) -(HGU1-HGZ1) -(HGN1-HGU1) -(HGK1-HGN1)'
# returns: 5-tuple
# 1. events db df as is
# 2. top_of_books db df filtered for the contracts in the synthetic
# 3. lined up books df corresponding to the legs in the synthetic
# 4. synthetic books top df
# 5. time to compute the result


def get_synthetic_book_top(db, synth_txt):
    import time
    beg = time.time()
    # downloading and cleaning books and events
    synth_spr = SyntheticSpread(synth_txt)
    bk_db, ev_db = get_books_ev_from_db(db, synth_spr.leg_contracts())
    print(
        f"downloaded and cleaned books and events, t: {time.time()-beg} secs")
    # lining up books for the synthetic
    lu_books = line_up_books(ev_db, bk_db, synth_spr.leg_contracts())
    print(f"lined up books and events, t: {time.time()-beg} secs")
    # computing synthetic books from the lined up leg books
    synth_book = compute_synth_top(lu_books, synth_spr.leg_quantities())
    print(f"computed synthetic books, t: {time.time()-beg} secs")
    end = time.time()
    return (ev_db, bk_db, lu_books, synth_book, end-beg)


def find_positive_edge(synthetic_top, tol=0.00001):
    return synthetic_top[(synthetic_top['pb'] >= tol) | (synthetic_top['pa'] <= -1*tol)]


# full_db_name is the fully qualified name of the .sqlite file
# ex: "/home/taha/sparkdata/comex/feb/2021-02-16_360_24h.sqlite"
# products is the list of the products
# ex: ["GC,SI,HG"]
def get_poly_vals_db(full_db_name, products):
    where_txt = ''
    i = 0
    for p in products:
        p_filter = 'product=' + "'" + p + "'"
        prefix_or = '' if (i == 0) else ' or '
        where_txt = where_txt + prefix_or + p_filter
        i = i+1
    where_txt = '(' + where_txt + ')'
    query = 'select * from polygon_value_events where ' + where_txt
    print(query)
    return pd.read_sql_query(query, sqlite3.connect(full_db_name))


def find_nearest_eid(full_db_name, eid):
    q_txt = "select eid,t_time from events where eid <= {eid_} order by eid desc limit 1;".format(
        eid_=eid)
    return pd.read_sql_query(q_txt, sqlite3.connect(full_db_name))


def get_book_evolution(full_db_name, sid, eid, n_events, time_win_ns=0):
    eid_row = find_nearest_eid(full_db_name, eid)
    eid = eid_row['eid'][0]
    t_time_0 = eid_row['t_time'][0]
    t_time_end = t_time_0 + time_win_ns
    if n_events > 0:
        q_txt = "select eid, sid, t_time, bid_p_0, bid_q_0, ask_p_0, ask_q_0 from books where sid={sid_} and eid >= {eid_} limit {n_events_}".format(
            sid_=sid, eid_=eid, n_events_=n_events)
    else:
        q_txt = "select eid, sid, t_time, bid_p_0, bid_q_0, ask_p_0, ask_q_0 from books where sid={sid_} and eid >= {eid_} and t_time <= {t_time_end_}".format(
            sid_=sid, eid_=eid, n_events_=n_events, t_time_end_=t_time_end)
    print(q_txt)
    df = pd.read_sql_query(q_txt, sqlite3.connect(full_db_name))
    df['spread'] = df['ask_p_0'] - df['bid_p_0']
    df['t_delta'] = (df['t_time'] - t_time_0)/1000
    df['eid_delta'] = df['eid'] - eid
    return df


def get_book_evolution(full_db_name, sec_id, start_eid, n_events):
    query_txt = ("select *, t_time-t2_t_time from  " +
                 "(select * from " +
                 "(select eid, sid, t_time, bid_p_0, bid_q_0, ask_p_0, ask_q_0,(ask_p_0-bid_p_0) as spread from books where sid=3853 and eid >= 4191809-11 limit 400) "
                 "JOIN " +
                 "(select sid as t2_sid, t_time as t2_t_time from books where eid = 4191809) t2 on sid = t2.t2_sid);")
    return pd.read_sql_query(query_txt, sqlite3.connect(full_db_name))


# adds 2 columns that are every opp_id's first_s_time and last_s_time
# repeated across all rows in the opp
# (on a second thought this will not work for polygons that get in
# and out with an opportunity, since they will be tagged with the
# start of the total opp)
def add_opp_start_times(poly_vals):
    # this is the groupby method that acts on a single opp and
    # returns the first row's (not 0th, since that is the pre row)
    # first_s_time and last_s_time as an array of 2
    def analyze_single_opp(single_opp_pvs):
        opp_first_p_st = single_opp_pvs['first_s_time'].iloc[1]
        opp_last_p_st = single_opp_pvs['last_s_time'].iloc[1]
        return [opp_first_p_st, opp_last_p_st]
    rv = poly_vals.groupby('opp_id').apply(lambda x: analyze_single_opp(x))
    st_df = rv.to_frame().reset_index()
    st_df.columns = ['opp_id', 'st']
    st_df['opp_first_s_time'] = st_df['st'].apply(lambda x: x[0])
    st_df['opp_last_s_time'] = st_df['st'].apply(lambda x: x[1])
    st_df = st_df[['opp_id', 'opp_first_s_time', 'opp_last_s_time']]
    # at this point st_df is a table with 3 cols - opp_id, opp_first_s_time, opp_last_s_time
    # and has a row for each opp_id
    # now join it with opps to repeat the values across
    return poly_vals.merge(st_df, how='inner', left_on=['opp_id'], right_on=['opp_id'])

# finds the nearest n_rows in both directions for a columns, to a given value
# df_sourece: datafrane containing the data
# col_name: column where to find the value
# target: numerical target value
# is_sorted:


def nearest_rows(df_source, col_name, target, n_rows, is_sorted=True):
    df = df_source
    df['diff'] = df[col_name]-target
    df_less = df[df['diff'] < 0]
    df_more = df[df['diff'] >= 0]
    if(is_sorted == False):
        df_more = df_more.sort_values(['diff'], ascending=[True])
        df_less = df_less.sort_values(['diff'], ascending=[True])
    rv = df_less.tail(n_rows).append(df_more.head(n_rows))
    return rv
