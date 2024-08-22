from flask import Blueprint

bp = Blueprint('dreamdb', __name__)

from datajournals.dreamdb import routes
