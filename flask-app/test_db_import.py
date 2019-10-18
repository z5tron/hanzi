import sqlite3
from chinese import db, Word, User, Progress
from datetime import datetime, timedelta
import dateparser
import pytz

db.drop_all()
db.create_all()

for i in [1,2,3]:
    uname = "A{}".format(i)
    u = User(id=i, username= uname, name=uname, email='{}@localhost.cc'.format(uname))
    db.session.add(u)
db.session.commit()

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

words = {}
cur.execute('select wordId,word,dateAdded,points,ifreq from pool')
for wid,w,t,p,ifreq in cur.fetchall():
    if len(w) > 4: continue
    words[wid] = { 'id' : wid, 'word': w, 'created_date': t, 'ifreq': ifreq }

word_in_table = {}
word_book = {}
cur.execute('select rowid,wordId,chapterId,bookName,chapterName from wordbook')
new_id = 1
for rid,wid,chid,name,chname in cur.fetchall():
    name = name.replace(u'\ufeff', '')
    if wid not in words: continue
    k = "{}_{}".format(wid, name)
    if k in word_book:
        print("skip existing {} {}".format(name, wid))
        continue
    word_book[k] = 1
    w = Word(id=new_id, word=words[wid]['word'], book=name, chapter=chname,
             created_date = words[wid]['created_date'])
    db.session.add(w)
    word_in_table[wid] = 1
    words[wid]['new_id'] = new_id # the one with table
    new_id += 1
db.session.commit()

for wid,w in words.items():
    if wid in word_in_table: continue
    # print("adding {} belongs to no book".format(w['word']))
    ww = Word(id=new_id, word=w['word'], book="45kuaidu", created_date=w['created_date'])
    db.session.add(ww)
    db.session.commit()
    w['new_id'] = new_id
    new_id += 1


word_trial = {}
cur.execute('select wordId,dateStudy,points from progress')
for wid,t,pt in cur.fetchall():
    if wid not in words:
        print("skip {}".format(wid))
        continue
    nid = words[wid]['new_id']
    total_pt = words[wid].get('total_points', 0) + pt
    t = pytz.utc.localize(datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%fZ"))
    words[wid]['total_points'] = total_pt
    word_trial[wid] = word_trial.get(wid, 0) + 1
    p = Progress(user_id=1, word_id=nid, word=words[wid]['word'],
                 trial = word_trial[wid],
                 study_date = t, points = pt, total_points = total_pt)
    db.session.add(p)
db.session.commit()


