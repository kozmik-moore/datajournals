import json
from logging.config import dictConfig
from os.path import dirname, abspath

from flask import Flask, current_app

from datajournals.extensions import db, migrate, Markdown, login_manager
from datajournals.logs import log_dict
from datajournals.app_config import config, JSON_PATH

APP_ROOT = dirname(abspath(__file__))
dictConfig(log_dict)


def create_app(cfg='default'):
    app_ = Flask(__name__, instance_relative_config=True)
    app_.logger.setLevel('INFO')  # TODO figure out why this was needed, instead of dictConfig
    app_.logger.info('Initializing data journals app.')
    try:
        cfg_class = config[cfg]
    except IndexError:
        cfg = 'default'
        cfg_class = config[cfg]
    app_.config.from_object(cfg_class)
    app_.config.from_pyfile('config.py', silent=True)

    # Initialize Flask extensions here
    db.init_app(app=app_)
    migrate.init_app(app=app_, db=db)
    Markdown(app_, extensions=['nl2br', 'sane_lists', 'smarty', 'tables'])
    login_manager.init_app(app_)
    app_.jinja_env.add_extension('jinja2.ext.do')

    with app_.app_context():
        from datajournals import models
        db.create_all()
        from datajournals.models.authorization import User
        from datajournals.dashboard import routes
        from datajournals.authorization import routes
        from datajournals.restaurantdb import routes
        from datajournals.dreamdb import routes
        from datajournals.journaldb import routes
        from datajournals.sleepdb import routes
        from datajournals.gamingdb import routes

        # Register blueprints here

        # Dashboard: primary index page, stats and directories
        from datajournals.dashboard import bp as dashboard_bp
        app_.register_blueprint(dashboard_bp)

        # Authorization: login, user session management
        from datajournals.authorization import bp as auth_bp
        app_.register_blueprint(auth_bp, url_prefix='/auth/')

        # Restaurant DB: visits and ratings on visited restaurants
        from datajournals.restaurantdb import bp as restaurant_bp
        app_.register_blueprint(restaurant_bp, url_prefix='/restaurantdb/')

        # Dream DB: records of dreams
        from datajournals.dreamdb import bp as dream_bp
        app_.register_blueprint(dream_bp, url_prefix='/dreamdb/')

        # Journal DB: records of thoughts and events
        from datajournals.journaldb import bp as journal_bp
        app_.register_blueprint(journal_bp, url_prefix='/journaldb/')

        # Sleep DB: records of time sleeping
        from datajournals.sleepdb import bp as sleep_bp
        app_.register_blueprint(sleep_bp, url_prefix='/sleepdb/')

        # Sleep DB: records of health concerns
        from datajournals.healthdb import bp as health_bp
        app_.register_blueprint(health_bp, url_prefix='/healthdb/')

        # Game DB: records of gaming sessions
        from datajournals.gamingdb import bp as gaming_bp
        app_.register_blueprint(gaming_bp, url_prefix='/gamingdb/')

        # Init default database values
        app_.logger.info('Checking default database configuration.')
        from datajournals.app_config import run_init_config
        run_init_config()
        app_.config.from_file(JSON_PATH, load=json.load)
        app_.logger.info('Finished checking database configuration.')

        # Init command line interfaces
        from datajournals.authorization.cli import user_cli
        app_.cli.add_command(user_cli)

        app_.logger.info('Data journals app successfully started.')
        return app_


def get_app(cfg='default'):
    """
    If the app is running, returns the current app. Otherwise, returns a newly created app.
    :return: an app instance
    """
    if not current_app:
        return create_app(cfg)
    else:
        return current_app


if __name__ == "__main__":
    main_app = create_app()
    main_app.run()
