from flask import render_template, redirect, request, url_for, flash, session
from flask_login import login_user, logout_user

from . import auth
from .. import db
from ..models import User
from .forms import LoginForm, RegistrationForm

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            session['username'] = user.username
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.user')
            return redirect(next)
        flash('Invalid username or password.')
    # print(form)
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    name = form.username.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You can not login.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

                    