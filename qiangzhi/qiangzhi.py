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
    import json
    from datetime import datetime
    word_hist = {}
    for line in open(fname, 'r'):
        if line.find("#") >= 0: continue
        j = json.loads(line)
        study_date = datetime.strptime(j['study_date'], "%Y-%m-%d %H:%M:%S.%f%z")
        p = Progress(user_id=j['user_id'],
                     word_id=int(j['word_id']), word=j['word'],
                     book=j['book'], chapter=j['chapter'],study_date=study_date, trial=int(j['trial']),
                     points=int(j['points']), total_points=int(j['total_points']))
        k = "{}_{}".format(j['book'], j['word'])
        word_hist.setdefault(k, [])
        word_hist[k].append(p)
    for k,v in word_hist.items():
        word_hist[k] = sorted(v, key = lambda x: x.trial, reverse=True)
        if len(word_hist[k]) > 2:
            word_hist[k] = word_hist[k][:3]
    for k,v in word_hist.items():
        for p in v:
            db.session.add(p)
    db.session.commit()

@app.cli.command("export-db")
@click.argument('fname')
def export_db(fname):
    # db.drop_all()
    # db.create_all()
    import pytz
    from datetime import datetime
    word_in_book = {}
    f = open(fname, 'w')
    for p in Progress.query.order_by(Progress.study_date.desc()).all():
        f.write("{}\n".format(p.json()))
    f.close()


@app.cli.command("check-db")
@click.argument('fname')
def check_db(fname):
    # db.drop_all()
    # db.create_all()
    import pytz
    import json
    from datetime import datetime
    for line in open(fname, 'r'):
        if line.find("#") >= 0: continue
        j = json.loads(line)
        study_date = datetime.strptime(j['study_date'], "%Y-%m-%d %H:%M:%S.%f%z")
        p = Progress(user_id=j['user_id'],
                     word_id=int(j['word_id']), word=j['word'],
                     book=j['book'], chapter=j['chapter'],study_date=study_date, trial=int(j['trial']),
                     points=int(j['points']), total_points=int(j['total_points']))
        # db.session.add(p)
    # db.session.commit()

# main
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
    
