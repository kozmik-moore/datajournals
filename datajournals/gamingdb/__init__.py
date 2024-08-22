from flask import Blueprint

bp = Blueprint('gamingdb', __name__)

from datajournals.gamingdb import routes
