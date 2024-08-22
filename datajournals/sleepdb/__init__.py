from flask import Blueprint

bp = Blueprint('sleepdb', __name__)

from datajournals.sleepdb import routes
