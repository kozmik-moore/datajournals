from flask import Blueprint

bp = Blueprint('healthdb', __name__)

from datajournals.healthdb import routes
