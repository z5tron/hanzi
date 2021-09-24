import json
from datetime import datetime, timedelta
from os import path, getcwd, chdir
import subprocess, uuid
import pytz
import math
import random

from flask import jsonify, render_template, render_template_string, session, redirect, url_for, request, send_file
from . import main
from .. import db, hanzi_words
from flask_login import login_required, current_user
from ..models import User, Progress, Word, Score

from sqlalchemy import desc
from sqlalchemy.sql import func

# the next practice date will be days later
NEXT_STUDY = [2,2,2,3,3,4,4,5,6,7,9,10,30,45,60,60,90,90,180,240,365,365]


@main.route('/')
def index():
    session_date = int(datetime.utcnow().strftime("%Y%m%d"))
    users = []
    for u in User.query.all():
        s = Score.query.filter_by(user_id=u.id, study_y4md=session_date).first()
 
        st = { 
            'name': u.name, 'tot_xpoints': u.tot_xpoints,
            'streak': u.streak, 'session_date': session_date,
            'num_pass': 0 if not s else s.num_pass,
            'num_fail': 0 if not s else s.num_fail,
            'num_thumb_up': 0 if not s else s.num_thumb_up,
            'cur_xpoints': 0 if not s else s.xpoints,
        }
        # c = Word.query.filter_by(user_id=u.id).filter(Word.streak >= 3).filter(func.length(Word.word) < 4).count()
        c = db.session.query(Word.word.distinct()).filter_by(user_id=u.id).filter(Word.streak >= 3).filter(func.length(Word.word) < 4).count()
        st['3streak'] = c
        t0 = datetime.utcnow() + timedelta(hours=4)
        st['num_due'] = Word.query.filter_by(user_id=u.id).filter(Word.next_study < t0).count()
        
        users.append(st)

    users = sorted(users, key=lambda x: (x['session_date'], x['cur_xpoints']), reverse=True)
    return render_template("index.html", users=users)

@main.route('/import-book')
@login_required
def import_book():
    book = request.args.get('book')
    chapter = request.args.get('chapter')
    if not book or not chapter:
        existing_books = {}
        for w in Word.query.filter_by(user_id=current_user.id).all():
            k = "{}__{}".format(w.book, w.chapter)
            if k in existing_books: continue
            existing_books[k] = 1
        books = []
        for w in db.session.query(Word.book, Word.chapter).distinct():
            k = "{}__{}".format(w.book, w.chapter)
            if k in existing_books: continue
            books.append([w.book, w.chapter])
        return render_template('import-book.html', books=sorted(books))
    else:
        inserted = {}
        for w in Word.query.filter_by(user_id=current_user.id).filter_by(book=book).filter_by(chapter=chapter).all():
            if w.word in inserted: continue
            inserted[w.word] = 1
        new_word = {}
        for w in Word.query.filter_by(book=book).filter_by(chapter=chapter).all():
            if w.word in inserted or w.word in new_word: continue
            new_word[w.word] = 1

        for w in new_word.keys():
            wi = Word(user_id=current_user.id, word=w,
                      book = book, chapter=chapter)
                      
            db.session.add(wi)
        db.session.commit()
        return redirect(url_for('main.user'))
        
@main.route('/user')
@login_required
def user():
    username = session.get("username", "")
    if not username:
        return redirect(url_for('auth.login'))
    user = User.query.filter_by(username=username).first_or_404()

    cur_t = datetime.utcnow()
    cur_y4md = cur_t.year*10000+cur_t.month*100+cur_t.day

    books = {}
    for w in Word.query.filter_by(user_id=current_user.id): #db.session.query(Word.book).filter(Word.user_id==current_user.id).distinct():
        books.setdefault(w.book, {'done': 0, 'due': 0})
        if w.next_study > cur_t:
            books[w.book]['done'] += 1
        else:
            books[w.book]['due'] += 1
            
    score = db.session.query(func.sum(Score.xpoints)).filter(Score.user_id==user.id).first()
    user.tot_xpoints = score[0]
    
    # user.session_date = cur_y4md
    
    score = Score.query.filter_by(user_id=user.id, study_y4md=cur_y4md).first()
    # print(score.id, score.num_pass)
    user.cur_xpoints = 0 if not score else score.xpoints
    num_pass_daily = 0 if not score else score.num_pass
    # cur_loc_t = cur_t - timedelta(minutes=user.timezone_offset)
    # cur_loc_y4md = cur_loc_t.year*10000 + cur_loc_t.month*100 + cur_loc_t.day
    # user.session_date = cur_loc_y4md
    db.session.add(user)
    db.session.commit()
    t0 = cur_t + timedelta(hours=4)
    num_due = Word.query.filter_by(user_id=user.id).filter(Word.next_study < t0).count()
    session['num_pass_daily'] = num_pass_daily
    return render_template('user.html', user=user, books=books, num_due = num_due)


def read_words(user_id, book = None, nlimit = 500, ignore_recent=0):
    words, word_set = [], set([])
    t0 = datetime.utcnow()
    wl = Word.query.filter_by(user_id=user_id).filter(Word.next_study < t0 + timedelta(hours=2)).filter(Word.study_date < t0 - timedelta(hours=abs(ignore_recent)))
    if book:
        wl = wl.filter_by(book=book)
        
    for w in wl.order_by(Word.tot_xpoints, desc(Word.next_study)):
        if len(words) >= nlimit: break
        # skip the know words
        if w.word in word_set: continue
        # reset the points
        if w.study_date < datetime.utcnow() - timedelta(hours=24):
            w.cur_xpoints = 0
        words.append({ 'id': w.id, 'word': w.word,
                       'book': w.book, 'chapter': w.chapter,
                       'study_date': w.study_date.timestamp(),
                       'next_study': w.next_study.timestamp(),
                       'cur_xpoints': w.cur_xpoints,
                       'tot_xpoints': w.tot_xpoints,
                       'score': 0,
                       'num_pass': w.num_pass, 'num_fail': w.num_fail,
                       'streak': w.streak,
                       'istep': w.istep + 1,
                       'related': hanzi_words.get(w.word, []) })
        word_set.update(w.word)
        
    return words

@main.route('/practice')
@login_required
def practice():
    book = request.args.get('book', None)
    num_pass_daily = session.get("num_pass_daily", 0)
    words = read_words(current_user.id, book=book, ignore_recent=2)
    random.shuffle(words)
    return render_template(
        'practice.html', user = current_user, book=book,
        streak=current_user.streak, words=words,
        num_pass_daily = num_pass_daily, tot_steps = len(NEXT_STUDY))

@main.route('/expand')
@login_required
def exam_expand():
    book = request.args.get('book', None)
    num_pass_daily = session.get("num_pass_daily", 0)
    t0 = datetime.now().timestamp()
    words = read_words(current_user.id, book, nlimit=3000)
    words = sorted(list(filter(lambda x: x['streak'] < 3 and x['next_study'] < t0, words)),
                   key = lambda x: x['num_pass'], reverse=True)
    
    return render_template(
        'practice.html', user = current_user, book=book,
        streak=current_user.streak, words=words,
        num_pass_daily = num_pass_daily, tot_steps = len(NEXT_STUDY))

@main.route('/exam')
@login_required
def exam():
    words, word_set = [], set([])
    for w in Word.query.filter_by(user_id=current_user.id).filter(Word.streak >= 3).order_by(Word.next_study, Word.tot_xpoints).all():
        if w.word in word_set: continue

        if w.study_date < datetime.utcnow() - timedelta(hours=24):
            w.cur_xpoints = 0
        words.append({ 'id': w.id, 'word': w.word,
                          'book': w.book, 'chapter': w.chapter,
                          'study_date': w.study_date.timestamp(),
                          'next_study': w.next_study.timestamp(),
                          'cur_xpoints': w.cur_xpoints,
                          'tot_xpoints': w.tot_xpoints,
                          'score': 0,
                          'num_pass': w.num_pass, 'num_fail': w.num_fail,
                          'streak': w.streak,
                          'istep': w.istep + 1,
                          'related': hanzi_words.get(w.word, []) })
        word_set.update(w.word)
        
    num_pass_daily = session.get("num_pass_daily", 0)
    return render_template(
        'practice.html', user = current_user, book='',
        streak=current_user.streak, words=words,
        num_pass_daily = num_pass_daily, tot_steps = len(NEXT_STUDY))

@main.route('/review')
@login_required
def review():
    num_pass_daily = session.get("num_pass_daily", 0)
    words = {}
    t0 = datetime.utcnow() - timedelta(days=7, hours=2)
    for w in Word.query.filter_by(user_id=current_user.id).filter(Word.cur_xpoints<0).filter(Word.study_date >= t0).order_by(Word.study_date, Word.tot_xpoints, Word.chapter).limit(200):
        words.setdefault(w.word, {
            'id': w.id, 'word': w.word,
            'book': w.book, 'chapter': w.chapter,
            'study_date': w.study_date.timestamp(),
            'next_study': w.next_study.timestamp(),
            'cur_xpoints': w.cur_xpoints, 'tot_xpoints': w.tot_xpoints,
            'score': 0, 'timezone_offset': current_user.timezone_offset,
            'num_pass': w.num_pass, 'num_fail': w.num_fail, 'streak': w.streak,
            'related': hanzi_words.get(w.word, []) })
    return render_template(
        'review.html', user = current_user, streak=current_user.streak, words=list(words.values()),
        num_pass_daily = num_pass_daily)

# @main.route('/words/<book>')
# def words(book):
#     istart = request.args.get('istart', 0)
#     words = []
#     for w in Word.query.filter_by(book=book).all(): #slice(istart, istart+10):
#         words.append({
#             'word': w.word, 'book': w.book, 'chapter': w.chapter,
#             'study_date': w.study_date.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
#             'id': w.id, 'total_points': w.total_points,
#             'score': 0, 'user_id': w.user_id})

#     return jsonify(words)

@main.route('/save', methods=['POST'])
@login_required
def save_words():
    data = request.get_json()
    uid = current_user.id

    w = data['word']
    p = Progress(user_id=uid, word_id=w['id'],
                 word = w['word'], book = w['book'], chapter = w['chapter'],
                 study_date = datetime.utcnow(),
                 xpoints = data['xpoints'])
    db.session.add(p)
    cur_t = datetime.utcnow()
    for wbi in Word.query.filter_by(word=w['word']).filter_by(user_id=current_user.id):
        wbi.cur_xpoints += data['xpoints']
        wbi.study_date = cur_t
        wbi.tot_xpoints += data['xpoints']
        # fix unitialized streak
        if wbi.streak == 0 and wbi.num_fail == 0 and data['xpoints'] > 0:
            wbi.streak = wbi.num_pass
            
        if data['xpoints'] > 0:
            wbi.num_pass += 1
            wbi.streak += 1
            wbi.istep += data['xpoints']
        elif data['xpoints'] < 0:
            wbi.num_fail += 1
            wbi.streak = 0
            wbi.istep -=2
        wbi.istep = min(max(0, wbi.istep), len(NEXT_STUDY)-1)
        if data['xpoints'] < 0:
            wbi.next_study = cur_t + timedelta(days=1)
        else:
            wbi.next_study = cur_t + timedelta(days=NEXT_STUDY[wbi.istep])
            
        db.session.add(wbi)

        # updates for the return
        w['study_date'] = cur_t.timestamp()
        w['next_study'] = wbi.next_study.timestamp()
        w['xpoints'] = wbi.tot_xpoints
        w['istep'] = wbi.istep

    score_date = int(cur_t.strftime("%Y%m%d"))
    score = Score.query.filter_by(user_id=current_user.id, study_y4md=score_date).first()
    if not score:
        score = Score(user_id=current_user.id, study_y4md=score_date)
        db.session.add(score)
        db.session.commit()
    score.xpoints += data['xpoints']
    score.study_date = datetime.utcnow()
    score.num_thumb_up += data['thumbs_up']
    if data['xpoints'] > 0: score.num_pass += 1
    elif data['xpoints'] < 0: score.num_fail += 1
    db.session.add(score)

    db.session.commit()

    return jsonify(w)

@main.route('/dump-progress', methods=['GET'])
def dump_progress():
    s = ""
    for p in Progress.query.all():
        s += p.json() + "\n"
    return s, 200, {'Content-Type': 'text/plain; charset=utf-8'}

@main.route('/cleanup-progress', methods=['GET'])
def cleanup_progress():
    p_info = {}
    del_id_list = []
    for p in Progress.query.order_by(Progress.study_date.desc()).all():
        if p.word not in p_info:
            p_info[p.word] = { 'max_trial': p.trial, 'total': 1 }
        else:
            p_info[p.word]['total'] += 1
            del_id_list.append(p.id)
        if len(del_id_list) > 500: break
    s = "DELETE {} rows\n".format(len(del_id_list))
    for pid in del_id_list:
        p = db.session.query(Progress).filter_by(id=pid).first()
        s += p.json() + "\n"
        db.session.delete(p)
    db.session.commit()
    return s, 200, {'Content-Type': 'text/plain; charset=utf-8'}
            
@main.route('/print', methods=['GET'])
def printWordsMain():
    return render_template("print.html")

@main.route('/print', methods=['POST'])
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
    OUTPUT = '/tmp'
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
