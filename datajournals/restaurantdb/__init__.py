from flask import Blueprint

bp = Blueprint('restaurantdb', __name__)

from datajournals.restaurantdb import routes
