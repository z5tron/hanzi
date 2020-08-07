import os
import sys
import click
import json
from datetime import datetime
import pytz

from flask_migrate import Migrate, upgrade
from app import create_app, db
from app.models import User, Word, Progress, Score

from sqlalchemy.sql.expression import func

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User)

@app.cli.command()
def test():
    """run the unit tests"""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

@app.cli.command("add-users")
def add_users():
    for i in range(1,4):
        u = "A{}".format(i)
        user = User(email=u+"@localhost.cc", username=u, name=u, password='cat',
                    first_study = pytz.utc.localize(datetime(2017, 7, 15, 12, 41, 12)) )
        db.session.add(user)
    db.session.commit()

@app.cli.command("deploy")
def deploy():
    upgrade()
    

@app.cli.command("import-word")
@click.argument('fname')
def import_word(fname):
    import json

    Word.query.delete()
    db.session.commit()

    for line in open(fname, 'r'):
        if line.find("#") >= 0: continue
        j = json.loads(line)

        study_date = datetime.strptime(j['study_date'], "%Y-%m-%d %H:%M:%S.%f%z")
        y4md = study_date.year * 10000 + study_date.month * 100 + study_date.day
        if j['__tablename__'] == 'word':
            created_date = datetime.strptime(j['created_date'], "%Y-%m-%d %H:%M:%S")
            w = Word(id = j['id'], word=j['word'], user_id=j['user_id'],
                     created_date=created_date,
                     book = j['book'], chapter=j['chapter'],
                     tot_xpoints = j['tot_xpoints'],
                     num_pass = j['num_pass'],
                     num_fail = j['num_fail'],
                     study_date = study_date)
            db.session.add(w)
    db.session.commit()

@app.cli.command("import-progress")
@click.argument('fname')
def import_progress(fname):
    import json

    Progress.query.delete()
    db.session.commit()

    for line in open(fname, 'r'):
        if line.find("#") >= 0: continue
        j = json.loads(line)

        study_date = datetime.strptime(j['study_date'], "%Y-%m-%d %H:%M:%S.%f%z")
        y4md = study_date.year * 10000 + study_date.month * 100 + study_date.day
        if j['__tablename__'] == 'progress':
            p = Progress(user_id=j['user_id'], word_id=j['word_id'], word=j['word'],
                         book=j['book'], chapter=j['chapter'],study_date=study_date, 
                         xpoints=int(j['xpoints']))
            db.session.add(p)

    db.session.commit()


@app.cli.command("adjust-progress-xpoints")
def adjust_progress_xpoints():
    user_study_date = {}
    daily_stat = {}
    
    for p in Progress.query.order_by(Progress.study_date).all():
        if p.xpoints <= 2 and p.xpoints >= -2: continue
        if p.xpoints > 2: p.xpoints = 2
        elif p.xpoints < -2: p.xpoints = -2
        db.session.add(p)
    db.session.commit()


@app.cli.command("calc-xpoints")
def calc_xpoints():
    score = {}
    word_points = {}
    for p in Progress.query.order_by(Progress.study_date).all():
        t = p.study_date
        y4md = t.year * 10000 + t.month * 100 + t.day
        k = y4md * 100 + p.user_id 
        score.setdefault(k, Score(user_id = p.user_id, study_y4md = y4md, xpoints=0, num_pass=0, num_fail=0, num_thumb_up=0, num_thumb_down=0 ))
        score[k].xpoints += p.xpoints
        score[k].study_date = p.study_date

        word_points.setdefault(p.user_id, {})
        word_points[p.user_id].setdefault(
            p.word, {'tot_xpoints': 0,
                     'num_pass': 0,
                     'num_fail': 0,
                     'cur_xpoints': 0,
                     'streak': 0,
                     'study_date': datetime(1970, 1, 1),
                     'session_date': 19700101})
        word_points[p.user_id][p.word]['tot_xpoints'] += p.xpoints;
        if p.xpoints > 0:
            score[k].num_pass += 1
            word_points[p.user_id][p.word]['num_pass'] += 1
            word_points[p.user_id][p.word]['streak'] += 1
        elif p.xpoints > 0:
            score[k].num_fail += 1
            word_points[p.user_id][p.word]['num_fail'] += 1
            word_points[p.user_id][p.word]['streak'] = 0

        if y4md == word_points[p.user_id][p.word]['session_date']:
            word_points[p.user_id][p.word]['cur_xpoints'] += p.xpoints
        else:
            word_points[p.user_id][p.word]['cur_xpoints'] = p.xpoints
            word_points[p.user_id][p.word]['session_date'] = y4md
        if word_points[p.user_id][p.word]['study_date'] < p.study_date:
            word_points[p.user_id][p.word]['study_date'] = p.study_date

    for k,sc in score.items():
        y4md = k // 100
        uid = k % 100
        s = Score.query.filter_by(user_id=uid, study_y4md=y4md).first()
        if s:
            s.xpoints = sc.xpoints
            s.study_date = sc.study_date
            s.num_pass = sc.num_pass
            s.num_fail = sc.num_fail
        else:
            s = sc
        db.session.add(s)
    db.session.commit()

    for uid, words in word_points.items():
        tot_points = 0
        for ws, wd in words.items():
            tot_points += wd['tot_xpoints']
            for w in Word.query.filter_by(user_id=uid, word=ws).all():
                w.study_date = wd['study_date']
                w.cur_xpoints = wd['cur_xpoints']
                w.tot_xpoints = wd['tot_xpoints']
                w.num_pass = wd['num_pass']
                w.num_fail = wd['num_fail']
                w.streak = wd['streak']
                db.session.add(w)
        db.session.commit()
        user = User.query.filter_by(id=uid).first()
        print(uid, user.name, user.tot_xpoints, tot_points)
        user.tot_xpoints = tot_points
        db.session.add(user)
        db.session.commit()


@app.cli.command("import-db")
@click.argument('fname')
def import_db(fname):
    import json

    Progress.query.delete()
    Word.query.delete()
    Score.query.delete()
    db.session.commit()

    user_study_date = {}
    daily_stat = {}
    
    for line in open(fname, 'r'):
        if line.find("#") >= 0: continue
        j = json.loads(line)

        study_date = datetime.strptime(j['study_date'], "%Y-%m-%d %H:%M:%S.%f%z")
        y4md = study_date.year * 10000 + study_date.month * 100 + study_date.day
        if j['__tablename__'] == 'word':
            created_date = datetime.strptime(j['created_date'], "%Y-%m-%d %H:%M:%S")
            w = Word(id = j['id'], word=j['word'], user_id=j['user_id'],
                     created_date=created_date,
                     book = j['book'], chapter=j['chapter'],
                     tot_xpoints = j['tot_xpoints'],
                     num_pass = j['num_pass'],
                     num_fail = j['num_fail'],
                     study_date = study_date)
            db.session.add(w)
        elif j['__tablename__'] == 'progress':
            p = Progress(user_id=j['user_id'], word_id=j['word_id'], word=j['word'],
                         book=j['book'], chapter=j['chapter'],study_date=study_date, 
                         xpoints=int(j['xpoints']))
            db.session.add(p)
            uid = j['user_id']
            daily_stat.setdefault(y4md, { } )
            daily_stat[y4md].setdefault(uid, { 'xpoints': 0, 'pass': 0, 'fail': 0, 'up': 0, 'down': 0,
                                               'study_date' : study_date})
            pt = j['xpoints']
            daily_stat[y4md][uid]['xpoints'] += pt
            if pt > 0: daily_stat[y4md][uid]['pass'] += 1
            if pt < 0: daily_stat[y4md][uid]['fail'] += 1
            daily_stat[y4md][uid]['study_date'] = max([study_date, daily_stat[y4md][uid]['study_date']])

            user_study_date.setdefault(uid, study_date)
            if study_date > user_study_date[uid]:
                user_study_date[uid] = pytz.utc.localize(study_date)
    #
    db.session.commit()
    for k in sorted(daily_stat.keys()):
        for uid,st in daily_stat[k].items():
            s = Score(user_id=uid, study_y4md=k, xpoints = st['xpoints'],
                      num_pass = st['pass'],
                      num_fail = st['fail'],
                      num_thumb_up = st['up'],
                      num_thumb_down = st['down'],
                      study_date = st['study_date'])
            db.session.add(s)
    db.session.commit()

    for uid, t in user_study_date.items():
        u = User.query.filter_by(id = uid).first()
        if u is None: continue
        if t > pytz.utc.localize(u.last_study):
            u.last_study = t
            db.session.add(u)
            db.session.commit()
        
    
    
@app.cli.command("export-db")
@click.argument('fname')
def export_db(fname):
    # db.drop_all()
    # db.create_all()
    import pytz
    from datetime import datetime
    word_in_book = {}
    f = open(fname, 'w')
    for p in Progress.query.order_by(Progress.study_date.desc()).all():
        f.write("{}\n".format(p.json()))
    f.close()


@app.cli.command("check-db")
@click.argument('fname')
def check_db(fname):
    # db.drop_all()
    # db.create_all()
    import pytz
    import json
    from datetime import datetime
    for line in open(fname, 'r'):
        if line.find("#") >= 0: continue
        j = json.loads(line)
        study_date = datetime.strptime(j['study_date'], "%Y-%m-%d %H:%M:%S.%f%z")
        p = Progress(user_id=j['user_id'],
                     word_id=int(j['word_id']), word=j['word'],
                     book=j['book'], chapter=j['chapter'],study_date=study_date, trial=int(j['trial']),
                     xpoints=int(j['xpoints']), total_points=int(j['total_points']))
        # db.session.add(p)
    # db.session.commit()

@app.cli.command("dump-old-db")
@click.argument('dbname')
def dump_old_db(dbname):
    import pytz
    import sqlite3
    conn = sqlite3.connect(dbname)
    cur = conn.cursor()

    # read all words, key is book_chapter_word
    words = {}
    # the same word with wid may be in different books
    word_id = {}
    cur.execute('select w.rowid,w.wordId,w.bookName,w.chapterName,p.word,p.dateAdded,p.points,p.ifreq '
                'from wordbook w '
                'left join pool p on p.wordId=w.wordId')
    max_id = 0
    for rowid,wid,book,chap,w,t,points,ifreq in cur.fetchall():
        k = "{}_{}_{}".format(book, chap, w)
        words[k] = { 'id': rowid, 'word_id' : wid, 'user_id': 1,
                     'word': w, 'book': book, 'chapter': chap,
                     'created_date': t, 'tot_xpoints': points, 'ifreq': ifreq,
                     'study_date': pytz.utc.localize(datetime(1970, 1, 1)),
                     'num_pass': 0, 'num_fail': 0
        }
        word_id.setdefault(wid, { 'bchw': [], 'ibook': 0 })
        word_id[wid]['bchw'].append(k)
        max_id = max([rowid, max_id])

    # some word has no book information
    cur.execute('select wordId,word,dateAdded,points from pool')
    for wid,w,t,points in cur.fetchall():
        if wid in word_id: continue
        k = "45kuaidu_ch_{}".format(w)
        max_id += 1
        words[k] = { 'id': max_id, 'word_id' : wid, 'word': w, 'user_id': 1,
                     'book': '45kuaidu', 'chapter': 'ch',
                     'created_date': t, 'tot_xpoints': points, 'ifreq': -1,
                     'study_date': pytz.utc.localize(datetime(1970, 1, 1)),
                     'num_pass': 0, 'num_fail': 0 }
        word_id.setdefault(wid, { 'bchw': [], 'ibook': 0 })
        word_id[wid]['bchw'].append(k)

    # for same word, use the smallest points
    for wid,info in word_id.items():
        min_points = min([words[k]['tot_xpoints'] for k in info['bchw']])
        max_points = max([words[k]['tot_xpoints'] for k in info['bchw']])
        for k in info['bchw']:
            words[k]['tot_xpoints'] = min_points
        
    progress = []
    cur.execute('select rowid,wordId,dateStudy,points from progress order by dateStudy desc')
    for rowid,wid,t,pt in cur.fetchall():
        if wid not in word_id:
            print("skip {}".format(wid))
            continue
        # word family
        wf = word_id[wid]
        wf.setdefault('xpoints', 0)
        t = pytz.utc.localize(datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%fZ"))
        if t < pytz.utc.localize(datetime(2011, 11, 1)):
            raise RuntimeError("invalid date: {} for {}".format(t, wid))
        i = wf['ibook']
        k = wf['bchw'][i]
        w = words[k]
        w['study_date'] = max([t, w['study_date']])
        progress.append({ 'id': rowid, 'user_id': 1, 'word_id': wid,
                          'word': w['word'], 'book': w['book'],
                          'chapter': w['chapter'],
                          'study_date': t, 'xpoints': pt })

        wf['ibook'] = (wf['ibook'] + 1) % len(wf['bchw'])
        if pt > 0:
            for k in wf['bchw']: words[k]['num_pass'] += 1
        elif pt < 0:
            for k in wf['bchw']: words[k]['num_fail'] += 1
        
    daily_stat = {}
    for p in progress:
        t = p['study_date']
        today = t.year * 10000 + t.month * 100 + t.day

        daily_stat.setdefault(today, { 'xpoints': 0, 'pass': 0, 'fail': 0, 'up': 0, 'down': 0})
        daily_stat[today]['xpoints'] += pt
        if pt > 0: daily_stat[today]['pass'] += 1
        if pt < 0: daily_stat[today]['fail'] += 1
    for k, w in words.items():
        w['__tablename__'] = 'word'
        #w['created_date'] = w['created_date'].strftime("%Y-%m-%d %H:%M:%S.%f%z")
        w['study_date'] = w['study_date'].strftime("%Y-%m-%d %H:%M:%S.%f%z")
        print(json.dumps(w, sort_keys=True))
    for p in progress:
        p['__tablename__'] = 'progress'
        p['study_date'] = p['study_date'].strftime("%Y-%m-%d %H:%M:%S.%f%z")        
        # print(p)
        print(json.dumps(p, sort_keys=True))
        
    for t in sorted(daily_stat.keys())[-10:]:
        print(t, daily_stat[t], file=sys.stderr)
    print("words: {}, progress: {}".format(len(words), len(progress)), file=sys.stderr)

@app.cli.command("cizu2zi")
def conv_cizu2zi():
    words = {}
    for w in Word.query.filter(func.length(Word.word) <= 3).all():
        words.setdefault((w.user_id, w.word, w.book, w.chapter), w)

    print(f"read {len(words)} cizu")
    del_ids = []
    for w in Word.query.filter(func.length(Word.word) > 3).all():
        cizu = w.word
        can_delete = True
        for zi in cizu:
            k = (w.user_id, zi, w.book, w.chapter)
            if k in words:
                print(f"skip {zi}")
            else:
                print("adding ", zi, w.book, w.chapter)
                w2 = Word(user_id=w.user_id, word = zi, book = w.book,
                          chapter = w.chapter, study_date = w.study_date,
                          cur_xpoints = w.cur_xpoints,
                          tot_xpoints = w.tot_xpoints,
                          num_pass = w.num_pass,
                          num_fail = w.num_fail,
                          streak = w.streak,
                          istep = w.istep,
                          next_study = w.next_study)
                db.session.add(w2)
                can_delete = False
                words[k] = w2

        db.session.commit()
        if can_delete:
            print(f"delete {cizu}, {w.id}")
            del_ids.append(w.id)
            db.session.delete(w)
            db.session.commit()

# main
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)

