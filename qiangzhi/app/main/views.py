import json
from datetime import datetime, timedelta
from os import path, getcwd, chdir
import subprocess, uuid
import pytz

from flask import jsonify, render_template, render_template_string, session, redirect, url_for, request, send_file
from . import main
from .. import db, hanzi_words
from flask_login import login_required, current_user
from ..models import User, Progress, Word, Score

from sqlalchemy.sql import func

def get_user_progress(userid, tz_offset=240):
    loc_t = datetime.utcnow() - timedelta(minutes=tz_offset)
    utc_cutoff = datetime.utcnow() - timedelta(hours=loc_t.hour, 
                                               minutes=loc_t.minute)
    words = {}
    total_points, today_points = 0, 0
    for w in Progress.query.filter_by(user_id=userid).order_by(Progress.study_date.desc()).all():
        if w.word_id not in words:
            words[w.word_id] = {
                'word': w.word, 'book': w.book, 'chapter': w.chapter,
                'trial': w.trial,
                'study_date': w.study_date.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
                'word_id': w.word_id, 'total_points': w.total_points,
                'score': 0, 'user_id': w.user_id}
            total_points += w.total_points if w.total_points < 5000 else 0
        if w.study_date > utc_cutoff:
            words[w.word_id]['score'] += w.points
            today_points += w.points
    return { 'total_points': total_points, 'today_points': today_points}


@main.route('/secret')
@login_required
def secret():
    return "Only authenticated users are allowed!"

@main.route('/')
def index():
    return render_template("index.html")

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
    books = []
    for w in db.session.query(Word.book).filter(Word.user_id==current_user.id).distinct():
        books.append(w.book)
    score = db.session.query(func.sum(Score.xpoints)).filter(Score.user_id==user.id).first()
    user.tot_xpoints = score[0]

    cur_t = datetime.utcnow()
    cur_y4md = cur_t.year*10000+cur_t.month*100+cur_t.day
    score = Score.query.filter_by(user_id=user.id, study_y4md=cur_y4md).first()
    user.cur_xpoints = 0 if not score else score.xpoints
    user.session_date = cur_y4md
    db.session.add(user)
    db.session.commit()

    return render_template('user.html', user=user, books=sorted(books))


@main.route('/practice')
@login_required
def practice():
    book = request.args.get('book')
    words = []
    t0 = datetime.utcnow() - timedelta(minutes=10)
    for w in Word.query.filter_by(user_id=current_user.id).filter_by(book=book).filter(Word.streak <= 5).order_by(Word.chapter, Word.tot_xpoints).limit(300):
        # if datetime.utcnow().strftime("%Y%m%d") == w.study_date.strftime("%Y%m%d"):
        #    score = w.xpoints
        y4md = w.study_date.year*10000+w.study_date.month*100+w.study_date.day
        if y4md != current_user.session_date:
            w.cur_xpoints = 0
            db.session.add(w)
            db.session.commit()

        # what can be skipped ? streak > 5
        # recent (within 30 minutes) studied and passed
        if w.study_date > datetime.utcnow() - timedelta(minutes=30) and w.cur_xpoints > 0: continue
        # print(w.word, w.cur_xpoints, w.tot_xpoints, w.study_date, end="")

        words.append({ 'id': w.id, 'word': w.word,
                       'book': w.book, 'chapter': w.chapter,
                       'study_date': w.study_date.strftime("%Y-%m-%dT%H:%M:%S%z"),
                       'cur_xpoints': w.cur_xpoints, 'tot_xpoints': w.tot_xpoints,
                       'score': 0,
                       'num_pass': w.num_pass, 'num_fail': w.num_fail, 'streak': w.streak,
                       'related': hanzi_words.get(w.word, []) })
    # words = json.dumps(words)
    return render_template(
        'words.html', user = current_user, book=book, streak=current_user.streak, words=words)

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
        if cur_t.strftime("%Y%m%d") == wbi.study_date.strftime("%Y%m%d"):
            wbi.cur_xpoints += data['xpoints']
        else:
            wbi.cur_xpoints = data['xpoints']
        wbi.study_date = cur_t
        wbi.tot_xpoints += data['xpoints']
        # fix unitialized streak
        if wbi.streak == 0 and wbi.num_fail == 0 and data['xpoints'] > 0:
            wbi.streak = wbi.num_pass
            
        if data['xpoints'] > 0:
            wbi.num_pass += 1
            wbi.streak += 1
        elif data['xpoints'] < 0:
            wbi.num_fail += 1
            wbi.streak = 0

        db.session.add(wbi)
    cur_y4md = cur_t.year*10000+cur_t.month*100+cur_t.day
    score = Score.query.filter_by(user_id=current_user.id, study_y4md=current_user.session_date).first()
    if not score:
        score = Score(user_id=current_user.id, study_y4md=current_user.session_date)
        db.session.add(score)
        db.session.commit()
    score.xpoints += data['xpoints']
    score.study_date = datetime.utcnow()
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
