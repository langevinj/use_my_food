from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.fields.html5 import DecimalRangeField
from wtforms.validators import DataRequired, Email, Length


class UserAddForm(FlaskForm):
    """Form for adding a user"""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])

class LoginForm(FlaskForm):
    """Form for logging in a user"""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])
