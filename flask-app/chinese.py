# -*- coding: utf-8 -*-
# Python 2.7

from flask import Flask, current_app
from flask import render_template
from flask import Response, request, jsonify, g

import codecs
import random
import sqlite3
from os import path
from datetime import datetime, timedelta


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# DBFNAME = path.join(app.root_path, "chinese.sqlite3")
DBFNAME = "/tmp/db.sqlite3"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DBFNAME)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()




@app.route('/')
def hello_world():
    T = datetime.now() - timedelta(days=4)
    conn = get_db()
    cur = conn.cursor()
    return current_app.send_static_file("chinese.html")

@app.route('/words')
def getWords():
    conn = get_db() # sqlite3.connect("chinese.sqlite3")
    cur = conn.cursor()
    dt = datetime.now().strftime("%Y-%m-%d")
    dt2 = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    cur.execute('select wordId,word,points,ifreq from pool')
    wd = dict([(r[0], {'wordId': r[0], 'word': r[1], 'points': r[2], 'ifreq': r[3], 'dateStudy': ''}) for r in cur.fetchall()])

    ncut = 50
    tcut = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
    cur.execute('select wordId,max(dateStudy),sum(points) from progress group by wordId')
    for wordId,dateStudy,points in cur.fetchall():
        if wordId not in wd:
            continue # studied not in pool ? 
        # studied today, skip
        if dateStudy[:10] >= dt2 or points > 100000 or (points >= ncut and dateStudy[:10] > tcut):
            wd.pop(wordId)
            continue
        
        # upate pool
        wd[wordId]['dateStudy'] = dateStudy
    newWd = [ w for w,v in wd.items() if v['dateStudy'] == '' ]
    #kn = random.sample(newWd, min(20, len(newWd)))
    print("found words:", len(wd))
    kn = random.sample(list(wd.keys()), len(wd)) # wd; #random.sample(wd, min(20, len(wd)))
    #while len(kn) < 20:
    #    kn += random.sample(wd.keys(), 1)
    allBooks = {}
    for k in kn:
        cur.execute('select wordId,chapterId,bookName,chapterName from wordbook where wordId=?',
                    (wd[k]['wordId'],))
        wd[k]['bookList'] = [ (c[2].strip(), c[3].strip()) for c in cur.fetchall()]
        wd[k]['books'] =', '.join([':'.join(c) for c in wd[k]['bookList']])
        for book,chap in wd[k]['bookList']:
            allBooks.setdefault(book, 0)
            ++allBooks[book]
    ret = {'words': sorted([wd[k] for k in kn], key = lambda x: (x['points'], x['dateStudy'])),
           'cut': ncut, 'totalWords': len(wd), 'daily': {}, 'bookList': list(allBooks.keys())}
    
    ret['today'] = int(datetime.now().strftime("%Y%m%d"))
    cur.execute('select date,pass,fail,points from daily order by date')
    totPoints = 0;
    for date,passed,failed,points in cur.fetchall():
        ret['daily'][date] = [passed, failed, points]
        if date < ret['today']:
            totPoints += points
    ret['firstDay'] = min(ret['daily'].keys())
    ret['totalStudyDays'] = len(ret['daily'])
    ret['totalPoints'] = sum([ points for d,(p,f,points) in ret['daily'].items()
                               if d < ret['today']])
    ret['totalDays'] = (datetime.now() - datetime.strptime(str(ret['firstDay']), "%Y%m%d")).days
    
    dt, ret['reviewDays'] = datetime.now(), []
    for i in range(5):
        ret['reviewDays'].append((dt-timedelta(days=i)).strftime("%Y-%m-%d"))
    ret['reviewDays'].append((dt-timedelta(days=14)).strftime("%Y-%m-%d"))
    return jsonify(ret)


@app.route('/save', methods=['POST'])
def saveWords():
    data = request.get_json()
    words = data['words']
    # return Response("{}".format(words), mimetype="text/text")
    conn = get_db() # sqlite3.connect("chinese.sqlite3")
    cur = conn.cursor()
    saved, passed, failed = [], 0, 0
    for word in words:
        if word.get('skip', 0): continue
        cur.execute('update pool set points=points + ? where wordId=?',
                    (word['score'], word['wordId']))
        cur.execute('insert into progress(wordId, points, dateStudy) values(?,?,?)',
                    (word['wordId'], word['score'], word['dateStudy']))
        saved.append(word)
        if word['score'] > 0: passed += 1
        elif word['score'] < 0: failed += 1
    if saved:
        d = datetime.now().strftime("%Y%m%d")
        cur.execute('insert into daily(date) values(?)', (int(d),))
        cur.execute('update daily set pass=pass+?,fail=fail+?,points=? where date=?',
                    (passed, failed, data['points'], d))
        conn.commit()
    #return Response("{}\n{}".format(words, saved), mimetype="text/text")
    print(saved)
    return jsonify(saved)


def utc_to_local(utcs, dt):
    t0 = datetime.strptime(utcs, "%Y-%m-%dT%H:%M:%S.%fZ")
    return (t0-dt).strftime("%Y-%m-%d %H:%M:%S")

@app.route('/review/<deadline>')
def review_words(deadline):
    deadline = ''.join(x for x in deadline if x.isdigit())
    T = datetime.now()
    dt1 = datetime(int(deadline[:4]), int(deadline[4:6]), int(deadline[6:8])) #T.strftime("%Y-%m-%d")
    dt2 = T
    if len(deadline) >= 16:
        dt2 = datetime(int(deadline[8:12]), int(deadline[12:14]), int(deadline[14:16]))
    # convert to utc
    dt = datetime.utcnow() - datetime.now()
    ts = [(ti+dt).strftime("%Y-%m-%dT%H:%M:%S") for ti in (dt1, dt2)]

    conn = get_db()
    cur = conn.cursor()

    cur.execute('select prog.wordId,pool.word,prog.dateStudy,pool.points from (select * from progress where points < 0) as prog left join pool on prog.wordId=pool.wordId where prog.dateStudy > ? and prog.dateStudy < ? and pool.points < 50 ORDER by prog.dateStudy ASC', (ts[0], ts[1],))
    words = [{'wordId': r[0], 'word': r[1], 'dateStudy': utc_to_local(r[2], dt), 'points': r[3]} for r in cur.fetchall()]

    count = {}
    cur.execute('select distinct wordId from progress where points > 0')
    count['once'] = len(cur.fetchall())
    cur.execute('select wordId from pool where points >= 50')
    count['done'] = len(cur.fetchall())
    cur.execute('select wordId from pool')
    count['size'] = len(cur.fetchall())
    cur.execute('select pass,fail,points from daily where date=?', (deadline[0:8],))
    
    count['points'] = cur.fetchone()[-1] if cur.rowcount > 0 else 0
    return render_template("chinese_review.html", words=words, count=count, revDate=deadline[0:8])




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
