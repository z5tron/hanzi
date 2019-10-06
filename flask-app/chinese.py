# -*- coding: utf-8 -*-

from flask import Flask, current_app
from flask import render_template, send_file
from flask import Response, abort, request, jsonify, g, send_from_directory

import sys
import codecs
import random
import sqlite3
from os import path, getcwd, chdir
from datetime import datetime, timedelta
import subprocess
import argparse
import uuid

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# DBFNAME = path.join(app.root_path, "chinese.sqlite3")
DBFNAME = "/var/tmp/db.sqlite3"
PORT=5000
DEBUG=False
OUTPUT="/tmp"

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
def hanzi_index():
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
    prevStudy = {} # 
    for wordId,dateStudy,points in cur.fetchall():
        if wordId not in wd:
            continue # studied not in pool ?
        prevStudy.setdefault(dateStudy[:10], 0)
        prevStudy[dateStudy[:10]] += 1
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
           'cut': ncut, 'totalWords': len(wd), 'daily': {}, 'bookList': sorted(list(allBooks.keys()))}
    
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
    
    # dt, ret['reviewDays'] = datetime.now(), []
    # for i in range(5):
    #     ret['reviewDays'].append((dt-timedelta(days=i)).strftime("%Y-%m-%d"))
    ret['reviewDays'] = []
    for k in sorted(prevStudy.keys(), reverse=True):
        if len(ret['reviewDays']) > 4: break
        ret['reviewDays'].append(k)
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
        saved.append([(k, word[k]) for k in ('wordId', 'score', 'dateStudy')])
        if word['score'] > 0: passed += 1
        elif word['score'] < 0: failed += 1
    print(saved)
    if saved:
        d = datetime.now().strftime("%Y%m%d")
        cur.execute('insert into daily(date) values(?)', (int(d),))
        cur.execute('update daily set pass=pass+?,fail=fail+?,points=? where date=?',
                    (passed, failed, data['points'], d))
    conn.commit()
    #return Response("{}\n{}".format(words, saved), mimetype="text/text")
    print(jsonify(saved))
    return jsonify(saved)

def updateBook(cur, book):
    """insert the book if not exist. return the bookId"""
    bookId = -1;
    for x in cur.execute('select bookId from books where bookName=? limit 1', (book,)):
        bookId = x[0]
    if bookId > 0: return bookId
    cur.execute('insert into books(bookName) values(?)', (book,))
    return cur.lastrowid
    
@app.route('/add', methods=['POST'])
def addWords():
    # print("request data:", request.get_data())
    conn = get_db() # sqlite3.connect("chinese.sqlite3")
    cur = conn.cursor()
    cur.execute("select word,wordId from pool")
    all_words = cur.fetchall()
    if len(all_words) > 100000: # Chinese is limited
        abort(400, "The database is full")
    # print("we have ", len(all_words), " words")
    data = request.get_json()
    # print(data)
    words = dict([(w, -1) for w in data['words']])
    if len(words) > 5000:
        abort(400, "Too many words") 
    # return Response("{}".format(words), mimetype="text/text")
    
    bookName = data['book']
    chapterName = data.get('chapter', '')
    bookId = updateBook(cur, bookName)

    for r in all_words:
        if r[0] not in words: continue
        words[r[0]] = r[1]

    saved = []
    for w, wid in words.items():
        w_pool_new, w_in_more_book = 0, 0 
        if wid < 0: # new word
            cur.execute('insert into pool(word,points) values(?,0)', (w,))
            w_pool_new = 1
            wid = cur.lastrowid
        # check if book
        cur.execute('select chapterId,bookName from wordbook where wordId=? and bookName=?',
                    (wid,bookName))
        data = cur.fetchone()
        if data is None:
            cur.execute('insert into wordbook(wordId,chapterId,bookName,chapterName) values(?,-1,?,?)',
                        (wid, bookName,chapterName))
            w_in_more_book = 1
        # response 
        saved.append((w, wid, w_pool_new, w_in_more_book))
    conn.commit()
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


@app.route('/print', methods=['GET'])
def printWordsMain():
    return current_app.send_static_file("print.html")

@app.route('/print', methods=['POST'])
def printWords():
    print("request data:", request.get_data())
    title=request.form.get("title", "汉字练习")
    #words=request.form.get("wordText", "").split()
    # fill the words into whole page, 36characters, 3columns*12
    rawWordText = request.form.get("wordText", "").replace(" ", "")
    # skip the ASCII
    words = rawWordText #
    print(request.form.get("dedupe"))
    if request.form.get("dedupe", "off") == "on":
        print("dedupe is turned on for rawWordText:", len(rawWordText))
        wdict = {}
        for i,w in enumerate(rawWordText):
            wdict.setdefault(w, i)
        wlist = sorted([(v,k) for k,v in wdict.items()])
        words = "".join([x[1] for x in wlist])
        print("new length: ", len(words))
    words = "".join([' ' if ord(x)<128 else x for x in words[:360]])
    words = words.strip()
    # patch to whole page, 12 per column, 3 columns per page
    while len(words) % 36 != 0:
        words = words + " "

    print(len(words), "'{}'".format(words))
    cwd = getcwd()
    chdir(OUTPUT)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    ftex = "{}-{}".format(ts, uuid.uuid4())
    with open("{}.tex".format(ftex), 'w') as f:
        f.write(render_template("print_words_3col.tex", title=title,
                                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                words=words))
    subprocess.run(["xelatex", path.join(OUTPUT, "{}.tex".format(ftex))])
    chdir(cwd)
    fpdf = path.join(OUTPUT, '{}.pdf'.format(ftex))
    print("output file: ", fpdf)
    return send_file(fpdf, as_attachment=True)
    return ftex

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chinese")
    parser.add_argument('--db', default='/var/tmp/db.sqlite3', help="SQLite3 db")
    parser.add_argument('--port', type=int, default=5000, help="port")
    parser.add_argument('--output', default='/var/www/output', help="Output dir")
    
    args = parser.parse_args()
    PORT = args.port
    DBFNAME = args.db
    OUTPUT=args.output
    app.run(host="0.0.0.0", port=PORT, debug=True)
