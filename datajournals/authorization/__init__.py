from functools import wraps

from flask import Blueprint, redirect, url_for, request
from flask_login import current_user

from datajournals.models.authorization import User
from .init_db import init_authorization_tables

bp = Blueprint('authorization', __name__)

from datajournals.authorization import routes


def requires_access(access: list[str]):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user:
                return redirect(url_for('authorization.login'))

            user = User.query.filter_by(username=current_user.username).first()
            if user.role.rolename not in access:
                return redirect(url_for('authorization.no_access', request_endpoint=request.endpoint))

            return f(*args, **kwargs)
        return decorated_function
    return decorator
