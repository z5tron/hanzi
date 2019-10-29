# -*- coding: utf-8 -*-

import os

from flask import Flask
from flask_moment import Moment
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from config import config, basedir

db = SQLAlchemy()
bootstrap = Bootstrap()
moment = Moment()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'

hanzi_words = {}
for line in open(os.path.join(basedir, "hanzi_words.txt")):
    hanzi_words[line[0]] = line[2:].split()
    
# application factory
def create_app(config_name):
    app = Flask(__name__, instance_relative_config=True)
    # app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://alex:abc123@localhost/hanzi"
    # "mysql+pymysql://alex:abc123@localhost/hanzi?charset=utf8"
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    bootstrap.init_app(app)
    db.init_app(app)
    moment.init_app(app)
    login_manager.init_app(app)

    #if app.config['SSL_REDIRECT']:
    #    from flask_sslify import SSLify
    #    sslify = SSLify(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # url_prefix makes '/login' in views to be '/auth/login'
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    return app
    
    
OUTPUT="/tmp"


