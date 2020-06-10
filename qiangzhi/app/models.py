from datetime import datetime
import hashlib
import pytz
import json
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import UserMixin

from . import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.Unicode(64), nullable=False)
    password_hash = db.Column(db.String(128))
    tot_xpoints = db.Column(db.Integer, default=0)
    first_study = db.Column(db.DateTime, default=datetime.utcnow)
    last_study = db.Column(db.DateTime, default=datetime.utcnow)
    streak = db.Column(db.Integer, default=1)
    days = db.Column(db.Integer, default=0)
    cur_xpoints = db.Column(db.Integer, default=0)
    session_date = db.Column(db.Integer, default=19700101)
    timezone_offset = db.Column(db.Integer, default=0)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
    
    def gravatar(self, size=100):
        hash = self.gravatar_hash()
        return '{url}/{hash}?s={size}'.format(url='https://secure.gravatar.com/avatar', hash=hash, size=size)

    def ping(self):
        t = datetime.utcnow()
        if self.last_study.year != t.year or \
           self.last_study.month != t.month or \
           self.last_study.day != t.day:
           s = Score(user_id = self.id, study_y4md=t.year*10000+t.month*100+t.day)
           db.session.add(s)
        self.last_study = datetime.utcnow()
        db.session.add(self)
        db.session.commit()


class Word(db.Model):
    __tablename__ = "word"
    __table_args__ = (
        db.UniqueConstraint('user_id', 'word', 'book', 'chapter', name="unique_word_book"),
    )
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    word = db.Column(db.Unicode(16), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    book = db.Column(db.Unicode(64), nullable=False)
    chapter = db.Column(db.Unicode(16), default="")
    study_date = db.Column(db.DateTime, default=datetime(1970, 1, 1))
    cur_xpoints = db.Column(db.Integer, default = 0)
    tot_xpoints = db.Column(db.Integer, default = 0)
    num_pass = db.Column(db.Integer, default=0)
    num_fail = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    istep = db.Column(db.Integer, default=0)

class Progress(db.Model):
    __tablename__ = "progress"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    word_id = db.Column(db.Integer, default=0, index=True)
    word = db.Column(db.Unicode(16), nullable=False, index=True)
    book = db.Column(db.Unicode(64), nullable=False)
    chapter = db.Column(db.Unicode(16), default="")
    study_date = db.Column(db.DateTime, nullable=False)
    xpoints = db.Column(db.Integer, default = 0)
    
    def json(self):
        import pytz
        return json.dumps({
            'id': self.id,
            'user_id': self.user_id,
            'word_id': self.word_id,
            'word': self.word,
            'book': self.book,
            'chapter': self.chapter,
            'study_date': pytz.utc.localize(self.study_date).strftime("%Y-%m-%d %H:%M:%S.%f%z"),
            'xpoints': self.xpoints,
        }, sort_keys=True)
    
                          
class Score(db.Model):
    __tablename__ = "score"
    __table_args__ = (
        db.UniqueConstraint('user_id', 'study_y4md', name="unique_word_book"),
    )
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    study_y4md = db.Column(db.Integer, nullable=False)
    xpoints = db.Column(db.Integer, default = 0)
    num_pass = db.Column(db.Integer, default=0)
    num_fail = db.Column(db.Integer, default=0)
    num_thumb_up = db.Column(db.Integer, default=0)
    num_thumb_down = db.Column(db.Integer, default=0)
    study_date = db.Column(db.DateTime, default=datetime.utcnow())

    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
