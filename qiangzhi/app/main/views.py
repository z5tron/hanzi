import json
from datetime import datetime, timedelta
from os import path, getcwd, chdir
import subprocess, uuid

from flask import jsonify, render_template, render_template_string, session, redirect, url_for, request, send_file
from . import main
from .. import db, hanzi_words
from flask_login import login_required, current_user
from ..models import User, Progress, Word, Score

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
    books = []
    for w in db.session.query(Word.book).distinct():
        books.append(w.book)
    return render_template('user.html', user=user, books=sorted(books))

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
    words = []
    for w in Word.query.filter_by(book=book).order_by(Word.chapter, Word.tot_xpoints).all():
        # if datetime.utcnow().strftime("%Y%m%d") == w.study_date.strftime("%Y%m%d"):
        #    score = w.xpoints
        words.append({ 'id': w.id, 'word': w.word,
                       'book': w.book, 'chapter': w.chapter,
                       'study_date': w.study_date.strftime("%Y-%m-%dT%H:%M:%S%z"),
                       'cur_xpoints': w.cur_xpoints, 'tot_xpoints': w.tot_xpoints,
                       'num_pass': w.num_pass, 'num_fail': w.num_fail,
                       'related': hanzi_words.get(w.word, []) })
    # words = json.dumps(words)
    return render_template('words.html', book=book, tot_xpoints = current_user.tot_xpoints,
                           cur_xpoints = current_user.cur_xpoints, words=words)

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
    for w in data['words']:
        p = Progress(user_id=uid, word_id=w['id'],
                     word = w['word'], book = w['book'], chapter = w['chapter'],
                     study_date = datetime.utcnow(),
                     xpoints = w['xpoints'])
        db.session.add(p)
        for wbi in Word.query.filter_by(word=w['word']):
            t = datetime.utcnow()
            if t.strftime("%Y%m%d") == wbi.study_date.strftime("%Y%m%d"):
                wbi.cur_xpoints += w['xpoints']
            else:
                wbi.cur_xpoints = w['xpoints']
            wbi.study_date = t
            wbi.tot_xpoints += w['xpoints']
            if w['xpoints'] > 0: wbi.num_pass += 1
            elif w['xpoints'] < 0: wbi.num_fail += 1
            db.session.add(wbi)
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
