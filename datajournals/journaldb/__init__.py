from flask import Blueprint

bp = Blueprint('journaldb', __name__)

from datajournals.journaldb import routes
