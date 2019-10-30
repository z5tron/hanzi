import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'abc123def456'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite3')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = "postgresql://alex:abc123@localhost/hanzi"

class MySQLConfig(Config):
    # mysqlclient (a maintained fork of MySQL-Python)
    SQLALCHEMY_DATABASE_URI = "mysql+mysqldb://alex:abc123@localhost/hanzi"
    
class HerokuConfig(ProductionConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '__NONE__')
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

class PythonAnywhereConfig(ProductionConfig):
    # mysqlclient (a maintained fork of MySQL-Python)
    SQLALCHEMY_DATABASE_URI = "mysql+mysqldb://z5tron:abc123def@z5tron.mysql.pythonanywhere-services.com/hanzi"
    
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
    'heroku': HerokuConfig,
    'mysql': MySQLConfig,
    'pythonanywhere': PythonAnywhereConfig,
    'SSL_REDIRECT': False,
}
