from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, HiddenField
from wtforms.validators import InputRequired, Length


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(1, 64)])
    password = PasswordField('Password', validators=[InputRequired(), Length(8, 72)])
    remember = BooleanField('Remember me')
    next_ = HiddenField('Next',)
    submit = SubmitField('Log In')
