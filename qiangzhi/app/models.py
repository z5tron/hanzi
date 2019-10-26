from datetime import datetime
import hashlib
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
    points = db.Column(db.Integer, default=0)
    first_study = db.Column(db.DateTime, default=datetime.utcnow)
    last_study = db.Column(db.DateTime, default=datetime.utcnow)

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
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

        
class Word(db.Model):
    __tablename__ = "word"
    #__table_args__ = (
    #    db.UniqueConstraint('word', 'book', name="unique_word_book"),
    #)
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    word = db.Column(db.Unicode(16), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
class Progress(db.Model):
    __tablename__ = "progress"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    word_id = db.Column(db.Integer, default=0, index=True)
    word = db.Column(db.Unicode(16), nullable=False, index=True)
    book = db.Column(db.Unicode(64), nullable=False)
    chapter = db.Column(db.Unicode(16), default="")
    study_date = db.Column(db.DateTime, nullable=False)
    trial = db.Column(db.Integer, default = 0)
    points = db.Column(db.Integer, default = 0)
    total_points = db.Column(db.Integer, default=0)

class Score(db.Model):
    __tablename__ = "score"
    __table_args__ = (
        db.UniqueConstraint('user_id', 'study_date', name="unique_word_book"),
    )
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    study_date = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, default = 0)
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
