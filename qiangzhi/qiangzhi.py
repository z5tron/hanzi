import os
import click

from flask_migrate import Migrate, upgrade
from app import create_app, db
from app.models import User, Word, Progress

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
        user = User(email=u+"@localhost.cc", username=u, name=u, password='cat')
        db.session.add(user)
    db.session.commit()

@app.cli.command("deploy")
def deploy():
    upgrade()
    
    
@app.cli.command("import-db")
@click.argument('fname')
def import_db(fname):
    # db.drop_all()
    # db.create_all()
    import pytz
    from datetime import datetime
    word_in_book = {}
    for line in open(fname, 'r'):
        if line.find("#") >= 0: continue
        rid,w,trial,wid,study_date,book,ch,pt,tot_pt = line.strip().split(',')
        study_date = datetime.strptime(study_date, "%Y-%m-%d %H:%M:%S.%f%z")
        p = Progress(user_id=1, word_id=int(wid), word=w,
                     book=book,chapter=ch,study_date=study_date, trial=int(trial),
                     points=int(pt), total_points=int(tot_pt))
        db.session.add(p)
    db.session.commit()
        
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
    
