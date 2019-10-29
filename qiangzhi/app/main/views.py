import json
from datetime import datetime, timedelta

from flask import jsonify, render_template, render_template_string, session, redirect, url_for, request
from . import main
from .. import db, hanzi_words
from flask_login import login_required
from ..models import User, Progress

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

@main.route('/user')
@login_required
def user():
    username = session.get("username", "")
    user = User.query.filter_by(username=username).first_or_404()
    books = {}
    user_progress = get_user_progress(user.id)
    for p in Progress.query.filter_by(user_id=user.id).order_by(Progress.study_date):
        if not p.book: continue
        books.setdefault(p.book, 0)
        books[p.book] += 1
    user.total_points = user_progress['total_points']
    user.today_points = user_progress['today_points']
    session['total_points'] = user.total_points
    session['today_points'] = user.today_points
    books = sorted(books.items(), key = lambda x: x[0])
    return render_template('user.html', user=user, books=books)

def get_practice_list(book, tz_offset = 240):
    loc_t = datetime.utcnow() - timedelta(minutes=tz_offset)
    utc_cutoff = datetime.utcnow() - timedelta(hours=loc_t.hour,
                                               minutes=loc_t.minute)
    words = {}
    for w in Progress.query.filter_by(book=book).order_by(Progress.study_date.desc()).all():
        if w.word_id not in words:
            words[w.word_id] = {
                'word': w.word, 'book': w.book, 'chapter': w.chapter,
                'trial': w.trial,
                'study_date': w.study_date.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
                'word_id': w.word_id, 'total_points': w.total_points,
                'score': 0, 'user_id': w.user_id}
        if w.study_date > utc_cutoff:
            words[w.word_id]['score'] += w.points
            
    return sorted(words.values(), key=lambda x: x['total_points'])

@main.route('/practice')
@login_required
def practice():
    book = request.args.get('book')
    all_words = get_practice_list(book)
    for w in all_words:
        w['related'] = hanzi_words.get(w['word'], [])
    # print(all_words)
    return render_template('words.html', book=book, totalPoints = session.get("total_points", 0),
                           todayPoints = session.get("today_points", 0),
                           words=json.dumps(all_words, indent=4, ensure_ascii=False))

@main.route('/words/<book>')
def words(book):
    return jsonify(get_practice_list(book))

@main.route('/save', methods=['POST'])
@login_required
def save_words():
    data = request.get_json()
    for w in data['words']:
        p = Progress(user_id=w['user_id'], word_id=w['word_id'],
                     word = w['word'], book = w['book'], chapter = w['chapter'],
                     study_date = datetime.utcnow(),
                     trial = w['trial'] + 1,
                     points = w['score'], total_points = w['total_points'] + w['score'])
        db.session.add(p)
        db.session.commit()
        
    return jsonify(data)

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
    return current_app.send_static_file("print.html")

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
