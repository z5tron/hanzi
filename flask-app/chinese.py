# -*- coding: utf-8 -*-

import sys
import codecs
import random
import sqlite3
from os import path, getcwd, chdir
from datetime import datetime, timedelta
import subprocess
import argparse
import uuid

from flask import Flask, current_app
from flask import render_template, send_file
from flask import Response, abort, request, jsonify, g, send_from_directory

from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    # "postgresql://alex:abc123@localhost/hanzi"
    # "mysql+pymysql://alex:abc123@localhost/hanzi?charset=utf8"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bootstrap = Bootstrap(app)

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), nullable=False)
    points = db.Column(db.Integer, default=0)
    first_study = db.Column(db.DateTime, default=datetime.utcnow)
    last_study = db.Column(db.DateTime, default=datetime.utcnow)
    
class Word(db.Model):
    __tablename__ = "word"
    __table_args__ = (
        db.UniqueConstraint('word', 'book', name="unique_word_book"),
    )
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    word = db.Column(db.Unicode(16), nullable=False)
    book = db.Column(db.Unicode(64), nullable=False)
    chapter = db.Column(db.Unicode(16), default="")
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
class Progress(db.Model):
    __tablename__ = "progress"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    word_id = db.Column(db.Integer, db.ForeignKey("word.id"))
    word = db.Column(db.Unicode(16), nullable=False)
    study_date = db.Column(db.DateTime, nullable=False)
    trial = db.Column(db.Integer, default = 0)
    points = db.Column(db.Integer, default = 0)
    total_points = db.Column(db.Integer, default=0)
    
OUTPUT="/tmp"


@app.route('/')
def index():
    return render_template("words.html")


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
