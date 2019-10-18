import pytz
import sqlite3
from datetime import datetime

utc=pytz.utc
ny=pytz.timezone("America/New_York")

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
cur.execute('select rowid,wordId,dateStudy from progress')
date_fix = []
for rid,wid,t in cur.fetchall():
    if not t:
        print(rid, wid)
        continue
    if len(t) == 19 and t[10] == ' ':
        loc_t = ny.localize(datetime.strptime(t, "%Y-%m-%d %H:%M:%S"))
        utc_t = loc_t.astimezone(utc)
        date_fix.append([utc_t.strftime("%Y-%m-%dT%H:%M:%S.000Z"), rid])
    elif len(t) == 24 and t[10]== 'T':
        continue
    else:
        print(t)
    # continue
#cur.executemany("update progress set dateStudy=? where rowid=?", date_fix)
#conn.commit()
conn.close()



