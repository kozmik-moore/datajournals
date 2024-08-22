from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flaskext.markdown import Markdown
from flask_login import LoginManager

db = SQLAlchemy()

migrate = Migrate(render_as_batch=True)

login_manager = LoginManager()
login_manager.login_view = 'authorization.login'
