from flask import Blueprint

bp = Blueprint('dashboard', __name__)

from datajournals.dashboard import routes
