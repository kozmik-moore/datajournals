from flask import render_template
from datajournals.dashboard import bp


@bp.route('/dash/')
@bp.route('/dashboard/')
@bp.route('/')
def index():
    return render_template('dashboard/index.html')
