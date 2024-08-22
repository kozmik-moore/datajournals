from flask import render_template, redirect, url_for, flash, current_app, request
from flask_login import logout_user, login_user, current_user

from datajournals.authorization import bp
from datajournals.authorization.forms import LoginForm
from datajournals.models.authorization import User


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember.data)
            next_ = form.next_.data
            if next_ is None or not next_.startswith('/'):
                next_ = url_for('dashboard.index')
            current_app.logger.info(f'User successfully logged in: {form.username.data}')
            return redirect(next_)
        else:
            flash('Invalid Username or password!', 'warning')
            if user is None:
                message = f'Attempted login with invalid username. ' \
                          f'Username: {form.username.data}. ' \
                          f'IP address: {request.remote_addr}.'
                current_app.logger.warning(message)
            else:
                message = f'Attempted login with invalid password. ' \
                          f'Username: {form.username.data}. ' \
                          f'IP address: {request.remote_addr}.'
                current_app.logger.warning(message)
    return render_template('/authorization/login.html', form=form)


@bp.route('/logout')
def logout():
    username = current_user.username
    logout_user()
    current_app.logger.info(f'User successfully logged out: {username}')
    return render_template('/authorization/logout.html')


@bp.route('/no_access/')
def no_access(request_endpoint=None):
    content = request_endpoint if request_endpoint else request.args.get('request_endpoint')
    message = f'You lack access to {request.url_root + url_for(content).lstrip("/") if content else "that feature"}'
    flash(message, 'warning')
    warning = f'User {current_user.username} attempted to access {content if content else "unauthorized content"}'
    current_app.logger.warning(warning)
    return render_template('/authorization/no_access.html')
